"""Rutas, esquemas y lógica de negocio para compras y emisión de tickets."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import (
    check_rate_limit,
    get_active_user_by_id,
    get_entity_or_404,
)
from ..models.concert import Concert
from ..models.purchase import Purchase
from ..models.ticket import Ticket
from ..models.user import User

RATE_LIMIT_PURCHASES = 10
RATE_LIMIT_WINDOW_SECONDS = 3600

router = APIRouter(prefix="/api", tags=["purchases"])


class TicketSimpleOut(PydanticBaseModel):
    """Esquema resumido de un ticket dentro del detalle de compra."""

    id: str
    concert_id: int
    concert_title: str
    concert_artist: str
    price: float
    redeemed: int

    class Config:
        from_attributes = True


class TicketOut(PydanticBaseModel):
    """Esquema completo de salida para un ticket emitido."""

    id: int
    concert_id: int
    user_id: int
    price_paid: float
    purchased_at: str | None = None
    redeemed: int
    qr_code: str

    class Config:
        from_attributes = True


class EmitirTicket(PydanticBaseModel):
    """Esquema de entrada para emitir tickets de una compra."""

    purchase_id: int = Field(..., gt=0, description="ID de la compra a emitir")


class PurchaseCreate(PydanticBaseModel):
    """Esquema de entrada para registrar una compra."""

    concert_id: int = Field(..., gt=0, description="ID del concierto")
    quantity: int = Field(..., ge=1, le=10000, description="Cantidad de tickets")
    user_id: int = Field(..., gt=0, description="ID del usuario")


class PurchaseOut(PydanticBaseModel):
    """Esquema de respuesta básica de una compra."""

    id: int
    user_id: int
    concert_id: int
    quantity: int
    total_price: float
    status: str
    purchased_at: str | None = None
    redeemed: int

    class Config:
        from_attributes = True


class PurchaseDetailOut(PurchaseOut):
    """Esquema de respuesta detallada de una compra con sus tickets."""

    tickets: list[TicketSimpleOut] = []


def _build_ticket_out(ticket: Ticket) -> TicketOut:
    """Serializa una instancia de Ticket al esquema TicketOut."""
    return TicketOut(
        id=ticket.id,
        concert_id=ticket.concert_id,
        user_id=ticket.user_id,
        price_paid=ticket.price_paid,
        purchased_at=str(ticket.purchased_at) if ticket.purchased_at else None,
        redeemed=ticket.redeemed,
        qr_code=ticket.qr_code,
    )


def _build_purchase_detail_out(purchase: Purchase) -> PurchaseDetailOut:
    """Serializa una instancia de Purchase al esquema detallado PurchaseDetailOut."""
    return PurchaseDetailOut(
        id=purchase.id,
        user_id=purchase.user_id,
        concert_id=purchase.concert_id,
        quantity=purchase.quantity,
        total_price=purchase.total_price,
        status=purchase.status,
        purchased_at=str(purchase.purchased_at) if purchase.purchased_at else None,
        redeemed=purchase.redeemed,
        tickets=purchase.get_tickets(),
    )


def _validate_purchase_entities(
    db: Session, purchase_payload: PurchaseCreate
) -> Concert:
    """Valida existencia de concierto, usuario activo y disponibilidad de stock."""
    concert = get_entity_or_404(
        db, Concert, purchase_payload.concert_id, "Concierto no encontrado"
    )
    get_active_user_by_id(db, purchase_payload.user_id)

    available_stock = concert.tickets_disponibles()
    if purchase_payload.quantity > available_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Stock insuficiente. Disponible: {available_stock}, "
                f"Solicitado: {purchase_payload.quantity}"
            ),
        )
    return concert


def _validate_and_get_emission_context(
    db: Session, purchase_id: int
) -> tuple[Purchase, Concert]:
    """Valida la compra, rate-limit, emisión previa y entidades relacionadas."""
    purchase = get_entity_or_404(db, Purchase, purchase_id, "Compra no encontrada")

    check_rate_limit(
        f"emit_{purchase.user_id}",
        RATE_LIMIT_PURCHASES,
        RATE_LIMIT_WINDOW_SECONDS,
        "Máximo número de emisiones por hora alcanzado",
    )

    if db.query(Ticket).filter(Ticket.concert_id == purchase.concert_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tickets ya emitidos para esta compra",
        )

    concert = get_entity_or_404(
        db, Concert, purchase.concert_id, "Concierto no encontrado"
    )
    get_entity_or_404(db, User, purchase.user_id, "Usuario no encontrado")
    return purchase, concert


def _generate_unique_tickets(
    db: Session, purchase: Purchase, concert: Concert
) -> list[TicketOut]:
    """Genera en lote los tickets con códigos QR únicos evitando consultas N+1."""
    candidate_codes: set[str] = set()
    while len(candidate_codes) < purchase.quantity:
        candidate_codes.add(Ticket.generar_qr_code())

    existing_codes = {
        row[0]
        for row in db.query(Ticket.qr_code)
        .filter(Ticket.qr_code.in_(candidate_codes))
        .all()
    }
    candidate_codes -= existing_codes

    while len(candidate_codes) < purchase.quantity:
        new_code = Ticket.generar_qr_code()
        if not db.query(Ticket.id).filter(Ticket.qr_code == new_code).first():
            candidate_codes.add(new_code)

    created_tickets: list[Ticket] = []
    for qr_code in candidate_codes:
        ticket = Ticket(
            concert_id=purchase.concert_id,
            user_id=purchase.user_id,
            price_paid=concert.price,
            qr_code=qr_code,
        )
        db.add(ticket)
        created_tickets.append(ticket)

    db.commit()
    for ticket in created_tickets:
        db.refresh(ticket)

    return [_build_ticket_out(ticket) for ticket in created_tickets]


@router.post(
    "/purchases", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED
)
def create_purchase(
    purchase_payload: PurchaseCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    """Crea una nueva compra de entradas validando stock y descontando disponibilidad."""
    check_rate_limit(
        f"purchase_{purchase_payload.user_id}",
        RATE_LIMIT_PURCHASES,
        RATE_LIMIT_WINDOW_SECONDS,
        "Máximo número de compras por hora alcanzado",
    )

    concert = _validate_purchase_entities(db, purchase_payload)
    new_purchase = Purchase(
        user_id=purchase_payload.user_id,
        concert_id=purchase_payload.concert_id,
        quantity=purchase_payload.quantity,
        total_price=round(concert.price * purchase_payload.quantity, 2),
        status="completed",
    )
    concert.reducir_stock(purchase_payload.quantity)

    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase.to_dict()


@router.post(
    "/purchases/emitir",
    response_model=list[TicketOut],
    status_code=status.HTTP_201_CREATED,
)
def emitir_tickets(
    emit_payload: EmitirTicket,
    db: Session = Depends(get_db),
    request: Request = None,
) -> list[TicketOut]:
    """Genera y emite los tickets individuales correspondientes a una compra."""
    purchase, concert = _validate_and_get_emission_context(db, emit_payload.purchase_id)
    return _generate_unique_tickets(db, purchase, concert)


@router.get("/tickets/usuario/{user_id}", response_model=list[TicketOut])
def list_tickets_by_user(
    user_id: int, db: Session = Depends(get_db)
) -> list[TicketOut]:
    """Obtiene todos los tickets asociados a un usuario."""
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    return [_build_ticket_out(ticket) for ticket in tickets]


@router.get("/purchases/user/{user_id}", response_model=list[PurchaseDetailOut])
def list_purchases_by_user(
    user_id: int, db: Session = Depends(get_db)
) -> list[PurchaseDetailOut]:
    """Retorna el historial de compras de un usuario."""
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    return [_build_purchase_detail_out(purchase) for purchase in purchases]


@router.get("/purchases/{purchase_id}", response_model=PurchaseDetailOut)
def get_purchase_detail(
    purchase_id: int, db: Session = Depends(get_db)
) -> PurchaseDetailOut:
    """Obtiene el detalle completo de una compra y sus tickets asociados."""
    purchase = get_entity_or_404(db, Purchase, purchase_id, "Compra no encontrada")
    return _build_purchase_detail_out(purchase)
