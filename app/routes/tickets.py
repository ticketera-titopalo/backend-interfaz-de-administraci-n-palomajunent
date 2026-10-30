from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.ticket import Ticket
from pydantic import BaseModel as PydanticBaseModel

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# Esquemas Pydantic
class TicketCreate(PydanticBaseModel):
    concert_id: int
    user_id: int
    price_paid: float

class TicketOut(PydanticBaseModel):
    id: int
    concert_id: int
    user_id: int
    price_paid: float
    purchased_at: str
    redeemed: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    """Listar todos los tickets."""
    tickets = db.query(Ticket).all()
    return [ticket.to_dict() for ticket in tickets]

@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """Crear un nuevo ticket."""
    db_ticket = Ticket(
        concert_id=ticket.concert_id,
        user_id=ticket.user_id,
        price_paid=ticket.price_paid
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket.to_dict()

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Obtener un ticket por ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket.to_dict()
