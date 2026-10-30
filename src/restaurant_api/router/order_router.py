import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies.auth import require_admin, require_staff
from ..models.dining_session import DiningSession
from ..models.bill import Bill
from ..models.menu import Item, ItemOption, OptionGroup
from ..models.order import Order, OrderItem, OrderItemOption
from ..models.table import RestaurantTable
from ..schemas.order import (
    AdminOrderRead,
    DiningSessionRead,
    OrderCreate,
    OrderRead,
    OrdererClaimRead,
    OrderStatusUpdate,
    PublicTableRead,
)
from ..schemas.bill import BillRead


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


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _get_table_by_qr_token(
    qr_token: str,
    session: AsyncSession,
) -> RestaurantTable:
    table = await session.scalar(
        select(RestaurantTable).where(RestaurantTable.qr_code_token == qr_token)
    )
    if table is None or not table.is_active:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


async def _require_orderer(
    dining_session: DiningSession,
    orderer_token: str | None,
) -> None:
    if (
        orderer_token is None
        or dining_session.orderer_token_hash is None
        or not secrets.compare_digest(
            _token_hash(orderer_token), dining_session.orderer_token_hash
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the table's ordering guest can submit orders",
        )


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


def _bill_payload(
    bill: Bill,
    dining_session: DiningSession,
) -> dict:
    included_orders = [
        order for order in dining_session.orders if order.status != "cancelled"
    ]
    excluded_orders = [
        order for order in dining_session.orders if order.status == "cancelled"
    ]
    subtotal = sum(order.total_price_paisa for order in included_orders)
    bill.subtotal_paisa = subtotal
    bill.total_paisa = subtotal
    bill.included_order_count = len(included_orders)
    return {
        "id": bill.id,
        "dining_session_id": dining_session.id,
        "table_id": dining_session.table_id,
        "table_number": dining_session.table.table_number,
        "status": bill.status,
        "subtotal_paisa": bill.subtotal_paisa,
        "total_paisa": bill.total_paisa,
        "included_order_count": bill.included_order_count,
        "created_at": bill.created_at,
        "paid_at": bill.paid_at,
        "confirmed_at": bill.confirmed_at,
        "included_orders": included_orders,
        "excluded_cancelled_orders": excluded_orders,
    }


async def _load_bill(
    bill_id: int,
    session: AsyncSession,
    *,
    for_update: bool = False,
) -> tuple[Bill, DiningSession]:
    query = (
        select(Bill)
        .join(Bill.dining_session)
        .where(Bill.id == bill_id)
        .options(
            selectinload(Bill.dining_session).selectinload(DiningSession.table),
            selectinload(Bill.dining_session)
            .selectinload(DiningSession.orders)
            .selectinload(Order.items)
            .selectinload(OrderItem.selected_options),
        )
    )
    if for_update:
        query = query.with_for_update()
    bill = await session.scalar(query)
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill, bill.dining_session


async def _get_or_create_bill(
    dining_session: DiningSession,
    session: AsyncSession,
) -> Bill:
    bill = await session.scalar(
        select(Bill).where(Bill.dining_session_id == dining_session.id)
    )
    if bill is None:
        bill = Bill(dining_session=dining_session)
        session.add(bill)
        await session.flush()
    return bill


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


@router.get(
    "/api/public/tables/{qr_token}",
    response_model=PublicTableRead,
)
async def get_public_table(
    qr_token: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    table = await _get_table_by_qr_token(qr_token, session)
    dining_session = await _get_open_session(table.id, session)
    await session.commit()
    return {
        "table_id": table.id,
        "table_number": table.table_number,
        "session_id": dining_session.id,
        "session_status": dining_session.status,
    }


@router.post(
    "/api/public/tables/{qr_token}/claim-orderer",
    response_model=OrdererClaimRead,
)
async def claim_orderer(
    qr_token: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    table = await _get_table_by_qr_token(qr_token, session)
    dining_session = await _get_open_session(table.id, session)
    await session.flush()

    orderer_token = secrets.token_urlsafe(32)
    result = await session.execute(
        update(DiningSession)
        .where(
            DiningSession.id == dining_session.id,
            DiningSession.orderer_token_hash.is_(None),
        )
        .values(
            orderer_token_hash=_token_hash(orderer_token),
            orderer_claimed_at=datetime.now(timezone.utc),
        )
    )
    if result.rowcount != 1:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another guest is already allowed to order",
        )

    await session.commit()
    return {"orderer_token": orderer_token, "session_id": dining_session.id}


@router.post(
    "/api/tables/{table_id}/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    table_id: int,
    payload: OrderCreate,
    orderer_token: str | None = Header(default=None, alias="X-Orderer-Token"),
    session: AsyncSession = Depends(get_db),
) -> Order:
    await _get_table(table_id, session)
    dining_session = await _get_open_session(table_id, session)
    await _require_orderer(dining_session, orderer_token)

    item_ids = [entry.item_id for entry in payload.items]
    if len(set(item_ids)) != len(item_ids):
        raise HTTPException(
            status_code=400,
            detail="Each menu item may only appear once in an order",
        )

    result = await session.execute(
        select(Item)
        .options(
            selectinload(Item.item_options).selectinload(ItemOption.option),
            selectinload(Item.option_groups).selectinload(OptionGroup.options),
        )
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
        selected_group_ids = {
            item_option.option.group_id
            for item_option in selected_options
        }
        missing_groups = [
            group.name
            for group in item.option_groups
            if group.id not in selected_group_ids
        ]
        if missing_groups:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Select one option from each option group for {item.name}: "
                    f"{', '.join(missing_groups)}"
                ),
            )
        selected_options_by_group: dict[int, int] = {}
        for item_option in selected_options:
            group_id = item_option.option.group_id
            if group_id in selected_options_by_group:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Only one option may be selected from the "
                        f"{next(group.name for group in item.option_groups if group.id == group_id)} "
                        f"group for {item.name}"
                    ),
                )
            selected_options_by_group[group_id] = item_option.option_id

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
    await _get_or_create_bill(dining_session, session)
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


