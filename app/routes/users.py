"""Rutas y esquemas para la gestión y perfil de usuarios."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, validator
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import decode_token, verify_token_header
from ..models.user import User

router = APIRouter(prefix="/api", tags=["Usuarios"])

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class UserOut(PydanticBaseModel):
    """Esquema de salida con los datos públicos de un usuario."""

    id: int
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class UserProfileUpdate(PydanticBaseModel):
    """Esquema de entrada para actualizar perfil de usuario."""

    full_name: str | None = Field(
        default=None, max_length=100, description="Nombre completo"
    )
    email: str | None = Field(default=None, max_length=255, description="Email")

    @validator("email")
    def validate_email_format(cls, email_value: str | None) -> str | None:
        """Valida que el formato del correo electrónico sea correcto."""
        if email_value is not None and not re.match(EMAIL_REGEX, email_value):
            raise ValueError("Formato de email inválido")
        return email_value


class UserPasswordChange(PydanticBaseModel):
    """Esquema de entrada para el cambio de contraseña."""

    old_password: str = Field(
        ..., min_length=6, max_length=128, description="Contraseña actual"
    )
    new_password: str = Field(
        ..., min_length=6, max_length=128, description="Contraseña nueva"
    )


def _get_authenticated_active_user(token: str | None, db: Session) -> User:
    """Decodifica el token JWT y retorna el usuario activo correspondiente.

    Args:
        token: Token JWT extraído del encabezado Authorization.
        db: Sesión activa de base de datos.

    Returns:
        User: Instancia del modelo User autenticado y activo.

    Raises:
        HTTPException: Si el token es inválido/expirado o el usuario no existe/está inactivo.
    """
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

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
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
    return user


def _update_user_email(db: Session, user: User, new_email: str) -> None:
    """Verifica disponibilidad del nuevo correo electrónico y lo asigna al usuario."""
    if new_email == user.email:
        return

    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user and existing_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está en uso",
        )
    user.email = new_email


@router.get("/", response_model=list[UserOut], summary="Listar todos los usuarios")
def list_users(db: Session = Depends(get_db)) -> list[dict]:
    """Obtiene el listado completo de usuarios registrados en el sistema."""
    users = db.query(User).all()
    return [user.to_dict() for user in users]


@router.get(
    "/me", response_model=UserOut, summary="Obtener perfil de usuario autenticado"
)
def get_my_profile(
    token: str = Depends(verify_token_header),
    db: Session = Depends(get_db),
) -> dict:
    """Retorna los datos del perfil del usuario autenticado mediante JWT."""
    current_user = _get_authenticated_active_user(token, db)
    return current_user.to_dict()


@router.put("/me", response_model=UserOut, summary="Editar perfil de usuario")
def update_my_profile(
    profile_payload: UserProfileUpdate | None = None,
    token: str = Depends(verify_token_header),
    db: Session = Depends(get_db),
) -> dict:
    """Actualiza el nombre completo y/o correo electrónico del usuario autenticado."""
    current_user = _get_authenticated_active_user(token, db)
    if profile_payload is None:
        return current_user.to_dict()

    if profile_payload.email is not None:
        _update_user_email(db, current_user, profile_payload.email)

    if profile_payload.full_name is not None:
        current_user.full_name = profile_payload.full_name

    db.commit()
    db.refresh(current_user)
    return current_user.to_dict()


@router.post("/password", response_model=dict, summary="Cambiar contraseña de usuario")
def change_password(
    password_payload: UserPasswordChange | None = None,
    token: str = Depends(verify_token_header),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Valida la contraseña actual y actualiza el hash con la nueva contraseña."""
    current_user = _get_authenticated_active_user(token, db)
    if password_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de contraseña requeridos",
        )

    if not current_user.verify_password(password_payload.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )

    current_user.password_hash = current_user.get_hash_password(
        password_payload.new_password
    )
    db.commit()
    return {"message": "Contraseña actualizada exitosamente"}