"""
Plan ORM model — lives in the `platform` schema.
"""
from typing import Optional
from sqlalchemy import Boolean, Numeric, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": "platform"}

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_etb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    max_referrals_per_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    features: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Plan id={self.id} name={self.name!r}>"
