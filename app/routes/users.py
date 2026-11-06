from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.user import User
from pydantic import BaseModel as PydanticBaseModel

router = APIRouter(prefix="/api/users", tags=["users"])

# Esquemas Pydantic
class UserCreate(PydanticBaseModel):
    email: str
    password: str
    full_name: str = ""
    role: str = "admin"

class UserOut(PydanticBaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Listar todos los usuarios."""
    users = db.query(User).all()
    return [user.to_dict() for user in users]

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario."""
    # Verificar si el usuario ya existe
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    db_user = User(
        email=user.email,
        password_hash=user.password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.to_dict()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario por ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user.to_dict()

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    """Actualizar un usuario."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db_user.email = user.email
    db_user.password_hash = user.password
    db_user.full_name = user.full_name
    db_user.role = user.role
    db.commit()
    db.refresh(db_user)
    return db_user.to_dict()

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Eliminar un usuario."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return None
