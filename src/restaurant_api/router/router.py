from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.menu import Item, ItemOption, Option, OptionGroup
from ..schemas.menu import (
	ItemCreate,
	ItemOptionPriceRead,
	ItemOptionPriceUpdate,
	ItemPage,
	ItemRead,
	ItemUpdate,
	OptionCreate,
	OptionGroupPage,
	OptionGroupCreate,
	OptionGroupRead,
	OptionGroupUpdate,
	OptionPage,
	OptionRead,
	OptionUpdate,
)


router = APIRouter(prefix="/api/menu", tags=["menu"])


async def _commit(session: AsyncSession) -> None:
	try:
		await session.commit()
	except Exception:
		await session.rollback()
		raise


def _pagination(page: int, page_size: int, total: int) -> dict[str, int]:
	return {
		"page": page,
		"page_size": page_size,
		"total": total,
		"total_pages": (total + page_size - 1) // page_size if total else 0,
	}


def _unique_ids(ids: Sequence[int]) -> list[int]:
	unique = list(dict.fromkeys(ids))
	if len(unique) != len(ids):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Duplicate resource IDs are not allowed",
		)
	return unique


async def _get_groups(session: AsyncSession, group_ids: Sequence[int]) -> list[OptionGroup]:
	group_ids = _unique_ids(group_ids)
	if not group_ids:
		return []

	result = await session.scalars(
		select(OptionGroup)
		.where(OptionGroup.id.in_(group_ids))
		.order_by(OptionGroup.id)
	)
	groups = list(result)
	if len(groups) != len(group_ids):
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="One or more option groups were not found",
		)
	return groups


async def _get_options(session: AsyncSession, option_ids: Sequence[int]) -> list[Option]:
	option_ids = _unique_ids(option_ids)
	if not option_ids:
		return []

	result = await session.scalars(
		select(Option).where(Option.id.in_(option_ids)).order_by(Option.id)
	)
	options = list(result)
	if len(options) != len(option_ids):
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="One or more options were not found",
		)
	return options


def _validate_option_groups(
	groups: Sequence[OptionGroup],
	options: Sequence[Option],
) -> None:
	group_ids = {group.id for group in groups}
	if group_ids and any(option.group_id not in group_ids for option in options):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Every item option must belong to one of the item's option groups",
		)


async def _load_item(session: AsyncSession, item_id: int) -> Item:
	result = await session.execute(
		select(Item)
		.options(
			selectinload(Item.option_groups).selectinload(OptionGroup.options),
			selectinload(Item.item_options).selectinload(ItemOption.option),
		)
		.where(Item.id == item_id)
	)
	item = result.scalar_one_or_none()
	if item is None:
		raise HTTPException(status_code=404, detail="Item not found")
	return item


async def _load_group(session: AsyncSession, group_id: int) -> OptionGroup:
	result = await session.execute(
		select(OptionGroup)
		.options(selectinload(OptionGroup.options))
		.where(OptionGroup.id == group_id)
	)
	group = result.scalar_one_or_none()
	if group is None:
		raise HTTPException(status_code=404, detail="Option group not found")
	return group


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, session: AsyncSession = Depends(get_db)) -> Item:
	groups = await _get_groups(session, payload.option_group_ids)
	options = await _get_options(
		session,
		[item_option.option_id for item_option in payload.item_options],
	)
	_validate_option_groups(groups, options)
	options_by_id = {option.id: option for option in options}

	item = Item(name=payload.name, base_price_paisa=payload.base_price_paisa)
	item.option_groups = groups
	item.item_options = [
		ItemOption(
			option=options_by_id[item_option.option_id],
			extra_price_paisa=item_option.extra_price_paisa,
		)
		for item_option in payload.item_options
	]
	session.add(item)
	await _commit(session)
	return await _load_item(session, item.id)


