from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class OrderItemCreate(BaseModel):
    item_id: PositiveInt
    quantity: PositiveInt
    option_ids: list[PositiveInt] = Field(default_factory=list)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    option_id: int
    option_name: str
    extra_price_paisa: int


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_name: str
    quantity: int
    unit_price_paisa: int
    status: str
    selected_options: list[OrderItemOptionRead] = Field(default_factory=list)


class TableSummary(BaseModel):
    id: int
    table_number: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    status: str
    total_price_paisa: int
    created_at: datetime
    table: TableSummary
    items: list[OrderItemRead] = Field(default_factory=list)


class DiningSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_id: int
    status: str
    started_at: datetime
    closed_at: datetime | None


class OrderStatusUpdate(BaseModel):
    status: str


class AdminOrderRead(OrderRead):
    pass
