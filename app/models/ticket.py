from sqlalchemy import Column, Integer, String, Float, DateTime, func
from ..core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    price_paid = Column(Float, nullable=False)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    redeemed = Column(Integer, nullable=False, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "concert_id": self.concert_id,
            "user_id": self.user_id,
            "price_paid": self.price_paid,
            "purchased_at": str(self.purchased_at) if self.purchased_at else None,
            "redeemed": self.redeemed
        }
