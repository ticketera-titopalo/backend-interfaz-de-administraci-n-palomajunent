from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Configuración JWT desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY", "tu-secreto-aqui-para-development")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crear token de acceso JWT.
    
    Args:
        data: Diccionario con los datos para codificar en el token (generalmente 'sub' y otros claims).
        expires_delta: Tiempo opcional hasta el expiration. Si no se proporciona,
            usará el valor default de ACCESS_TOKEN_EXPIRE_MINUTES.
    
    Returns:
        String con el token JWT codificado.
    
    Example:
        >>> from datetime import timedelta
        >>> token = create_access_token({"sub": "1", "email": "user@example.com"})
        >>> len(token) > 0  # True
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """Crear token de refresh JWT.
    
    Args:
        data: Diccionario con los datos para codificar en el token (generalmente 'sub' y email).
        expires_delta: Tiempo opcional hasta el expiration. Si no se proporciona,
            usará el valor default de REFRESH_TOKEN_EXPIRE_DAYS.
    
    Returns:
        String con el token JWT refresh codificado.
    
    Example:
        >>> from datetime import timedelta
        >>> token = create_refresh_token({"sub": "1", "email": "user@example.com"})
        >>> token.startswith(" eyJhbGci ")  # Typical JWT format check
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Decodificar y validar token JWT.
    
    Args:
        token: String del token JWT a decodificar.
    
    Returns:
        Diccionario con el payload del token si es válido, None si el token
        es inválido o ha expirado.
    
    Raises:
        None: Esta función captura JWTError internamente y retorna None.
    
    Example:
        >>> payload = decode_token("valid.jwt.token")
        >>> payload.get("sub")  # Returns the subject/username
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        logger.warning("Attempted to decode invalid or expired JWT token")
        return None


def verify_token_header(authorization: str):
    """Verificar y extraer token del header Authorization.
    
    Args:
        authorization: Valor del header Authorization (ej. 'Bearer eyJhbGci...').
    
    Returns:
        String con el token JWT si el header tiene el formato correcto 'Bearer <token>',
        None si el header está vacío, es None, o el scheme no es 'bearer'.
    
    Example:
        >>> verify_token_header("Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiw")
        'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiw'
        >>> verify_token_header(None)
        None
        >>> verify_token_header("Basic somecreds")
        None
    """
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token
