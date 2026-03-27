"""
Shop API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from models import Shop, Sale


router = APIRouter()


# Response schemas
class SaleResponse(BaseModel):
    id: str
    shop_id: str
    title: str
    description: Optional[str] = None
    discount_percent: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: str
    source_url: Optional[str] = None
    detected_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ShopResponse(BaseModel):
    id: str
    name: str
    address: str
    neighborhood: str
    lat: float
    lng: float
    categories: List[str]
    description: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    hours: Optional[dict] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    photos: Optional[List[str]] = None
    active_sale: Optional[SaleResponse] = None
    recent_sales: Optional[List[SaleResponse]] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class ShopsResponse(BaseModel):
    shops: List[ShopResponse]
    total: int
    has_more: bool


@router.get("/shops", response_model=ShopsResponse)
async def get_shops(
    categories: Optional[str] = Query(None, description="Comma-separated category IDs"),
    has_sale: Optional[bool] = Query(None, description="Filter to shops with active sales"),
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get list of shops with optional filters"""

    query = select(Shop).where(Shop.is_active == True)

    # Category filter
    if categories:
        cat_list = categories.split(",")
        # Filter shops that have any of the specified categories
        query = query.where(
            or_(*[Shop.categories.contains([cat]) for cat in cat_list])
        )

    # Neighborhood filter
    if neighborhood:
        query = query.where(Shop.neighborhood == neighborhood)

    # Rating filter
    if min_rating is not None:
        query = query.where(Shop.rating >= min_rating)

    # Search filter
    if q:
        search_term = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Shop.name).like(search_term),
                func.lower(Shop.address).like(search_term),
                func.lower(Shop.neighborhood).like(search_term),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    shops = result.scalars().all()

    # Filter by active sale if requested
    if has_sale:
        shops = [s for s in shops if s.has_active_sale]

    # Build response
    shop_responses = []
    for shop in shops:
        active_sale = None
        recent_sales = []

        if shop.sales:
            active_sales = [s for s in shop.sales if s.is_active]
            if active_sales:
                active_sale = SaleResponse.model_validate(active_sales[0])

            recent_sales = [
                SaleResponse.model_validate(s)
                for s in sorted(shop.sales, key=lambda x: x.detected_at, reverse=True)[:5]
            ]

        shop_responses.append(
            ShopResponse(
                id=shop.id,
                name=shop.name,
                address=shop.address,
                neighborhood=shop.neighborhood,
                lat=shop.lat,
                lng=shop.lng,
                categories=shop.categories or [],
                description=shop.description,
                phone=shop.phone,
                website=shop.website,
                instagram=shop.instagram,
                hours=shop.hours,
                rating=shop.rating,
                review_count=shop.review_count,
                price_level=shop.price_level,
                photos=shop.photos or [],
                active_sale=active_sale,
                recent_sales=recent_sales,
                last_updated=shop.updated_at,
            )
        )

    return ShopsResponse(
        shops=shop_responses,
        total=total,
        has_more=(offset + limit) < total,
    )


@router.get("/shops/{shop_id}", response_model=ShopResponse)
async def get_shop(
    shop_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single shop by ID"""

    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    active_sale = None
    recent_sales = []

    if shop.sales:
        active_sales = [s for s in shop.sales if s.is_active]
        if active_sales:
            active_sale = SaleResponse.model_validate(active_sales[0])

        recent_sales = [
            SaleResponse.model_validate(s)
            for s in sorted(shop.sales, key=lambda x: x.detected_at, reverse=True)[:10]
        ]

    return ShopResponse(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        neighborhood=shop.neighborhood,
        lat=shop.lat,
        lng=shop.lng,
        categories=shop.categories or [],
        description=shop.description,
        phone=shop.phone,
        website=shop.website,
        instagram=shop.instagram,
        hours=shop.hours,
        rating=shop.rating,
        review_count=shop.review_count,
        price_level=shop.price_level,
        photos=shop.photos or [],
        active_sale=active_sale,
        recent_sales=recent_sales,
        last_updated=shop.updated_at,
    )


@router.get("/search")
async def search_shops(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Quick search for shops"""

    search_term = f"%{q.lower()}%"

    query = (
        select(Shop)
        .where(Shop.is_active == True)
        .where(
            or_(
                func.lower(Shop.name).like(search_term),
                func.lower(Shop.address).like(search_term),
                func.lower(Shop.neighborhood).like(search_term),
            )
        )
        .limit(limit)
    )

    result = await db.execute(query)
    shops = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "address": s.address,
            "neighborhood": s.neighborhood,
            "categories": s.categories,
        }
        for s in shops
    ]
