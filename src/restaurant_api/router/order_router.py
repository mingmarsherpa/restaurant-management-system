from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.dining_session import DiningSession
from ..models.menu import Item, ItemOption
from ..models.order import Order, OrderItem, OrderItemOption
from ..models.table import RestaurantTable
from ..schemas.order import (
    AdminOrderRead,
    DiningSessionRead,
    OrderCreate,
    OrderRead,
    OrderStatusUpdate,
)


router = APIRouter(tags=["orders"])


async def _get_table(
    table_id: int,
    session: AsyncSession,
) -> RestaurantTable:
    table = await session.get(RestaurantTable, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if not table.is_active:
        raise HTTPException(status_code=409, detail="Table is inactive")
    return table


async def _get_open_session(
    table_id: int,
    session: AsyncSession,
) -> DiningSession:
    result = await session.scalars(
        select(DiningSession)
        .where(
            DiningSession.table_id == table_id,
            DiningSession.status == "open",
        )
        .order_by(DiningSession.id.desc())
    )
    dining_session = result.first()
    if dining_session is not None:
        return dining_session

    dining_session = DiningSession(table_id=table_id)
    session.add(dining_session)
    await session.flush()
    return dining_session


async def _load_order(
    order_id: int,
    session: AsyncSession,
) -> Order:
    result = await session.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.selected_options),
            selectinload(Order.session).selectinload(DiningSession.table),
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _validate_status(value: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Status must be one of: {', '.join(sorted(allowed))}",
        )
    return value


async def _load_order_for_table(
    table_id: int,
    order_id: int,
    session: AsyncSession,
) -> Order:
    await _get_table(table_id, session)
    result = await session.execute(
        select(Order)
        .join(Order.session)
        .where(Order.id == order_id, DiningSession.table_id == table_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.selected_options),
            selectinload(Order.session).selectinload(DiningSession.table),
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get(
    "/api/tables/{table_id}/sessions/current",
    response_model=DiningSessionRead,
)
async def get_current_session(
    table_id: int,
    session: AsyncSession = Depends(get_db),
) -> DiningSession:
    await _get_table(table_id, session)
    dining_session = await _get_open_session(table_id, session)
    await session.commit()
    return dining_session


@router.post(
    "/api/tables/{table_id}/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    table_id: int,
    payload: OrderCreate,
    session: AsyncSession = Depends(get_db),
) -> Order:
    await _get_table(table_id, session)
    dining_session = await _get_open_session(table_id, session)

    item_ids = [entry.item_id for entry in payload.items]
    if len(set(item_ids)) != len(item_ids):
        raise HTTPException(
            status_code=400,
            detail="Each menu item may only appear once in an order",
        )

    result = await session.execute(
        select(Item)
        .options(selectinload(Item.item_options).selectinload(ItemOption.option))
        .where(Item.id.in_(item_ids))
    )
    items_by_id = {item.id: item for item in result.scalars().unique()}
    if len(items_by_id) != len(item_ids):
        raise HTTPException(status_code=404, detail="One or more items not found")

    order = Order(session=dining_session, status="pending")
    total = 0
    for entry in payload.items:
        item = items_by_id[entry.item_id]
        prices_by_option_id = {
            item_option.option_id: item_option
            for item_option in item.item_options
        }
        if len(set(entry.option_ids)) != len(entry.option_ids):
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate options selected for {item.name}",
            )
        if any(option_id not in prices_by_option_id for option_id in entry.option_ids):
            raise HTTPException(
                status_code=400,
                detail=f"One or more options are invalid for {item.name}",
            )

        selected_options = [
            prices_by_option_id[option_id] for option_id in entry.option_ids
        ]
        unit_price = item.base_price_paisa + sum(
            option.extra_price_paisa for option in selected_options
        )
        order_item = OrderItem(
            item=item,
            item_name=item.name,
            quantity=entry.quantity,
            unit_price_paisa=unit_price,
            selected_options=[
                OrderItemOption(
                    option=option.option,
                    option_name=option.option.name,
                    extra_price_paisa=option.extra_price_paisa,
                )
                for option in selected_options
            ],
        )
        order.items.append(order_item)
        total += unit_price * entry.quantity

    order.total_price_paisa = total
    session.add(order)
    await session.commit()
    return await _load_order(order.id, session)


