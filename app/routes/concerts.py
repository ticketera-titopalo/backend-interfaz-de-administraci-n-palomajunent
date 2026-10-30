from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.concert import Concert
from pydantic import BaseModel as PydanticBaseModel

# Crear tablas al importar
# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/concerts", tags=["concerts"])

# Esquemas Pydantic
class ConcertCreate(PydanticBaseModel):
    title: str
    artist: str
    description: str = ""
    price: float
    stock: int = 0

class ConcertOut(ConcertCreate):
    id: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[ConcertOut])
def list_concerts(db: Session = Depends(get_db)):
    """Listar todos los conciertos."""
    concerts = db.query(Concert).all()
    return [concert.to_dict() for concert in concerts]

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

@router.get("/{concert_id}", response_model=ConcertOut)
def get_concert(concert_id: int, db: Session = Depends(get_db)):
    """Obtener un concierto por ID."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(status_code=404, detail="Concierto no encontrado")
    return concert.to_dict()

@router.put("/{concert_id}", response_model=ConcertOut)
def update_concert(concert_id: int, concert: ConcertCreate, db: Session = Depends(get_db)):
    """Actualizar un concierto."""
    db_concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not db_concert:
        raise HTTPException(status_code=404, detail="Concierto no encontrado")
    db_concert.title = concert.title
    db_concert.artist = concert.artist
    db_concert.description = concert.description
    db_concert.price = concert.price
    db_concert.stock = concert.stock
    db.commit()
    db.refresh(db_concert)
    return db_concert.to_dict()

@router.delete("/{concert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concert(concert_id: int, db: Session = Depends(get_db)):
    """Eliminar un concierto."""
    db_concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not db_concert:
        raise HTTPException(status_code=404, detail="Concierto no encontrado")
    db.delete(db_concert)
    db.commit()
    return None
