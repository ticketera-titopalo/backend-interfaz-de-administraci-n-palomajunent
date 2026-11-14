"""Rutas y esquemas para la gestión y consulta de conciertos."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.concert import Concert
from ..models.purchase import Purchase

router = APIRouter(
    prefix="/api/concerts",
    tags=["Conciertos"],
    responses={404: {"description": "Concierto no encontrado"}},
)


class ConcertCreate(PydanticBaseModel):
    """Esquema de validación para crear un nuevo concierto."""

    title: str = Field(..., max_length=255, description="Título del concierto")
    artist: str = Field(..., max_length=255, description="Artista o banda")
    description: str = Field(
        default="", max_length=500, description="Descripción del concierto"
    )
    price: float = Field(..., gt=0, le=100000, description="Precio de la entrada")
    stock: int = Field(..., ge=0, le=10000, description="Stock disponible de entradas")

    @validator("title")
    def validate_non_empty_title(cls, title_value: str) -> str:
        """Verifica que el título no contenga únicamente espacios en blanco."""
        if not title_value.strip():
            raise ValueError("El título no puede estar vacío")
        return title_value

    @validator("artist")
    def validate_non_empty_artist(cls, artist_value: str) -> str:
        """Verifica que el artista no contenga únicamente espacios en blanco."""
        if not artist_value.strip():
            raise ValueError("El nombre del artista no puede estar vacío")
        return artist_value


class ConcertOut(PydanticBaseModel):
    """Esquema de respuesta básica de un concierto."""

    id: int
    title: str
    artist: str
    description: str = ""
    price: float
    stock: int
    created_at: str | None = None

    class Config:
        from_attributes = True


class ConcertDetailOut(ConcertOut):
    """Esquema de respuesta detallada incluyendo métricas de venta."""

    tickets_vendidos: int


@router.get("/", response_model=list[ConcertOut], summary="Listar todos los conciertos")
def list_concerts(db: Session = Depends(get_db)) -> list[ConcertOut]:
    """Obtiene todos los conciertos registrados en el sistema."""
    concerts = db.query(Concert).all()
    return [
        ConcertOut(
            id=concert.id,
            title=concert.title,
            artist=concert.artist,
            description=concert.description or "",
            price=concert.price,
            stock=concert.stock,
            created_at=str(concert.created_at) if concert.created_at else None,
        )
        for concert in concerts
    ]


@router.post(
    "/",
    response_model=ConcertOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo concierto",
)
def create_concert(
    concert_payload: ConcertCreate, db: Session = Depends(get_db)
) -> dict:
    """Registra un nuevo concierto con sus datos de precio y stock inicial."""
    new_concert = Concert(
        title=concert_payload.title,
        artist=concert_payload.artist,
        description=concert_payload.description,
        price=concert_payload.price,
        stock=concert_payload.stock,
    )
    db.add(new_concert)
    db.commit()
    db.refresh(new_concert)
    return new_concert.to_dict()


@router.get(
    "/{concert_id}",
    response_model=ConcertDetailOut,
    summary="Obtener detalle de concierto por ID",
)
def get_concert(concert_id: int, db: Session = Depends(get_db)) -> ConcertDetailOut:
    """Obtiene el detalle de un concierto y suma sus entradas vendidas mediante agregación SQL."""
    concert = db.query(Concert).filter(Concert.id == concert_id).first()
    if not concert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Concierto no encontrado"
        )

    sold_tickets = (
        db.query(func.coalesce(func.sum(Purchase.quantity), 0))
        .filter(Purchase.concert_id == concert_id)
        .scalar()
    )

    return ConcertDetailOut(
        id=concert.id,
        title=concert.title,
        artist=concert.artist,
        description=concert.description or "",
        price=concert.price,
        stock=concert.stock,
        tickets_vendidos=int(sold_tickets),
        created_at=str(concert.created_at) if concert.created_at else None,
    )
