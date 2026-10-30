from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Configurar desde variables de entorno
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "mysql+pymysql://ticketera_admin:admin_password@localhost:3306/ticketera_admin_db"
)

# Motor síncrono para crear tablas al iniciar
engine = create_engine(DATABASE_URI)

# Motor asíncrono para peticiones reales
async_engine = create_async_engine(
    DATABASE_URI.replace("mysql+pymysql", "mysql+asyncmy"),
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