@router.get(
    "/api/tables/{table_id}/orders",
    response_model=list[OrderRead],
)
async def list_table_orders(
    table_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[Order]:
    await _get_table(table_id, session)
    result = await session.execute(
        select(Order)
        .join(Order.session)
        .where(DiningSession.table_id == table_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.selected_options),
            selectinload(Order.session).selectinload(DiningSession.table),
        )
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().unique())


@router.get(
    "/api/admin/orders",
    response_model=list[AdminOrderRead],
)
async def list_admin_orders(
    order_status: str | None = Query(default=None, alias="status"),
    table_id: int | None = None,
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
) -> list[Order]:
    query = (
        select(Order)
        .join(Order.session)
        .options(
            selectinload(Order.items).selectinload(OrderItem.selected_options),
            selectinload(Order.session).selectinload(DiningSession.table),
        )
        .order_by(Order.created_at.desc())
    )
    if order_status is not None:
        _validate_status(
            order_status,
            {"pending", "confirmed", "preparing", "ready", "served", "completed", "cancelled"},
        )
        query = query.where(Order.status == order_status)
    if table_id is not None:
        query = query.where(DiningSession.table_id == table_id)
    if active_only:
        query = query.where(DiningSession.status == "open")
    result = await session.execute(query)
    return list(result.scalars().unique())


@router.get(
    "/api/admin/orders/{order_id}",
    response_model=AdminOrderRead,
)
async def get_admin_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
) -> Order:
    return await _load_order(order_id, session)


@router.patch(
    "/api/admin/orders/{order_id}/status",
    response_model=AdminOrderRead,
)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    session: AsyncSession = Depends(get_db),
) -> Order:
    order = await _load_order(order_id, session)
    order.status = _validate_status(
        payload.status,
        {"pending", "confirmed", "preparing", "ready", "served", "completed", "cancelled"},
    )
    await session.commit()
    return await _load_order(order_id, session)


@router.patch(
    "/api/admin/orders/{order_id}/items/{item_id}/status",
    response_model=AdminOrderRead,
)
async def update_order_item_status(
    order_id: int,
    item_id: int,
    payload: OrderStatusUpdate,
    session: AsyncSession = Depends(get_db),
) -> Order:
    order = await _load_order(order_id, session)
    item = next((value for value in order.items if value.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Order item not found")
    item.status = _validate_status(
        payload.status,
        {"pending", "preparing", "ready", "completed", "cancelled"},
    )
    active_items = [value for value in order.items if value.status != "cancelled"]
    if active_items and all(value.status == "completed" for value in active_items):
        order.status = "completed"
    elif any(value.status == "preparing" for value in active_items):
        order.status = "preparing"
    elif active_items and all(value.status == "ready" for value in active_items):
        order.status = "ready"
    await session.commit()
    return await _load_order(order_id, session)


@router.get(
    "/api/tables/{table_id}/orders/{order_id}",
    response_model=OrderRead,
)
async def get_customer_order(
    table_id: int,
    order_id: int,
    session: AsyncSession = Depends(get_db),
) -> Order:
    return await _load_order_for_table(table_id, order_id, session)


@router.get(
    "/api/tables/{table_id}/current-orders",
    response_model=list[OrderRead],
)
async def list_current_table_orders(
    table_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[Order]:
    await _get_table(table_id, session)
    result = await session.execute(
        select(Order)
        .join(Order.session)
        .where(
            DiningSession.table_id == table_id,
            DiningSession.status == "open",
        )
        .options(
            selectinload(Order.items).selectinload(OrderItem.selected_options),
            selectinload(Order.session).selectinload(DiningSession.table),
        )
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().unique())
