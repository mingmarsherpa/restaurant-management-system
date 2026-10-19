
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List
from ..database import Base


# Links foods to option groups
item_option_groups = Table(
    "item_option_groups",
    Base.metadata,
    Column(
        "item_id",
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "group_id",
        ForeignKey("option_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Base price of the food, stored in paisa
    base_price_paisa: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Which option groups does this food use?
    option_groups: Mapped[List["OptionGroup"]] = relationship(
        secondary=item_option_groups,
        back_populates="items",
    )

    # Which individual options and prices does this food offer?
    item_options: Mapped[List["ItemOption"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )


class OptionGroup(Base):
    __tablename__ = "option_groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    items: Mapped[List["Item"]] = relationship(
        secondary=item_option_groups,
        back_populates="option_groups",
    )

    options: Mapped[List["Option"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("option_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["OptionGroup"] = relationship(
        back_populates="options",
    )

    # Foods that offer this option
    item_options: Mapped[List["ItemOption"]] = relationship(
        back_populates="option",
    )


class ItemOption(Base):
    __tablename__ = "item_options"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    )

    option_id: Mapped[int] = mapped_column(
        ForeignKey("options.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Extra charge depends on the food
    extra_price_paisa: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    item: Mapped["Item"] = relationship(
        back_populates="item_options",
    )

    option: Mapped["Option"] = relationship(
        back_populates="item_options",
    )
