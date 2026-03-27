"""
Sale Scraper Runner
Checks shops for sales via Instagram and website scraping
"""

import asyncio
import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime

from instagram import InstagramScraper, DetectedSale
from website import WebsiteScraper, WebsiteSale


async def scrape_shop_sales(
    shop_id: str,
    instagram_handle: Optional[str] = None,
    website_url: Optional[str] = None,
) -> List[Dict]:
    """
    Scrape a single shop for sales.
    Returns list of sale dicts ready for database insertion.
    """

    sales = []

    # Initialize scrapers
    instagram_scraper = InstagramScraper()
    website_scraper = WebsiteScraper()

    try:
        # Scrape Instagram
        if instagram_handle:
            print(f"  Checking Instagram @{instagram_handle}...")
            ig_sales = await instagram_scraper.scrape_shop(instagram_handle)

            for sale in ig_sales:
                sales.append({
                    "id": str(uuid.uuid4()),
                    "shop_id": shop_id,
                    "title": sale.title,
                    "description": sale.description,
                    "discount_percent": sale.discount_percent,
                    "start_date": sale.start_date,
                    "end_date": sale.end_date,
                    "source": "instagram",
                    "source_url": sale.source_url,
                    "source_post_id": sale.source_post_id,
                    "raw_text": sale.raw_text,
                    "confidence_score": sale.confidence,
                    "is_active": True,
                    "detected_at": datetime.utcnow(),
                })

            await asyncio.sleep(1)  # Rate limiting

        # Scrape website
        if website_url:
            print(f"  Checking website {website_url}...")
            web_sales = await website_scraper.check_website(website_url)

            for sale in web_sales:
                sales.append({
                    "id": str(uuid.uuid4()),
                    "shop_id": shop_id,
                    "title": sale.title,
                    "description": sale.description,
                    "discount_percent": sale.discount_percent,
                    "source": "website",
                    "source_url": sale.url,
                    "raw_text": sale.raw_text,
                    "confidence_score": sale.confidence,
                    "is_active": True,
                    "detected_at": datetime.utcnow(),
                })

    finally:
        await instagram_scraper.close()
        await website_scraper.close()

    return sales


async def scrape_all_shops(shops: List[Dict]) -> List[Dict]:
    """
    Scrape multiple shops for sales.

    Args:
        shops: List of shop dicts with 'id', 'instagram', and 'website' fields

    Returns:
        List of all detected sales
    """

    all_sales = []

    for shop in shops:
        print(f"Scraping {shop.get('name', shop['id'])}...")

        shop_sales = await scrape_shop_sales(
            shop_id=shop["id"],
            instagram_handle=shop.get("instagram"),
            website_url=shop.get("website"),
        )

        if shop_sales:
            print(f"  Found {len(shop_sales)} potential sales")
            all_sales.extend(shop_sales)
        else:
            print(f"  No sales detected")

        # Rate limiting between shops
        await asyncio.sleep(2)

    return all_sales


async def mark_expired_sales(
    current_sales: List[Dict],
    existing_sales: List[Dict],
) -> List[str]:
    """
    Determine which existing sales should be marked as expired.
    Returns list of sale IDs to mark as inactive.
    """

    # Get current source URLs
    current_urls = {s.get("source_url") for s in current_sales}
    current_post_ids = {s.get("source_post_id") for s in current_sales if s.get("source_post_id")}

    expired_ids = []

    for existing in existing_sales:
        if not existing.get("is_active"):
            continue

        # Check if this sale is still being detected
        source_url = existing.get("source_url")
        post_id = existing.get("source_post_id")

        # If the source post/page is no longer showing a sale, mark as expired
        if post_id and post_id not in current_post_ids:
            expired_ids.append(existing["id"])
        elif source_url and source_url not in current_urls:
            expired_ids.append(existing["id"])

    return expired_ids


# Example shops for testing
SAMPLE_SHOPS = [
    {
        "id": "sample-1",
        "name": "L Train Vintage",
        "instagram": "ltrainvintage",
        "website": "https://ltrainvintage.com",
    },
    {
        "id": "sample-2",
        "name": "Beacon's Closet",
        "instagram": "beaconscloset",
        "website": "https://beaconscloset.com",
    },
    {
        "id": "sample-3",
        "name": "Stella Dallas Living",
        "instagram": "stelladallasliving",
        "website": None,
    },
]


async def run_test_scrape():
    """Run a test scrape on sample shops"""

    print("Starting test scrape...")
    print("=" * 50)

    sales = await scrape_all_shops(SAMPLE_SHOPS)

    print("\n" + "=" * 50)
    print(f"Total sales detected: {len(sales)}")

    for sale in sales:
        print(f"\n{sale['title']}")
        print(f"  Shop: {sale['shop_id']}")
        print(f"  Source: {sale['source']}")
        print(f"  Confidence: {sale['confidence_score']:.2f}")
        if sale.get('discount_percent'):
            print(f"  Discount: {sale['discount_percent']}%")

    return sales


if __name__ == "__main__":
    asyncio.run(run_test_scrape())