@router.post(
    "/api/admin/tables/{table_id}/sessions/close",
    response_model=DiningSessionRead,
    dependencies=[Depends(require_admin)],
)
async def close_current_session(
    table_id: int,
    session: AsyncSession = Depends(get_db),
) -> DiningSession:
    await _get_table(table_id, session)
    result = await session.scalars(
        select(DiningSession)
        .where(
            DiningSession.table_id == table_id,
            DiningSession.status == "open",
        )
        .order_by(DiningSession.id.desc())
    )
    dining_session = result.first()
    if dining_session is None:
        raise HTTPException(status_code=404, detail="No open dining session")

    dining_session.status = "closed"
    dining_session.closed_at = datetime.now(timezone.utc)
    await session.commit()
    return dining_session


@router.get(
    "/api/admin/tables/{table_id}/bill",
    response_model=BillRead,
    dependencies=[Depends(require_admin)],
)
async def get_current_bill(
    table_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict:
    await _get_table(table_id, session)
    dining_session = await session.scalar(
        select(DiningSession)
        .where(
            DiningSession.table_id == table_id,
            DiningSession.status == "open",
        )
        .options(
            selectinload(DiningSession.table),
            selectinload(DiningSession.orders)
            .selectinload(Order.items)
            .selectinload(OrderItem.selected_options),
        )
        .order_by(DiningSession.id.desc())
    )
    if dining_session is None:
        raise HTTPException(status_code=404, detail="No open dining session")
    if not dining_session.orders:
        raise HTTPException(status_code=404, detail="No orders for this dining session")
    bill = await session.scalar(
        select(Bill).where(Bill.dining_session_id == dining_session.id)
    )
    if bill is None:
        raise HTTPException(status_code=404, detail="No bill for this dining session")
    payload = _bill_payload(bill, dining_session)
    await session.commit()
    return payload


@router.get(
    "/api/admin/bills",
    response_model=list[BillRead],
    dependencies=[Depends(require_admin)],
)
async def list_admin_bills(
    bill_status: str | None = Query(default=None, alias="status"),
    table_id: int | None = None,
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    if bill_status is not None:
        _validate_status(bill_status, {"open", "paid", "confirmed"})
    query = (
        select(Bill)
        .join(Bill.dining_session)
        .join(DiningSession.orders)
        .options(
            selectinload(Bill.dining_session).selectinload(DiningSession.table),
            selectinload(Bill.dining_session)
            .selectinload(DiningSession.orders)
            .selectinload(Order.items)
            .selectinload(OrderItem.selected_options),
        )
        .order_by(Bill.created_at.desc())
    )
    if bill_status is not None:
        query = query.where(Bill.status == bill_status)
    if table_id is not None:
        query = query.where(DiningSession.table_id == table_id)
    bills = list((await session.scalars(query)).unique())
    payloads = [_bill_payload(bill, bill.dining_session) for bill in bills]
    await session.commit()
    return payloads


@router.get(
    "/api/admin/bills/{bill_id}",
    response_model=BillRead,
    dependencies=[Depends(require_admin)],
)
async def get_admin_bill(
    bill_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict:
    bill, dining_session = await _load_bill(bill_id, session)
    return _bill_payload(bill, dining_session)


@router.post(
    "/api/admin/bills/{bill_id}/confirm-payment",
    response_model=BillRead,
    dependencies=[Depends(require_admin)],
)
async def confirm_bill_payment(
    bill_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict:
    bill, dining_session = await _load_bill(bill_id, session, for_update=True)
    if bill.status == "confirmed":
        raise HTTPException(status_code=409, detail="Bill payment is already confirmed")
    if dining_session.status != "open":
        raise HTTPException(status_code=409, detail="Dining session is already closed")

    now = datetime.now(timezone.utc)
    bill.status = "confirmed"
    bill.paid_at = now
    bill.confirmed_at = now
    dining_session.status = "closed"
    dining_session.closed_at = now
    for order in dining_session.orders:
        if order.status != "cancelled":
            order.status = "completed"

    payload = _bill_payload(bill, dining_session)
    await session.commit()
    return payload


@router.get(
    "/api/public/tables/{qr_token}/orders",
    response_model=list[OrderRead],
)
async def list_public_table_orders(
    qr_token: str,
    session: AsyncSession = Depends(get_db),
) -> list[Order]:
    table = await _get_table_by_qr_token(qr_token, session)
    dining_session = await _get_open_session(table.id, session)
    await session.commit()
    result = await session.execute(
        select(Order)
        .where(Order.session_id == dining_session.id)
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
    dependencies=[Depends(require_staff)],
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
    dependencies=[Depends(require_staff)],
)
async def get_admin_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
) -> Order:
    return await _load_order(order_id, session)


@router.patch(
    "/api/admin/orders/{order_id}/status",
    response_model=AdminOrderRead,
    dependencies=[Depends(require_staff)],
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
    dependencies=[Depends(require_staff)],
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
