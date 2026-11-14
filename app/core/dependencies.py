"""Dependencias y utilidades compartidas para validación, rate limiting y consultas."""

import time

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User
from .database import get_db
from .security import decode_token, verify_token_header

_rate_limit_storage: dict[str, list[float]] = {}


def check_rate_limit(
    rate_key: str,
    limit: int,
    period_seconds: float,
    error_detail: str,
    include_auth_header: bool = False,
) -> bool:
    """Verifica y registra intentos por clave dentro de una ventana de tiempo."""
    current_time = time.time()
    timestamps = _rate_limit_storage.get(rate_key, [])
    valid_timestamps = [ts for ts in timestamps if current_time - ts < period_seconds]

    if len(valid_timestamps) >= limit:
        _rate_limit_storage[rate_key] = valid_timestamps
        headers = {"WWW-Authenticate": "Bearer"} if include_auth_header else None
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_detail,
            headers=headers,
        )

    valid_timestamps.append(current_time)
    _rate_limit_storage[rate_key] = valid_timestamps
    return True


def get_entity_or_404(db: Session, model: type, entity_id: int, detail: str):
    """Busca un registro por ID o lanza HTTPException 404 si no existe."""
    instance = db.query(model).filter(model.id == entity_id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return instance


def get_active_user_by_id(
    db: Session, user_id: int, unauthorized_on_missing: bool = False
) -> User:
    """Obtiene un usuario por ID y verifica que se encuentre activo."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if unauthorized_on_missing
            else status.HTTP_404_NOT_FOUND
        )
        detail = (
            "Usuario no encontrado o inactivo"
            if unauthorized_on_missing
            else "Usuario no encontrado"
        )
        raise HTTPException(status_code=status_code, detail=detail)

    if not user.is_active:
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if unauthorized_on_missing
            else status.HTTP_400_BAD_REQUEST
        )
        detail = (
            "Usuario no encontrado o inactivo"
            if unauthorized_on_missing
            else "Usuario inactivo"
        )
        raise HTTPException(status_code=status_code, detail=detail)

    return user


def get_current_active_user(
    token: str | None = Depends(verify_token_header),
    db: Session = Depends(get_db),
) -> User:
    """Decodifica el token Bearer JWT y retorna el usuario activo autenticado."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )

    payload = decode_token(token)
    if payload is None or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    return get_active_user_by_id(db, int(payload["sub"]))
