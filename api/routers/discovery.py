"""
Shop discovery API endpoints - triggers data collection pipelines
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from core.database import get_db


router = APIRouter()


class DiscoveryRequest(BaseModel):
    """Request to discover shops in an area"""
    neighborhood: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_meters: int = 2000
    sources: List[str] = ["google", "yelp", "osm"]


class ScrapeRequest(BaseModel):
    """Request to scrape sales for shops"""
    shop_ids: Optional[List[str]] = None  # If None, scrape all
    sources: List[str] = ["instagram", "website"]


@router.post("/discovery/shops")
async def discover_shops(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger shop discovery pipeline.
    Searches Google Places, Yelp, and OSM for vintage/antique shops.
    """
    # This would trigger the ETL discovery pipeline
    # For now, return a placeholder response

    return {
        "status": "queued",
        "message": "Shop discovery job queued",
        "config": {
            "neighborhood": request.neighborhood,
            "location": [request.lat, request.lng] if request.lat else None,
            "radius": request.radius_meters,
            "sources": request.sources,
        },
    }


@router.post("/discovery/sales")
async def scrape_sales(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger sale scraping pipeline.
    Checks Instagram, websites, etc. for sale announcements.
    """
    # This would trigger the ETL scraping pipeline
    # For now, return a placeholder response

    return {
        "status": "queued",
        "message": "Sale scraping job queued",
        "config": {
            "shop_ids": request.shop_ids or "all",
            "sources": request.sources,
        },
    }


@router.get("/discovery/status")
async def get_discovery_status():
    """Get status of running discovery/scraping jobs"""

    # This would check the job queue status
    return {
        "discovery": {
            "status": "idle",
            "last_run": None,
            "shops_found": 0,
        },
        "scraping": {
            "status": "idle",
            "last_run": None,
            "sales_found": 0,
        },
    }
