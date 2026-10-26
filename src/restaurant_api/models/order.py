
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'preparing', 'ready', "
            "'served', 'completed', 'cancelled')",
            name="ck_orders_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("dining_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    total_price_paisa: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["DiningSession"] = relationship(
        back_populates="orders",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    @property
    def table(self) -> "RestaurantTable":
        return self.session.table


class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint(
            "unit_price_paisa >= 0",
            name="ck_order_items_unit_price",
        ),
        CheckConstraint(
            "status IN ('pending', 'preparing', 'ready', 'completed', 'cancelled')",
            name="ck_order_items_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Preserve the menu item's name and base price at ordering time
    item_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price_paisa: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="items",
    )

    item: Mapped["Item"] = relationship()

    selected_options: Mapped[list["OrderItemOption"]] = (
        relationship(
            back_populates="order_item",
            cascade="all, delete-orphan",
        )
    )


class OrderItemOption(Base):
    __tablename__ = "order_item_options"

    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            "option_id",
            name="uq_order_item_option",
        ),
        CheckConstraint(
            "extra_price_paisa >= 0",
            name="ck_order_item_options_price",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    option_id: Mapped[int] = mapped_column(
        ForeignKey("options.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Preserve the option's name and extra price at ordering time
    option_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    extra_price_paisa: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    order_item: Mapped["OrderItem"] = relationship(
        back_populates="selected_options",
    )

    option: Mapped["Option"] = relationship()
