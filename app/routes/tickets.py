"""Rutas y esquemas para la gestión individual de tickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.ticket import Ticket

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class TicketCreate(PydanticBaseModel):
    """Esquema de entrada para crear un ticket."""

    concert_id: int
    user_id: int
    price_paid: float


class TicketOut(PydanticBaseModel):
    """Esquema de salida con los datos de un ticket."""

    id: int
    concert_id: int
    user_id: int
    price_paid: float
    purchased_at: str | None = None
    redeemed: int

    class Config:
        from_attributes = True


@router.get("/", response_model=list[TicketOut], summary="Listar todos los tickets")
def list_tickets(db: Session = Depends(get_db)) -> list[dict]:
    """Obtiene el listado completo de tickets emitidos."""
    tickets = db.query(Ticket).all()
    return [ticket.to_dict() for ticket in tickets]


@router.post(
    "/",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo ticket",
)
def create_ticket(ticket_payload: TicketCreate, db: Session = Depends(get_db)) -> dict:
    """Crea y persiste un nuevo ticket en la base de datos."""
    new_ticket = Ticket(
        concert_id=ticket_payload.concert_id,
        user_id=ticket_payload.user_id,
        price_paid=ticket_payload.price_paid,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket.to_dict()


@router.get("/{ticket_id}", response_model=TicketOut, summary="Obtener ticket por ID")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> dict:
    """Busca y retorna un ticket específico según su identificador."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado"
        )
    return ticket.to_dict()
