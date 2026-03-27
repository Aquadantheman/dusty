"""
Shop Discovery Pipeline Runner
Aggregates data from Google Places, Yelp, and OpenStreetMap
"""

import asyncio
import os
import uuid
from typing import List, Dict
from datetime import datetime

from google_places import GooglePlacesDiscovery
from yelp import YelpDiscovery
from osm import OSMDiscovery


# NYC neighborhoods with their approximate centers
NYC_NEIGHBORHOODS = {
    "Lower East Side": (40.7150, -73.9843),
    "East Village": (40.7265, -73.9817),
    "West Village": (40.7336, -74.0027),
    "SoHo": (40.7233, -73.9961),
    "NoLita": (40.7234, -73.9954),
    "Williamsburg": (40.7081, -73.9571),
    "Greenpoint": (40.7282, -73.9512),
    "Bushwick": (40.6944, -73.9213),
    "Park Slope": (40.6710, -73.9814),
    "DUMBO": (40.7033, -73.9881),
    "Chelsea": (40.7465, -74.0014),
    "Hell's Kitchen": (40.7638, -73.9918),
    "Upper West Side": (40.7870, -73.9754),
    "Harlem": (40.8116, -73.9465),
    "Astoria": (40.7720, -73.9301),
    "Long Island City": (40.7447, -73.9485),
}


