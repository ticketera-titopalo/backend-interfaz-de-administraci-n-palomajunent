from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.purchase import Purchase
from ..models.concert import Concert
from ..models.user import User
from pydantic import BaseModel as PydanticBaseModel

# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["purchases"])

# Esquemas Pydantic
class PurchaseCreate(PydanticBaseModel):
    concert_id: int
    quantity: int = 1
    user_id: int

class PurchaseOut(PydanticBaseModel):
    id: int
    concert_id: int
    user_id: int
    quantity: int
    total_price: float
    status: str
    purchased_at: str
    redeemed: int
    
    class Config:
        from_attributes = True

@router.post("/purchases", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
def create_purchase(purchase_data: PurchaseCreate, db: Session = Depends(get_db)):
    """Crear una nueva compra de entradas."""
    # Validar que el concierto existe
    concert = db.query(Concert).filter(Concert.id == purchase_data.concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=404, 
            detail="Concierto no encontrado"
        )
    
    # Validar que el usuario existe y está activo
    user = db.query(User).filter(User.id == purchase_data.user_id).first()
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

@router.get("/purchases", response_model=list[PurchaseOut])
def list_purchases(db: Session = Depends(get_db)):
    """Listar todas las compras."""
    purchases = db.query(Purchase).all()
    return [purchase.to_dict() for purchase in purchases]

@router.get("/purchases/user/{user_id}", response_model=list[PurchaseOut])
def list_purchases_by_user(user_id: int, db: Session = Depends(get_db)):
    """Listar compras de un usuario específico."""
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    return [purchase.to_dict() for purchase in purchases]
