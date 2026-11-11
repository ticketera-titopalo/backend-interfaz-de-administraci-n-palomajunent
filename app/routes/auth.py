from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from ..core.database import get_db, engine, Base
from ..models.user import User
from ..core.security import create_access_token, create_refresh_token, decode_token, verify_token_header
from pydantic import BaseModel as PydanticBaseModel
import time

# Constantes de rate limiting
RATE_LIMIT_LOGIN = 5  # 5 intentos por minuto
RATE_LIMIT_REFRESH = 3  # 3 intentos por hora

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

# Rate limiter para endpoints de auth
auth_rate_limit_storage = {}

def check_auth_rate_limit(key: str, limit: int, period: float) -> bool:
    """Verificar límite de tasa para endpoints de auth."""
    now = time.time()
    if key not in auth_rate_limit_storage:
        auth_rate_limit_storage[key] = []
    
    # Limpiar entradas viejas
    auth_rate_limit_storage[key] = [t for t in auth_rate_limit_storage[key] if now - t < period]
    
    if len(auth_rate_limit_storage[key]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Máximo {limit} intentos por {period/60} minutos. Intente más tarde.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_rate_limit_storage[key].append(now)
    return True

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(credentials: LoginCredentials, db: Session = Depends(get_db), request: Request = None):
    """Iniciar sesión y obtener tokens JWT."""
    # Rate limiting para login - 5 intentos por minuto por IP
    client_ip = request.client.host if request else "unknown"
    rate_key = f"login_{client_ip}"
    
    if not check_auth_rate_limit(rate_key, RATE_LIMIT_LOGIN, 60):
        raise HTTPException(status_code=429, detail="Demasiados intentos de login")
    
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
def refresh_token(refresh: RefreshToken, db: Session = Depends(get_db), request: Request = None):
    """Renovar token de acceso usando refresh token."""
    # Rate limiting para refresh token - 3 intentos por hora por IP
    client_ip = request.client.host if request else "unknown"
    rate_key = f"refresh_{client_ip}"
    
    if not check_auth_rate_limit(rate_key, RATE_LIMIT_REFRESH, 3600):
        raise HTTPException(status_code=429, detail="Demasiados intentos de refresh")
    
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
