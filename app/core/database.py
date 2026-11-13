import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Configurar logger
logger = logging.getLogger(__name__)

# Configurar desde variables de entorno
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "mysql+pymysql://ticketera_admin:admin123@db:3306/ticketera_admin_db",
)

# Motor síncrono para crear tablas al iniciar - con timeout de 30segundos
# pool_timeout: Tiempo máximo en segundos para obtener una conexión del pool
# max_overflow: Conexiones adicionales permitidas beyond pool_size
engine = create_engine(DATABASE_URI, pool_timeout=30, max_overflow=0, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Obtener sesión de base de datos con timeout configurado.

    Yields:
        Session: Sesión de SQLAlchemy para usar en endpoints de FastAPI.

    Example:
        >>> from fastapi import Depends
        >>> from fastapi.testclient import TestClient
        >>> from app.main import app
        >>> client = TestClient(app)
        >>> def get_session():
        ...     for db in get_db():
        ...         yield db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
