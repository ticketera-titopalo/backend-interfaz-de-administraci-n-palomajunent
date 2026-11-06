from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.purchase import Purchase
from ..models.ticket import Ticket
from ..models.concert import Concert
from ..models.user import User
from pydantic import BaseModel as PydanticBaseModel
import hashlib
import time

# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["purchases"])

# Esquemas Pydantic
class TicketOut(PydanticBaseModel):
    id: int
    concert_id: int
    user_id: int
    price_paid: float
    purchased_at: str
    redeemed: int
    qr_code: str
    
    class Config:
        from_attributes = True

class EmitirTicket(PydanticBaseModel):
    purchase_id: int

class TicketSimple(PydanticBaseModel):
    id: int
    qr_code: str
    concert_title: str
    concert_artist: str
    price_paid: float
    redeemed: int
    
    class Config:
        from_attributes = True

@router.post("/purchases/emitir", response_model=list[TicketOut], status_code=status.HTTP_201_CREATED)
def emitir_tickets(emitir: EmitirTicket, db: Session = Depends(get_db)):
    """Emitir tickets tras una compra exitosa."""
    # Validar que la compra existe
    purchase = db.query(Purchase).filter(Purchase.id == emitir.purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
        )
    
    # Validar que los tickets aún no hayan sido emitidos
    # Revisamos si ya hay tickets creados para esta compra
    existing_tickets = db.query(Ticket).filter(Ticket.concert_id == purchase.concert_id).first()
    if existing_tickets:
        raise HTTPException(
            status_code=400, 
            detail="Tickets ya emitidos para esta compra"
        )
    
    # Obtener concierto y usuario
    concert = db.query(Concert).filter(Concert.id == purchase.concert_id).first()
    user = db.query(User).filter(User.id == purchase.user_id).first()
    
    if not concert:
        raise HTTPException(
            status_code=404, 
            detail="Concierto no encontrado"
        )
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Usuario no encontrado"
        )
    
    # Generar tickets
    tickets_creados = []
    for i in range(purchase.quantity):
        qr_code = Ticket.generar_qr_code()
        # Evitar duplicados simples
        while db.query(Ticket).filter(Ticket.qr_code == qr_code).first():
            qr_code = Ticket.generar_qr_code()
        
        ticket = Ticket(
            concert_id=purchase.concert_id,
            user_id=purchase.user_id,
            price_paid=concert.price,
            qr_code=qr_code
        )
        db.add(ticket)
        tickets_creados.append(ticket.to_dict())
    
    db.commit()
    
    # Retornar todos los tickets creados
    result = []
    for ticket in tickets_creados:
        result.append(TicketOut(
            id=ticket["id"],
            concert_id=ticket["concert_id"],
            user_id=ticket["user_id"],
            price_paid=ticket["price_paid"],
            purchased_at=ticket["purchased_at"],
            redeemed=ticket["redeemed"],
            qr_code=ticket["qr_code"]
        ))
    
    return result

@router.get("/tickets/usuario/{user_id}", response_model=list[TicketOut])
def list_tickets_by_user(user_id: int, db: Session = Depends(get_db)):
    """Lista de tickets del usuario."""
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    result = []
    for ticket in tickets:
        # Obtener info del concierto
        concert = db.query(Concert).filter(Concert.id == ticket.concert_id).first()
        result.append(TicketOut(
            id=ticket.id,
            concert_id=ticket.concert_id,
            user_id=ticket.user_id,
            price_paid=ticket.price_paid,
            purchased_at=str(ticket.purchased_at) if ticket.purchased_at else None,
            redeemed=ticket.redeemed,
            qr_code=ticket.qr_code
        ))
    return result
