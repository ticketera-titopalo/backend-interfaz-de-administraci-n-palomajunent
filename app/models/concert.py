from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func
from ..core.database import Base

class Concert(Base):
    __tablename__ = "concerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "created_at": str(self.created_at) if self.created_at else None
        }
    
    def tickets_disponibles(self):
        """Retorna la cantidad de tickets aún disponibles."""
        return self.stock
    
    def reducir_stock(self, cantidad):
        """Reducir el stock en la cantidad especificada."""
        self.stock = max(0, self.stock - cantidad)
