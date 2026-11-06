from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.user import User
from ..core.security import create_access_token, create_refresh_token, decode_token, verify_token_header
from pydantic import BaseModel as PydanticBaseModel

# Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["auth"])

# Esquemas Pydantic
class LoginCredentials(PydanticBaseModel):
    email: str
    password: str

class TokenResponse(PydanticBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshToken(PydanticBaseModel):
    refresh_token: str

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    """Iniciar sesión y obtener tokens JWT."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    # Crear payload
    access_expires = timedelta(minutes=30)
    refresh_expires = timedelta(days=7)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": int(ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(refresh: RefreshToken, db: Session = Depends(get_db)):
    """Renovar token de acceso usando refresh token."""
    payload = decode_token(refresh.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    # Crear nuevos tokens
    access_expires = timedelta(minutes=30)
    refresh_expires = timedelta(days=7)
    
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": int(ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    """Cerrar sesión (en este ejemplo, solo retorna éxito)."""
    # En un sistema real, aquí invalidaríamos el token en Redis o base de datos
    return None
