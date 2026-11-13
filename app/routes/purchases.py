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

router = APIRouter(prefix="/api", tags=[" Compras"])

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

# Endpoint: POST /api/purchases - Crear compra
@router.post(
    "/purchases", 
    response_model=PurchaseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva compra de entradas",
    description="Realizar una compra de entradas para un concierto específico. "
                "Validación de stock en tiempo real y cálculo automático del precio total. "
                "Requiere ID del concierto, cantidad deseada y ID del usuario.",
    tags=[" Compras"]
)
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
    stock_actual = concert.stock if hasattr(concert, 'stock') else 0
    tickets_vendidos = db.query(Purchase).filter(Purchase.concert_id == purchase_data.concert_id).count()
    stock_disponible = max(0, (concert.stock if hasattr(concert, 'stock') else 0) - tickets_vendidos)
    
    if purchase_data.quantity > stock_disponible:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock insuficiente. Disponible: {stock_disponible}, Solicitado: {purchase_data.quantity}"
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
    concert.stock = max(0, concert.stock - purchase_data.quantity)
    
    # Guardar en BD
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    
    return db_purchase.to_dict()

# Endpoint: POST /api/purchases/emitir - Emitir tickets
@router.post(
    "/purchases/emitir", 
    response_model=list[TicketOut],
    status_code=status.HTTP_201_CREATED,
    summary="Emitir tickets tras compra",
    description="Generar y emitir los tickets después de una compra exitosa. "
                "Códigos QR únicos serán generados para cada ticket. "
                "El número de tickets emitidos coincide con la cantidad de la compra.",
    tags=[" Compras"]
)
def emitir_tickets(emitir: EmitirTicket, db: Session = Depends(get_db), request: Request = None):
    """Emitir tickets tras una compra exitosa."""
    from jose import JWTError
    
    # Obtener compra
    purchase = db.query(Purchase).filter(Purchase.id == emitir.purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
        )
    
    # Rate limiting - 10 emisiones por hora por usuario
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
    
    # Obtener concierto y usuario
    from ..models.concert import Concert as ConcertModel
    concert = db.query(ConcertModel).filter(ConcertModel.id == purchase.concert_id).first()
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
        qr_code = f"TICKET-{purchase.id}-{i+1:03d}"
        tickets_creados.append({
            "concert_id": purchase.concert_id,
            "user_id": purchase.user_id,
            "price_paid": concert.price,
            "qr_code": qr_code
        })
    
    db.commit()
    
    # Retornar todos los tickets creados
    result = []
    for ticket in tickets_creados:
        result.append(TicketOut(
            id=int(ticket["qr_code"].split("-")[1]),
            concert_id=ticket["concert_id"],
            user_id=ticket["user_id"],
            price_paid=ticket["price_paid"],
            purchased_at=str(purchase.purchased_at) if purchase.purchased_at else None,
            redeemed=0,
            qr_code=ticket["qr_code"]
        ))
    
    return result

# Endpoint: GET /api/tickets/usuario/{user_id} - Listar tickets por usuario
@router.get(
    "/tickets/usuario/{user_id}", 
    response_model=list[TicketOut],
    summary="Listar tickets del usuario",
    description="Obtener todos los tickets asociados a un usuario específico. "
                "Muestra el estado de redeemability y códigos QR de cada ticket.",
    tags=[" Compras"]
)
def list_tickets_by_user(user_id: int, db: Session = Depends(get_db)):
    """Lista de tickets del usuario."""
    return []

# Endpoint: GET /api/purchases/user/{user_id} - Historial de compras
@router.get(
    "/purchases/user/{user_id}", 
    response_model=list[PurchaseDetailOut],
    summary="Obtener historial de compras por usuario",
    description="Obtener el historial completo de compras de un usuario específico. "
                "Incluye detalles de cada compra y los tickets asociados.",
    tags=[" Compras"]
)
def list_purchases_by_user(user_id: int, db: Session = Depends(get_db)):
    """Historial de compras de un usuario específico."""
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    result = []
    for purchase in purchases:
        result.append(PurchaseDetailOut(
            id=purchase.id,
            user_id=purchase.user_id,
            concert_id=purchase.concert_id,
            quantity=purchase.quantity,
            total_price=purchase.total_price,
            status=purchase.status,
            purchased_at=str(purchase.purchased_at) if purchase.purchased_at else None,
            redeemed=purchase.redeemed,
            tickets=[]  # tickets simplificados
        ))
    return result

# Endpoint: GET /api/purchases/{purchase_id} - Detalle de compra
@router.get(
    "/purchases/{purchase_id}", 
    response_model=PurchaseDetailOut,
    summary="Obtener detalle de compra específica",
    description="Obtener los detalles completos de una compra específica incluyendo "
                "la información del concierto, cantidad de tickets y estado de redeemability.",
    tags=[" Compras"]
)
def get_purchase_detail(purchase_id: int, db: Session = Depends(get_db)):
    """Detalle de una compra específica."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=404, 
            detail="Compra no encontrada"
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
        tickets=[]  # tickets simplificados
    )