@router.get("/items", response_model=ItemPage)
async def list_items(
	page: int = Query(1, ge=1),
	page_size: int = Query(5, ge=1, le=100),
	session: AsyncSession = Depends(get_db),
) -> dict:
	total = await session.scalar(select(func.count()).select_from(Item))
	result = await session.execute(
		select(Item)
		.options(
			selectinload(Item.option_groups).selectinload(OptionGroup.options),
			selectinload(Item.item_options).selectinload(ItemOption.option),
		)
		.order_by(Item.id)
		.offset((page - 1) * page_size)
		.limit(page_size)
	)
	return {
		"items": list(result.scalars().unique()),
		"pagination": _pagination(page, page_size, total or 0),
	}


@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, session: AsyncSession = Depends(get_db)) -> Item:
	return await _load_item(session, item_id)


@router.patch("/items/{item_id}", response_model=ItemRead)
async def update_item(
	item_id: int,
	payload: ItemUpdate,
	session: AsyncSession = Depends(get_db),
) -> Item:
	item = await _load_item(session, item_id)
	values = payload.model_dump(exclude_unset=True)

	if "name" in values:
		item.name = values["name"]
	if "base_price_paisa" in values:
		item.base_price_paisa = values["base_price_paisa"]
	if "option_group_ids" in values:
		item.option_groups = await _get_groups(session, values["option_group_ids"])
	if "item_options" in values:
		item_options = values["item_options"]
		options = await _get_options(
			session,
			[item_option["option_id"] for item_option in item_options],
		)
		_validate_option_groups(item.option_groups, options)
		options_by_id = {option.id: option for option in options}
		item.item_options = [
			ItemOption(
				option=options_by_id[item_option["option_id"]],
				extra_price_paisa=item_option["extra_price_paisa"],
			)
			for item_option in item_options
		]
	elif "option_group_ids" in values:
		_validate_option_groups(
			item.option_groups,
			[item_option.option for item_option in item.item_options],
		)

	await _commit(session)
	return await _load_item(session, item_id)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, session: AsyncSession = Depends(get_db)) -> Response:
	item = await _load_item(session, item_id)
	await session.delete(item)
	await _commit(session)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
	"/option-groups",
	response_model=OptionGroupRead,
	status_code=status.HTTP_201_CREATED,
)
async def create_option_group(
	payload: OptionGroupCreate,
	session: AsyncSession = Depends(get_db),
) -> OptionGroup:
	group = OptionGroup(name=payload.name)
	group.options = [Option(name=option.name) for option in payload.options]
	session.add(group)
	await _commit(session)
	return await _load_group(session, group.id)


@router.get("/option-groups", response_model=OptionGroupPage)
async def list_option_groups(
	page: int = Query(1, ge=1),
	page_size: int = Query(5, ge=1, le=100),
	session: AsyncSession = Depends(get_db),
) -> dict:
	total = await session.scalar(select(func.count()).select_from(OptionGroup))
	result = await session.execute(
		select(OptionGroup)
		.options(selectinload(OptionGroup.options))
		.order_by(OptionGroup.id)
		.offset((page - 1) * page_size)
		.limit(page_size)
	)
	return {
		"groups": list(result.scalars().unique()),
		"pagination": _pagination(page, page_size, total or 0),
	}


@router.get("/option-groups/{group_id}", response_model=OptionGroupRead)
async def get_option_group(
	group_id: int,
	session: AsyncSession = Depends(get_db),
) -> OptionGroup:
	return await _load_group(session, group_id)


@router.patch("/option-groups/{group_id}", response_model=OptionGroupRead)
async def update_option_group(
	group_id: int,
	payload: OptionGroupUpdate,
	session: AsyncSession = Depends(get_db),
) -> OptionGroup:
	group = await _load_group(session, group_id)
	if payload.name is not None:
		group.name = payload.name
	await _commit(session)
	return await _load_group(session, group_id)


