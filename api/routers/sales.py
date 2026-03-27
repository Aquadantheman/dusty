"""
Sales API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from models import Sale, Shop


router = APIRouter()


class SaleWithShopResponse(BaseModel):
    id: str
    shop_id: str
    shop_name: str
    shop_neighborhood: str
    title: str
    description: Optional[str] = None
    discount_percent: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: str
    source_url: Optional[str] = None
    detected_at: datetime
    is_active: bool


class SalesResponse(BaseModel):
    sales: List[SaleWithShopResponse]
    total: int


@router.get("/sales", response_model=SalesResponse)
async def get_sales(
    shop_id: Optional[str] = Query(None),
    active_only: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get sales with optional filters"""

    query = select(Sale).join(Shop)

    if shop_id:
        query = query.where(Sale.shop_id == shop_id)

    if active_only:
        query = query.where(Sale.is_active == True)

    if source:
        query = query.where(Sale.source == source)

    # Order by most recent
    query = query.order_by(Sale.detected_at.desc())

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    sales = result.scalars().all()

    return SalesResponse(
        sales=[
            SaleWithShopResponse(
                id=sale.id,
                shop_id=sale.shop_id,
                shop_name=sale.shop.name,
                shop_neighborhood=sale.shop.neighborhood,
                title=sale.title,
                description=sale.description,
                discount_percent=sale.discount_percent,
                start_date=sale.start_date,
                end_date=sale.end_date,
                source=sale.source.value,
                source_url=sale.source_url,
                detected_at=sale.detected_at,
                is_active=sale.is_active,
            )
            for sale in sales
        ],
        total=total,
    )


@router.get("/sales/active")
async def get_active_sales(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all currently active sales"""

    query = (
        select(Sale)
        .join(Shop)
        .where(Sale.is_active == True)
        .order_by(Sale.detected_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    sales = result.scalars().all()

    return [
        {
            "id": sale.id,
            "shop_id": sale.shop_id,
            "shop_name": sale.shop.name,
            "shop_neighborhood": sale.shop.neighborhood,
            "title": sale.title,
            "discount_percent": sale.discount_percent,
            "end_date": sale.end_date,
            "source": sale.source.value,
        }
        for sale in sales
    ]


@router.get("/sales/{sale_id}")
async def get_sale(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single sale by ID"""

    result = await db.execute(
        select(Sale).where(Sale.id == sale_id).join(Shop)
    )
    sale = result.scalar_one_or_none()

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    return {
        "id": sale.id,
        "shop_id": sale.shop_id,
        "shop_name": sale.shop.name,
        "shop_neighborhood": sale.shop.neighborhood,
        "shop_address": sale.shop.address,
        "title": sale.title,
        "description": sale.description,
        "discount_percent": sale.discount_percent,
        "start_date": sale.start_date,
        "end_date": sale.end_date,
        "source": sale.source.value,
        "source_url": sale.source_url,
        "detected_at": sale.detected_at,
        "is_active": sale.is_active,
        "raw_text": sale.raw_text,
    }
