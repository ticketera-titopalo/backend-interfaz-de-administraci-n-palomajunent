from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from fastapi import Depends, HTTPException, status
import os
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Configurar desde variables de entorno
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "mysql+pymysql://ticketera_admin:admin_password@localhost:3306/ticketera_admin_db"
)

# Motor síncrono para crear tablas al iniciar - con timeout de 30segundos
engine = create_engine(
    DATABASE_URI,
    pool_timeout=30,
    max_overflow=0,
    echo=False
)

# Motor asíncrono para peticiones reales
async_engine = create_async_engine(
    DATABASE_URI.replace("mysql+pymysql", "mysql+asyncmy"),
    echo=False,
    pool_timeout=30,
    max_overflow=0,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """Dependencia para obtener sesión de BD con timeout configurado."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
