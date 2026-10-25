from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints


MenuName = Annotated[
	str,
	StringConstraints(strip_whitespace=True, min_length=1),
]

class OptionCreateInGroup(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=100)]


class OptionRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	group_id: int


class OptionGroupCreate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=100)]
	options: list[OptionCreateInGroup] = Field(default_factory=list)


class OptionGroupUpdate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=100)] | None = None


class OptionGroupRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	options: list[OptionRead] = Field(default_factory=list)


class PaginationMeta(BaseModel):
	page: int
	page_size: int
	total: int
	total_pages: int


class ItemPage(BaseModel):
	items: list["ItemRead"] = Field(default_factory=list)
	pagination: PaginationMeta


class OptionGroupPage(BaseModel):
	groups: list[OptionGroupRead] = Field(default_factory=list)
	pagination: PaginationMeta


class OptionPage(BaseModel):
	options: list[OptionRead] = Field(default_factory=list)
	pagination: PaginationMeta


class OptionCreate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=100)]
	group_id: PositiveInt


class OptionUpdate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=100)] | None = None
	group_id: PositiveInt | None = None


class ItemOptionPriceCreate(BaseModel):
	option_id: PositiveInt
	extra_price_paisa: Annotated[int, Field(ge=0)] = 0


class ItemOptionPriceUpdate(BaseModel):
	extra_price_paisa: Annotated[int, Field(ge=0)] = 0


class ItemOptionPriceRead(ItemOptionPriceCreate):
	model_config = ConfigDict(from_attributes=True)


class ItemCreate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=150)]
	base_price_paisa: Annotated[int, Field(ge=0)] = 0
	option_group_ids: list[PositiveInt] = Field(default_factory=list)
	item_options: list[ItemOptionPriceCreate] = Field(default_factory=list)


class ItemUpdate(BaseModel):
	name: Annotated[MenuName, StringConstraints(max_length=150)] | None = None
	base_price_paisa: Annotated[int, Field(ge=0)] | None = None
	option_group_ids: list[PositiveInt] | None = None
	item_options: list[ItemOptionPriceCreate] | None = None


class ItemRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	base_price_paisa: int
	option_groups: list[OptionGroupRead] = Field(default_factory=list)
	item_options: list[ItemOptionPriceRead] = Field(default_factory=list)
