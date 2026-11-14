from sqlalchemy import Column, DateTime, Float, Integer, String, func

from ..core.database import Base


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
    user = None
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
            "redeemed": self.redeemed,
        }

    def calcular_total(self, price_per_ticket):
        """Calcular precio total basado en precio por ticket."""
        return round(price_per_ticket * self.quantity, 2)

    def get_tickets(self):
        """Retorna la lista de tickets asociados a esta compra."""
        # En un sistema real, estoiría una relación muchos-a-muchos con la tabla tickets
        # Por ahora retornamos la info básica basada en el concierto
        if self.concert:
            return [
                {
                    "id": f"ticket_{self.id}_{i}",
                    "concert_id": self.concert_id,
                    "concert_title": self.concert.title,
                    "concert_artist": self.concert.artist,
                    "price": self.concert.price,
                    "redeemed": 0 if i < self.quantity else 1,
                }
                for i in range(self.quantity)
            ]
        return []
