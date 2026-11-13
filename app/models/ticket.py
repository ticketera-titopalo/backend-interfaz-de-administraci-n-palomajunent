from sqlalchemy import Column, DateTime, Float, Integer, String, func

from ..core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    concert_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    price_paid = Column(Float, nullable=False)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    redeemed = Column(
        Integer, nullable=False, default=0
    )  # 0 = no usado, 1 = usado en puerta
    qr_code = Column(String(255), unique=True, nullable=False)

    # Relaciones
    concert = None
    user = None

    def to_dict(self):
        return {
            "id": self.id,
            "concert_id": self.concert_id,
            "user_id": self.user_id,
            "price_paid": self.price_paid,
            "purchased_at": str(self.purchased_at) if self.purchased_at else None,
            "redeemed": self.redeemed,
            "qr_code": self.qr_code,
        }

    @staticmethod
    def generar_qr_code():
        """Genera un código QR único (simulación con hash corto)."""
        import hashlib
        import time

        data = f"{time.time()}{id(Ticket)}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
