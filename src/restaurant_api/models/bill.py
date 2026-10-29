from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (
        UniqueConstraint("dining_session_id", name="uq_bills_dining_session_id"),
        CheckConstraint(
            "status IN ('open', 'paid', 'confirmed')",
            name="ck_bills_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dining_session_id: Mapped[int] = mapped_column(
        ForeignKey("dining_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")
    subtotal_paisa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_paisa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    included_order_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    dining_session: Mapped["DiningSession"] = relationship(
        back_populates="bill",
    )
