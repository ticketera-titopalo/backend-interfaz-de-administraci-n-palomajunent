from sqlalchemy import Column, Integer, Float, DateTime, String, func
from ..core.database import Base
from ..models.user import User
from ..models.concert import Concert

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    concert_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="completed")
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    redeemed = Column(Integer, nullable=False, default=0)
    
    # Relaciones
    user = None  # Will be set by relationship if needed
    concert = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "concert_id": self.concert_id,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "status": self.status,
            "purchased_at": str(self.purchased_at) if self.purchased_at else None,
            "redeemed": self.redeemed
        }
    
    def calcular_total(self, price_per_ticket):
        """Calcular precio total basado en precio por ticket."""
        return round(price_per_ticket * self.quantity, 2)
