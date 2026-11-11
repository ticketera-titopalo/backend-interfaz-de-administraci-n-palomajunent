from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.purchase import Purchase
from ..models.concert import Concert
from ..models.user import User
from pydantic import BaseModel as PydanticBaseModel, Field, validator
import time

# Constantes de rate limiting
RATE_LIMIT_PURCHASES = 10  # 10 requests por hora por usuario

router = APIRouter(prefix="/api", tags=["purchases"])

# Almacenamiento para rate limiting de purchases
purchase_rate_limit_storage = {}

def check_purchase_rate_limit(user_id: int, limit: int, period: int) -> bool:
    """Verificar límite de tasa para compras por usuario."""
    now = time.time()
    key = f"purchase_{user_id}"
    
    if key not in purchase_rate_limit_storage:
        purchase_rate_limit_storage[key] = []
    
    # Limpiar entradas viejas
    purchase_rate_limit_storage[key] = [t for t in purchase_rate_limit_storage[key] if now - t < period]
    
    if len(purchase_rate_limit_storage[key]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Máximo {limit} operaciones de compra por hora. Intente más tarde."
        )
    
    purchase_rate_limit_storage[key].append(now)
    return True

# Esquemas Pydantic con validaciones
class TicketSimpleOut(PydanticBaseModel):
    id: str
    concert_id: int
    concert_title: str
    concert_artist: str
    price: float
    redeemed: int
    
    class Config:
        from_attributes = True

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
    purchase_id: int = Field(..., gt=0, description="ID de la compra a emitir")

class PurchaseCreate(PydanticBaseModel):
    concert_id: int = Field(..., gt=0, description="ID del concierto")
    quantity: int = Field(..., ge=1, le=10000, description="Cantidad de tickets")
    user_id: int = Field(..., gt=0, description="ID del usuario")

class PurchaseOut(PydanticBaseModel):
    id: int
    user_id: int
    concert_id: int
    quantity: int
    total_price: float
    status: str
    purchased_at: str
    redeemed: int
    
    class Config:
        from_attributes = True

class PurchaseDetailOut(PydanticBaseModel):
    id: int
    user_id: int
    concert_id: int
    quantity: int
    total_price: float
    status: str
    purchased_at: str
    redeemed: int
    tickets: list[TicketSimpleOut] = []
    
    class Config:
        from_attributes = True

@router.post("/purchases", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
def create_purchase(purchase_data: PurchaseCreate, db: Session = Depends(get_db), request: Request = None):
    """Crear una nueva compra de entradas."""
    from ..models.concert import Concert as ConcertModel
    from ..models.user import User as UserModel
    
    # Rate limiting - 10 compras por hora por usuario
    user_id = purchase_data.user_id
    if not check_purchase_rate_limit(user_id, RATE_LIMIT_PURCHASES, 3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Máximo número de compras por hora alcanzado"
        )
    
    # Validar que el concierto existe
    concert = db.query(ConcertModel).filter(ConcertModel.id == purchase_data.concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=404, 
            detail="Concierto no encontrado"
        )
    
    # Validar que el usuario existe y está activo
    user = db.query(UserModel).filter(UserModel.id == purchase_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Usuario no encontrado"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=400, 
            detail="Usuario inactivo"
        )
    
    # Validar stock disponible
    stock_actual = concert.tickets_disponibles()
    if purchase_data.quantity > stock_actual:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {purchase_data.quantity}"
        )
    
    # Calcular precio total
    total_price = round(concert.price * purchase_data.quantity, 2)
    
    # Crear la compra
    db_purchase = Purchase(
        user_id=purchase_data.user_id,
        concert_id=purchase_data.concert_id,
        quantity=purchase_data.quantity,
        total_price=total_price,
        status="completed"
    )
    
    # Reducir stock del concierto
    concert.reducir_stock(purchase_data.quantity)
    
    # Guardar en BD
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    
    return db_purchase.to_dict()

@router.post("/purchases/emitir", response_model=list[TicketOut], status_code=status.HTTP_201_CREATED)
def emitir_tickets(emitir: EmitirTicket, db: Session = Depends(get_db), request: Request = None):
    """Emitir tickets tras una compra exitosa."""
    from jose import JWTError
    
    # Rate limiting - 10 emisiones por hora por usuario
    # Obtener user_id desde el token (usaremos el purchase_id para identificar usuario)
    purchase = db.query(Purchase).filter(Purchase.id == emitir.purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
        )
    
    user_id = purchase.user_id
    now = time.time()
    key = f"emit_{user_id}"
    
    if key not in purchase_rate_limit_storage:
        purchase_rate_limit_storage[key] = []
    
    purchase_rate_limit_storage[key] = [t for t in purchase_rate_limit_storage[key] if now - t < 3600]
    
    if len(purchase_rate_limit_storage[key]) >= RATE_LIMIT_PURCHASES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Máximo número de emisiones por hora alcanzado"
        )
    
    purchase_rate_limit_storage[key].append(now)
    
    # Validar que la compra existe
    purchase = db.query(Purchase).filter(Purchase.id == emitir.purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
        )
    
    # Validar que los tickets aún no hayan sido emitidos
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

@router.get("/purchases/user/{user_id}", response_model=list[PurchaseDetailOut])
def list_purchases_by_user(user_id: int, db: Session = Depends(get_db)):
    """Historial de compras de un usuario específico."""
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    result = []
    for purchase in purchases:
        tickets = purchase.get_tickets()
        result.append(PurchaseDetailOut(
            id=purchase.id,
            user_id=purchase.user_id,
            concert_id=purchase.concert_id,
            quantity=purchase.quantity,
            total_price=purchase.total_price,
            status=purchase.status,
            purchased_at=str(purchase.purchased_at) if purchase.purchased_at else None,
            redeemed=purchase.redeemed,
            tickets=tickets
        ))
    return result

@router.get("/purchases/{purchase_id}", response_model=PurchaseDetailOut)
def get_purchase_detail(purchase_id: int, db: Session = Depends(get_db)):
    """Detalle de una compra específica."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
        )
    
    tickets = purchase.get_tickets()
    return PurchaseDetailOut(
        id=purchase.id,
        user_id=purchase.user_id,
        concert_id=purchase.concert_id,
        quantity=purchase.quantity,
        total_price=purchase.total_price,
        status=purchase.status,
        purchased_at=str(purchase.purchased_at) if purchase.purchased_at else None,
        redeemed=purchase.redeemed,
        tickets=tickets
    )