async def discover_shops(
    lat: float,
    lng: float,
    radius_meters: int = 3000,
    google_api_key: str = None,
    yelp_api_key: str = None,
) -> List[Dict]:
    """
    Discover shops from all sources and merge results.
    Returns a list of shop dictionaries ready for database insertion.
    """

    all_shops: Dict[str, Dict] = {}

    # Initialize clients
    google_client = GooglePlacesDiscovery(google_api_key) if google_api_key else None
    yelp_client = YelpDiscovery(yelp_api_key) if yelp_api_key else None
    osm_client = OSMDiscovery()

    try:
        # Run all discovery in parallel
        tasks = []

        if google_client:
            tasks.append(google_client.discover_all(lat, lng, radius_meters))
        if yelp_client:
            tasks.append(yelp_client.discover_all(lat, lng, radius_meters))

        # OSM uses bounding box
        # Approximate bounding box from center and radius
        lat_delta = radius_meters / 111000  # ~111km per degree latitude
        lng_delta = radius_meters / (111000 * abs(cos(radians(lat))))
        tasks.append(osm_client.search_area(
            lat - lat_delta, lng - lng_delta,
            lat + lat_delta, lng + lng_delta,
        ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process Google Places results
        if google_client and not isinstance(results[0], Exception):
            for place in results[0]:
                key = _normalize_key(place.name, place.lat, place.lng)
                if key not in all_shops:
                    all_shops[key] = _place_to_shop(place)
                else:
                    # Merge Google data
                    _merge_google_data(all_shops[key], place)

        # Process Yelp results
        yelp_idx = 1 if google_client else 0
        if yelp_client and not isinstance(results[yelp_idx], Exception):
            for business in results[yelp_idx]:
                key = _normalize_key(business.name, business.lat, business.lng)
                if key not in all_shops:
                    all_shops[key] = _yelp_to_shop(business)
                else:
                    _merge_yelp_data(all_shops[key], business)

        # Process OSM results
        osm_idx = len([c for c in [google_client, yelp_client] if c])
        if not isinstance(results[osm_idx], Exception):
            for place in results[osm_idx]:
                key = _normalize_key(place.name, place.lat, place.lng)
                if key not in all_shops:
                    all_shops[key] = _osm_to_shop(place)
                else:
                    _merge_osm_data(all_shops[key], place)

    finally:
        # Cleanup
        if google_client:
            await google_client.close()
        if yelp_client:
            await yelp_client.close()
        await osm_client.close()

    return list(all_shops.values())


def _normalize_key(name: str, lat: float, lng: float) -> str:
    """Create a normalized key for deduplication"""
    # Normalize name (lowercase, remove special chars)
    normalized_name = "".join(c.lower() for c in name if c.isalnum())
    # Round coordinates to ~100m precision
    lat_rounded = round(lat, 3)
    lng_rounded = round(lng, 3)
    return f"{normalized_name}_{lat_rounded}_{lng_rounded}"


def _place_to_shop(place) -> Dict:
    """Convert Google Place to shop dict"""
    return {
        "id": str(uuid.uuid4()),
        "name": place.name,
        "address": place.address,
        "lat": place.lat,
        "lng": place.lng,
        "categories": place.categories or ["vintage"],
        "rating": place.rating,
        "review_count": place.review_count,
        "price_level": place.price_level,
        "phone": place.phone,
        "website": place.website,
        "hours": place.hours,
        "photos": place.photos,
        "google_place_id": place.place_id,
        "created_at": datetime.utcnow(),
    }


def _yelp_to_shop(business) -> Dict:
    """Convert Yelp business to shop dict"""
    return {
        "id": str(uuid.uuid4()),
        "name": business.name,
        "address": business.address,
        "lat": business.lat,
        "lng": business.lng,
        "categories": business.categories or ["vintage"],
        "rating": business.rating,
        "review_count": business.review_count,
        "price_level": business.price_level,
        "phone": business.phone,
        "website": business.url,
        "photos": business.photos,
        "yelp_id": business.yelp_id,
        "created_at": datetime.utcnow(),
    }


def _osm_to_shop(place) -> Dict:
    """Convert OSM place to shop dict"""
    return {
        "id": str(uuid.uuid4()),
        "name": place.name,
        "address": place.address,
        "lat": place.lat,
        "lng": place.lng,
        "categories": place.categories or ["vintage"],
        "phone": place.phone,
        "website": place.website,
        "osm_id": f"{place.osm_type}/{place.osm_id}",
        "created_at": datetime.utcnow(),
    }


def _merge_google_data(shop: Dict, place) -> None:
    """Merge Google data into existing shop"""
    shop["google_place_id"] = place.place_id
    if not shop.get("phone") and place.phone:
        shop["phone"] = place.phone
    if not shop.get("website") and place.website:
        shop["website"] = place.website
    if not shop.get("hours") and place.hours:
        shop["hours"] = place.hours
    if not shop.get("photos") and place.photos:
        shop["photos"] = place.photos
    if place.rating and (not shop.get("rating") or place.review_count > (shop.get("review_count") or 0)):
        shop["rating"] = place.rating
        shop["review_count"] = place.review_count


def _merge_yelp_data(shop: Dict, business) -> None:
    """Merge Yelp data into existing shop"""
    shop["yelp_id"] = business.yelp_id
    if not shop.get("phone") and business.phone:
        shop["phone"] = business.phone
    if not shop.get("photos") and business.photos:
        shop["photos"] = business.photos


def _merge_osm_data(shop: Dict, place) -> None:
    """Merge OSM data into existing shop"""
    shop["osm_id"] = f"{place.osm_type}/{place.osm_id}"
    if not shop.get("phone") and place.phone:
        shop["phone"] = place.phone
    if not shop.get("website") and place.website:
        shop["website"] = place.website


from math import cos, radians


async def run_full_discovery():
    """Run discovery for all NYC neighborhoods"""

    google_key = os.getenv("GOOGLE_PLACES_API_KEY")
    yelp_key = os.getenv("YELP_API_KEY")

    all_shops = []

    for neighborhood, (lat, lng) in NYC_NEIGHBORHOODS.items():
        print(f"Discovering shops in {neighborhood}...")
        shops = await discover_shops(
            lat, lng,
            radius_meters=2000,
            google_api_key=google_key,
            yelp_api_key=yelp_key,
        )

        # Add neighborhood to each shop
        for shop in shops:
            shop["neighborhood"] = neighborhood
            shop["city"] = "NYC"

        all_shops.extend(shops)
        print(f"  Found {len(shops)} shops")

        # Rate limiting
        await asyncio.sleep(1)

    print(f"\nTotal shops discovered: {len(all_shops)}")
    return all_shops


if __name__ == "__main__":
    asyncio.run(run_full_discovery())
