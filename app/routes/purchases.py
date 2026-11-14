"""Rutas, esquemas y lógica de negocio para compras y emisión de tickets."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.concert import Concert
from ..models.purchase import Purchase
from ..models.ticket import Ticket
from ..models.user import User

RATE_LIMIT_PURCHASES = 10
RATE_LIMIT_WINDOW_SECONDS = 3600

router = APIRouter(prefix="/api", tags=["purchases"])
purchase_rate_limit_storage: dict[str, list[float]] = {}


def check_operation_rate_limit(
    rate_key: str,
    limit: int = RATE_LIMIT_PURCHASES,
    period_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    error_detail: str | None = None,
) -> bool:
    """Verifica el límite de operaciones por ventana de tiempo para un usuario."""
    current_time = time.time()
    timestamps = purchase_rate_limit_storage.get(rate_key, [])
    valid_timestamps = [ts for ts in timestamps if current_time - ts < period_seconds]

    if len(valid_timestamps) >= limit:
        purchase_rate_limit_storage[rate_key] = valid_timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_detail
            or f"Máximo {limit} operaciones de compra por hora. Intente más tarde.",
        )

    valid_timestamps.append(current_time)
    purchase_rate_limit_storage[rate_key] = valid_timestamps
    return True


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


def _validate_purchase_entities(
    db: Session, purchase_payload: PurchaseCreate
) -> tuple[Concert, User]:
    """Valida existencia de concierto, usuario activo y disponibilidad de stock."""
    concert = (
        db.query(Concert).filter(Concert.id == purchase_payload.concert_id).first()
    )
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Concierto no encontrado"
        )

    user = db.query(User).filter(User.id == purchase_payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )

    available_stock = concert.tickets_disponibles()
    if purchase_payload.quantity > available_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Stock insuficiente. Disponible: {available_stock}, "
                f"Solicitado: {purchase_payload.quantity}"
            ),
        )

    return concert, user


def _validate_and_get_emission_context(
    db: Session, purchase_id: int
) -> tuple[Purchase, Concert, User]:
    """Valida la compra, rate-limit, emisión previa y entidades relacionadas."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compra no encontrada"
        )

    check_operation_rate_limit(
        f"emit_{purchase.user_id}",
        error_detail="Máximo número de emisiones por hora alcanzado",
    )

    existing_ticket = (
        db.query(Ticket).filter(Ticket.concert_id == purchase.concert_id).first()
    )
    if existing_ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tickets ya emitidos para esta compra",
        )

    concert = db.query(Concert).filter(Concert.id == purchase.concert_id).first()
    user = db.query(User).filter(User.id == purchase.user_id).first()
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Concierto no encontrado"
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    return purchase, concert, user


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

    return [
        TicketOut(
            id=ticket.id,
            concert_id=ticket.concert_id,
            user_id=ticket.user_id,
            price_paid=ticket.price_paid,
            purchased_at=str(ticket.purchased_at) if ticket.purchased_at else None,
            redeemed=ticket.redeemed,
            qr_code=ticket.qr_code,
        )
        for ticket in created_tickets
    ]


@router.post(
    "/purchases", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED
)
def create_purchase(
    purchase_payload: PurchaseCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    """Crea una nueva compra de entradas validando stock y descontando disponibilidad."""
    check_operation_rate_limit(
        f"purchase_{purchase_payload.user_id}",
        error_detail="Máximo número de compras por hora alcanzado",
    )

    concert, _ = _validate_purchase_entities(db, purchase_payload)
    total_price = round(concert.price * purchase_payload.quantity, 2)

    new_purchase = Purchase(
        user_id=purchase_payload.user_id,
        concert_id=purchase_payload.concert_id,
        quantity=purchase_payload.quantity,
        total_price=total_price,
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
    purchase, concert, _ = _validate_and_get_emission_context(
        db, emit_payload.purchase_id
    )
    return _generate_unique_tickets(db, purchase, concert)


@router.get("/tickets/usuario/{user_id}", response_model=list[TicketOut])
def list_tickets_by_user(
    user_id: int, db: Session = Depends(get_db)
) -> list[TicketOut]:
    """Obtiene todos los tickets asociados a un usuario."""
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    return [
        TicketOut(
            id=ticket.id,
            concert_id=ticket.concert_id,
            user_id=ticket.user_id,
            price_paid=ticket.price_paid,
            purchased_at=str(ticket.purchased_at) if ticket.purchased_at else None,
            redeemed=ticket.redeemed,
            qr_code=ticket.qr_code,
        )
        for ticket in tickets
    ]


@router.get("/purchases/user/{user_id}", response_model=list[PurchaseDetailOut])
def list_purchases_by_user(
    user_id: int, db: Session = Depends(get_db)
) -> list[PurchaseDetailOut]:
    """Retorna el historial de compras de un usuario."""
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    return [
        PurchaseDetailOut(
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
        for purchase in purchases
    ]


@router.get("/purchases/{purchase_id}", response_model=PurchaseDetailOut)
def get_purchase_detail(
    purchase_id: int, db: Session = Depends(get_db)
) -> PurchaseDetailOut:
    """Obtiene el detalle completo de una compra y sus tickets asociados."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compra no encontrada"
        )

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