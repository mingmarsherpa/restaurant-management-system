from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class DiningSession(Base):
    __tablename__ = "dining_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_dining_sessions_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    table_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant_tables.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="open"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    orderer_token_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    orderer_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    table: Mapped["RestaurantTable"] = relationship(
        back_populates="sessions",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )

    bill: Mapped["Bill | None"] = relationship(
        back_populates="dining_session",
        uselist=False,
    )