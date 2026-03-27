"""
Neighborhoods API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from core.database import get_db
from models import Shop


router = APIRouter()


@router.get("/neighborhoods", response_model=List[str])
async def get_neighborhoods(
    db: AsyncSession = Depends(get_db),
):
    """Get list of all neighborhoods with shops"""

    query = (
        select(Shop.neighborhood)
        .where(Shop.is_active == True)
        .where(Shop.neighborhood.isnot(None))
        .distinct()
        .order_by(Shop.neighborhood)
    )

    result = await db.execute(query)
    neighborhoods = result.scalars().all()

    return list(neighborhoods)


@router.get("/neighborhoods/stats")
async def get_neighborhood_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get shop counts by neighborhood"""

    query = (
        select(
            Shop.neighborhood,
            func.count(Shop.id).label("shop_count"),
            func.avg(Shop.rating).label("avg_rating"),
        )
        .where(Shop.is_active == True)
        .where(Shop.neighborhood.isnot(None))
        .group_by(Shop.neighborhood)
        .order_by(func.count(Shop.id).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "neighborhood": row.neighborhood,
            "shop_count": row.shop_count,
            "avg_rating": round(row.avg_rating, 2) if row.avg_rating else None,
        }
        for row in rows
    ]
