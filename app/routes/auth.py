"""Rutas y lógica de autenticación JWT y control de rate limiting."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import check_rate_limit, get_active_user_by_id
from ..core.security import create_access_token, create_refresh_token, decode_token
from ..models.user import User

RATE_LIMIT_LOGIN = 5
RATE_LIMIT_REFRESH = 3
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

router = APIRouter(prefix="/api", tags=["auth"])


class LoginCredentials(PydanticBaseModel):
    """Credenciales de entrada para inicio de sesión."""

    email: str
    password: str


class TokenResponse(PydanticBaseModel):
    """Respuesta estándar con par de tokens JWT."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshToken(PydanticBaseModel):
    """Solicitud de renovación de token de acceso."""

    refresh_token: str


def _get_client_ip(request: Request | None) -> str:
    """Obtiene la dirección IP del cliente desde el objeto Request."""
    return request.client.host if request and request.client else "unknown"


def _build_token_pair(user: User) -> dict[str, str | int]:
    """Genera un par nuevo de access_token y refresh_token para un usuario."""
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token_str = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def _authenticate_user(db: Session, email: str, password: str) -> User:
    """Valida email, contraseña y estado activo del usuario."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )
    return user


def _extract_refresh_user_id(raw_token: str) -> int:
    """Decodifica el refresh token y valida que contenga un subject válido."""
    payload = decode_token(raw_token)
    if not payload or payload.get("type") != "refresh" or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido",
        )
    return int(payload["sub"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    credentials: LoginCredentials,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict[str, str | int]:
    """Autentica al usuario con email y contraseña y emite tokens JWT."""
    check_rate_limit(
        f"login_{_get_client_ip(request)}",
        RATE_LIMIT_LOGIN,
        60,
        f"Máximo {RATE_LIMIT_LOGIN} intentos por 1.0 minutos. Intente más tarde.",
        include_auth_header=True,
    )
    user = _authenticate_user(db, credentials.email, credentials.password)
    return _build_token_pair(user)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    refresh_payload: RefreshToken,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict[str, str | int]:
    """Renueva el par de tokens JWT a partir de un refresh_token válido."""
    check_rate_limit(
        f"refresh_{_get_client_ip(request)}",
        RATE_LIMIT_REFRESH,
        3600,
        f"Máximo {RATE_LIMIT_REFRESH} intentos por 60.0 minutos. Intente más tarde.",
        include_auth_header=True,
    )
    user_id = _extract_refresh_user_id(refresh_payload.refresh_token)
    user = get_active_user_by_id(db, user_id, unauthorized_on_missing=True)
    return _build_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """Cierra la sesión actual del cliente."""
    return None
