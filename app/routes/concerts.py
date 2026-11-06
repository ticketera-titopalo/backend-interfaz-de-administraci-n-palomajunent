from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.concert import Concert
from pydantic import BaseModel as PydanticBaseModel

# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/concerts", tags=["concerts"])

# Esquemas Pydantic
class ConcertOut(PydanticBaseModel):
    id: int
    title: str
    artist: str
    description: str = ""
    price: float
    stock: int
    created_at: str
    
    class Config:
        from_attributes = True

class ConcertDetailOut(PydanticBaseModel):
    id: int
    title: str
    artist: str
    description: str = ""
    price: float
    stock: int
    tickets_vendidos: int
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[ConcertOut])
def list_concerts(db: Session = Depends(get_db)):
    """Listar todos los conciertos."""
    concerts = db.query(Concert).all()
    return [ConcertOut(
        id=c.id, title=c.title, artist=c.artist, 
        description=c.description, price=c.price, 
        stock=c.stock, created_at=str(c.created_at) if c.created_at else None
    ) for c in concerts]

@router.get("/{concert_id}", response_model=ConcertDetailOut)
def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Detalle de un concierto por ID."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=404, 
            detail="Concierto no encontrado"
        )
    # Calcular tickets vendidos total desde purchases
    tickets_vendidos = 0
    # Hacer la suma simple sin subconsultas complejas
    all_purchases = db.query(Purchase).filter(Purchase.concert_id == concert_id).all()
    for p in all_purchases:
        tickets_vendidos += p.quantity
    
    return ConcertDetailOut(
        id=concert.id,
        title=concert.title,
        artist=concert.artist,
        description=concert.description,
        price=concert.price,
        stock=concert.stock,
        tickets_vendidos=tickets_vendidos,
        created_at=str(concert.created_at) if concert.created_at else None
    )
