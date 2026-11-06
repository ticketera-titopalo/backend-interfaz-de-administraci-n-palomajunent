from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.user import User
from ..core.security import verify_token_header, decode_token
from pydantic import BaseModel as PydanticBaseModel

# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["users"])

# Esquemas Pydantic
class UserOut(PydanticBaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: str
    
    class Config:
        from_attributes = True

class UserProfileUpdate(PydanticBaseModel):
    full_name: str = None
    email: str = None

class UserPasswordChange(PydanticBaseModel):
    old_password: str
    new_password: str

# Dependency opcional para token
def get_token_header(authorization: str = Header(None)):
    """Obtener header Authorization, opcional."""
    if authorization is None:
        return None
    return verify_token_header(authorization)

# Endpoint para listar todos los usuarios (admin)
@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Listar todos los usuarios."""
    users = db.query(User).all()
    return [user.to_dict() for user in users]

# Endpoint: GET /api/users/me - Perfil del usuario autenticado
@router.get("/me", response_model=UserOut)
def get_my_profile(token: str = Depends(get_token_header), db: Session = Depends(get_db)):
    """Perfil del usuario autenticado con JWT token."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )
    
    return user.to_dict()

# Endpoint: PUT /api/users/me - Editar perfil del usuario autenticado
@router.put("/me", response_model=UserOut)
def update_my_profile(data: UserProfileUpdate, token: str = Depends(get_token_header), db: Session = Depends(get_db)):
    """Editar perfil del usuario autenticado."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )
    
    # Validar y actualizar email si se proporcionó y es diferente
    if data.email is not None and data.email != user.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso",
            )
        user.email = data.email
    
    # Actualizar nombre completo si se proporcionó
    if data.full_name is not None:
        user.full_name = data.full_name
    
    db.commit()
    db.refresh(user)
    
    return user.to_dict()

# Endpoint: POST /api/users/password - Cambiar contraseña
@router.post("/password", response_model=dict)
def change_password(data: UserPasswordChange, token: str = Depends(get_token_header), db: Session = Depends(get_db)):
    """Cambiar contraseña del usuario autenticado."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )
    
    # Verificar contraseña actual usando passlib
    if not user.verify_password(data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )
    
    # Generar nuevo hash y actualizar
    user.password_hash = user.get_hash_password(data.new_password)
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}
