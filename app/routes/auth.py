"""Rutas y lógica de autenticación JWT y control de rate limiting."""

import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import (create_access_token, create_refresh_token,
                             decode_token)
from ..models.user import User

RATE_LIMIT_LOGIN = 5
RATE_LIMIT_REFRESH = 3
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

router = APIRouter(prefix="/api", tags=["auth"])
auth_rate_limit_storage: dict[str, list[float]] = {}


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


def check_auth_rate_limit(rate_key: str, limit: int, period_seconds: float) -> bool:
    """Verifica y registra intentos por clave para prevenir fuerza bruta."""
    current_time = time.time()
    timestamps = auth_rate_limit_storage.get(rate_key, [])
    valid_timestamps = [ts for ts in timestamps if current_time - ts < period_seconds]

    if len(valid_timestamps) >= limit:
        auth_rate_limit_storage[rate_key] = valid_timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Máximo {limit} intentos por {period_seconds / 60} minutos. Intente más tarde.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    valid_timestamps.append(current_time)
    auth_rate_limit_storage[rate_key] = valid_timestamps
    return True


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


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    credentials: LoginCredentials,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict[str, str | int]:
    """Autentica al usuario con email y contraseña y emite tokens JWT."""
    client_ip = request.client.host if request and request.client else "unknown"
    check_auth_rate_limit(f"login_{client_ip}", RATE_LIMIT_LOGIN, 60)

    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )

    return _build_token_pair(user)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    refresh_payload: RefreshToken,
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict[str, str | int]:
    """Renueva el par de tokens JWT a partir de un refresh_token válido."""
    client_ip = request.client.host if request and request.client else "unknown"
    check_auth_rate_limit(f"refresh_{client_ip}", RATE_LIMIT_REFRESH, 3600)

    payload = decode_token(refresh_payload.refresh_token)
    if (
        payload is None
        or payload.get("type") != "refresh"
        or payload.get("sub") is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return _build_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """Cierra la sesión actual del cliente."""
    return None
