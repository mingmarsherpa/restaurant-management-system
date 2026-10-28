
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import FRONTEND_URL
from ..database import get_db
from ..models.table import RestaurantTable
from ..schemas.table import (
    RestaurantTableCreate,
    RestaurantTableRead,
    RestaurantTableUpdate,
)
from ..services.qr import generate_table_qr

router = APIRouter(
    prefix="/tables",
    tags=["Restaurant Tables"],
)


@router.get("/{table_id}/qr")
async def get_table_qr(
    table_id: int,
    db: AsyncSession = Depends(get_db),
):
    table = await db.get(RestaurantTable, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    image = generate_table_qr(f"{FRONTEND_URL}/order?table={table.qr_code_token}")
    return Response(content=image.getvalue(), media_type="image/png")


@router.post(
    "/",
    response_model=RestaurantTableRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_table(
    table_data: RestaurantTableCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(RestaurantTable).where(
            RestaurantTable.table_number == table_data.table_number
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table number already exists",
        )

    table = RestaurantTable(
        table_number=table_data.table_number,
        qr_code_token=secrets.token_urlsafe(32),
    )

    db.add(table)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create table due to a duplicate value",
        )

    await db.refresh(table)
    return table


@router.get(
    "/",
    response_model=list[RestaurantTableRead],
)
async def list_tables(
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(RestaurantTable).order_by(
            RestaurantTable.table_number
        )
    )
    return list(result)


@router.get(
    "/{table_id}",
    response_model=RestaurantTableRead,
)
async def get_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
):
    table = await db.get(RestaurantTable, table_id)

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    return table


@router.patch(
    "/{table_id}",
    response_model=RestaurantTableRead,
)
async def update_table(
    table_id: int,
    table_data: RestaurantTableUpdate,
    db: AsyncSession = Depends(get_db),
):
    table = await db.get(RestaurantTable, table_id)

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    updates = table_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is not None:
            setattr(table, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table number already exists",
        )

    await db.refresh(table)
    return table


@router.delete(
    "/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
):
    table = await db.get(RestaurantTable, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    try:
        await db.delete(table)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table cannot be deleted because it has dining history",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
