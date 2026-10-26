
from pydantic import BaseModel, ConfigDict, Field


class RestaurantTableCreate(BaseModel):
    table_number: int = Field(gt=0)


class RestaurantTableUpdate(BaseModel):
    table_number: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RestaurantTableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_number: int
    qr_code_token: str
    is_active: bool
