from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    table_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    qr_code_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    sessions: Mapped[list["DiningSession"]] = relationship(
        back_populates="table",
    )