@router.delete("/option-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option_group(
	group_id: int,
	session: AsyncSession = Depends(get_db),
) -> Response:
	group = await _load_group(session, group_id)
	await session.delete(group)
	await _commit(session)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/options", response_model=OptionRead, status_code=status.HTTP_201_CREATED)
async def create_option(
	payload: OptionCreate,
	session: AsyncSession = Depends(get_db),
) -> Option:
	group = await session.get(OptionGroup, payload.group_id)
	if group is None:
		raise HTTPException(status_code=404, detail="Option group not found")
	option = Option(name=payload.name, group=group)
	session.add(option)
	await _commit(session)
	return option


@router.get("/options", response_model=OptionPage)
async def list_options(
	group_id: int | None = None,
	page: int = Query(1, ge=1),
	page_size: int = Query(5, ge=1, le=100),
	session: AsyncSession = Depends(get_db),
) -> dict:
	query = select(Option).order_by(Option.id)
	count_query = select(func.count()).select_from(Option)
	if group_id is not None:
		query = query.where(Option.group_id == group_id)
		count_query = count_query.where(Option.group_id == group_id)
	total = await session.scalar(count_query)
	query = query.offset((page - 1) * page_size).limit(page_size)
	result = await session.scalars(query)
	return {
		"options": list(result),
		"pagination": _pagination(page, page_size, total or 0),
	}


@router.get("/options/{option_id}", response_model=OptionRead)
async def get_option(option_id: int, session: AsyncSession = Depends(get_db)) -> Option:
	option = await session.get(Option, option_id)
	if option is None:
		raise HTTPException(status_code=404, detail="Option not found")
	return option


@router.patch("/options/{option_id}", response_model=OptionRead)
async def update_option(
	option_id: int,
	payload: OptionUpdate,
	session: AsyncSession = Depends(get_db),
) -> Option:
	option = await session.get(Option, option_id)
	if option is None:
		raise HTTPException(status_code=404, detail="Option not found")
	values = payload.model_dump(exclude_unset=True)
	if "name" in values:
		option.name = values["name"]
	if "group_id" in values:
		group = await session.get(OptionGroup, values["group_id"])
		if group is None:
			raise HTTPException(status_code=404, detail="Option group not found")
		option.group = group
	await _commit(session)
	return option


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(option_id: int, session: AsyncSession = Depends(get_db)) -> Response:
	option = await session.get(Option, option_id)
	if option is None:
		raise HTTPException(status_code=404, detail="Option not found")
	await session.delete(option)
	await _commit(session)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
	"/items/{item_id}/options/{option_id}",
	response_model=ItemOptionPriceRead,
)
async def set_item_option_price(
	item_id: int,
	option_id: int,
	payload: ItemOptionPriceUpdate,
	session: AsyncSession = Depends(get_db),
) -> ItemOption:
	item = await _load_item(session, item_id)
	option = await session.get(Option, option_id)
	if option is None:
		raise HTTPException(status_code=404, detail="Option not found")
	_validate_option_groups(item.option_groups, [option])

	item_option = await session.get(
		ItemOption,
		{"item_id": item_id, "option_id": option_id},
	)
	if item_option is None:
		item_option = ItemOption(
			item=item,
			option=option,
			extra_price_paisa=payload.extra_price_paisa,
		)
		session.add(item_option)
	else:
		item_option.extra_price_paisa = payload.extra_price_paisa
	await _commit(session)
	return item_option


@router.delete(
	"/items/{item_id}/options/{option_id}",
	status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_item_option_price(
	item_id: int,
	option_id: int,
	session: AsyncSession = Depends(get_db),
) -> Response:
	item_option = await session.get(
		ItemOption,
		{"item_id": item_id, "option_id": option_id},
	)
	if item_option is None:
		raise HTTPException(status_code=404, detail="Item option price not found")
	await session.delete(item_option)
	await _commit(session)
	return Response(status_code=status.HTTP_204_NO_CONTENT)
