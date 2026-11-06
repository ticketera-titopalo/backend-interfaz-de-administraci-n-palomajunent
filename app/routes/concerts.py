from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.concert import Concert
from pydantic import BaseModel as PydanticBaseModel, Field, validator

# # Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/concerts", tags=["concerts"])

# Esquemas Pydantic con validaciones
class ConcertCreate(PydanticBaseModel):
    title: str = Field(..., max_length=255, description="Título del concierto")
    artist: str = Field(..., max_length=255, description="Artista o banda")
    description: str = Field(default="", max_length=500, description="Descripción del concierto")
    price: float = Field(..., gt=0, le=100000, description="Precio de la entrada")
    stock: int = Field(..., ge=0, le=10000, description="Stock disponible de entradas")
    
    @validator("title")
    def titulo_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El título no puede estar vacío")
        return v
    
    @validator("artist")
    def artista_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre del artista no puede estar vacío")
        return v

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

@router.post("/", response_model=ConcertOut, status_code=status.HTTP_201_CREATED)
def create_concert(concert: ConcertCreate, db: Session = Depends(get_db)):
    """Crear un nuevo concierto."""
    db_concert = Concert(
        title=concert.title,
        artist=concert.artist,
        description=concert.description,
        price=concert.price,
        stock=concert.stock
    )
    db.add(db_concert)
    db.commit()
    db.refresh(db_concert)
    return db_concert.to_dict()

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
