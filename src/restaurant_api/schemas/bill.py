from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .order import AdminOrderRead


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dining_session_id: int
    table_id: int
    table_number: int
    status: str
    subtotal_paisa: int
    total_paisa: int
    included_order_count: int
    created_at: datetime
    paid_at: datetime | None
    confirmed_at: datetime | None
    included_orders: list[AdminOrderRead]
    excluded_cancelled_orders: list[AdminOrderRead]
