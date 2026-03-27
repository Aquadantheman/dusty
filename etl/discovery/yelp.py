"""
Yelp Fusion API integration for shop discovery
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class YelpBusiness:
    """Standardized Yelp business result"""
    yelp_id: str
    name: str
    address: str
    lat: float
    lng: float
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    photos: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class YelpDiscovery:
    """Discover vintage/antique shops using Yelp Fusion API"""

    BASE_URL = "https://api.yelp.com/v3"

    # Yelp category aliases for vintage/antique shops
    CATEGORIES = [
        "vintage",
        "antiques",
        "thrift_stores",
        "usedvintageconsignment",
        "fleamarkets",
        "vinylrecords",
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def search(
        self,
        lat: float,
        lng: float,
        radius_meters: int = 5000,
        categories: Optional[List[str]] = None,
        term: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[YelpBusiness]:
        """Search for businesses near a location"""

        url = f"{self.BASE_URL}/businesses/search"
        params = {
            "latitude": lat,
            "longitude": lng,
            "radius": min(radius_meters, 40000),  # Yelp max is 40km
            "limit": min(limit, 50),  # Yelp max is 50
            "offset": offset,
            "sort_by": "best_match",
        }

        if categories:
            params["categories"] = ",".join(categories)

        if term:
            params["term"] = term

        response = await self.client.get(url, params=params)

        if response.status_code != 200:
            print(f"Yelp API error: {response.status_code}")
            return []

        data = response.json()
        return [self._parse_business(b) for b in data.get("businesses", [])]

    async def get_business_details(self, business_id: str) -> Optional[YelpBusiness]:
        """Get detailed information about a specific business"""

        url = f"{self.BASE_URL}/businesses/{business_id}"

        response = await self.client.get(url)

        if response.status_code != 200:
            return None

        return self._parse_business(response.json(), detailed=True)

    async def discover_all(
        self,
        center_lat: float,
        center_lng: float,
        radius_meters: int = 5000,
    ) -> List[YelpBusiness]:
        """Run all category searches and dedupe results"""

        all_results: Dict[str, YelpBusiness] = {}

        # Search each category
        tasks = [
            self.search(center_lat, center_lng, radius_meters, categories=[cat])
            for cat in self.CATEGORIES
        ]

        # Also do some text searches
        text_searches = [
            "vintage shop",
            "antique store",
            "thrift store",
            "consignment shop",
        ]
        tasks.extend([
            self.search(center_lat, center_lng, radius_meters, term=term)
            for term in text_searches
        ])

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        for results in results_lists:
            if isinstance(results, Exception):
                print(f"Yelp search error: {results}")
                continue

            for business in results:
                if business.yelp_id not in all_results:
                    all_results[business.yelp_id] = business

        return list(all_results.values())

    def _parse_business(self, data: dict, detailed: bool = False) -> YelpBusiness:
        """Parse a Yelp business response"""

        # Parse location
        location = data.get("location", {})
        coords = data.get("coordinates", {})

        address_parts = [
            location.get("address1", ""),
            location.get("city", ""),
            location.get("state", ""),
            location.get("zip_code", ""),
        ]
        address = ", ".join(p for p in address_parts if p)

        # Parse price level ($ = 1, $$ = 2, etc.)
        price_str = data.get("price", "")
        price_level = len(price_str) if price_str else None

        # Parse categories
        yelp_categories = data.get("categories", [])
        categories = self._map_categories(yelp_categories)

        # Photos
        photos = data.get("photos", [])
        if not photos and "image_url" in data:
            photos = [data["image_url"]]

        return YelpBusiness(
            yelp_id=data.get("id", ""),
            name=data.get("name", ""),
            address=address,
            lat=coords.get("latitude", 0),
            lng=coords.get("longitude", 0),
            rating=data.get("rating"),
            review_count=data.get("review_count"),
            price_level=price_level,
            phone=data.get("display_phone"),
            url=data.get("url"),
            photos=photos[:5] if photos else None,
            categories=categories,
        )

    def _map_categories(self, yelp_categories: List[dict]) -> List[str]:
        """Map Yelp categories to Dusty categories"""

        categories = []
        aliases = [c.get("alias", "") for c in yelp_categories]

        if any(a in ["vintage", "vinylrecords"] for a in aliases):
            categories.append("vintage")
        if "antiques" in aliases:
            categories.append("antique")
        if "thrift_stores" in aliases:
            categories.append("thrift")
        if "usedvintageconsignment" in aliases:
            categories.append("consignment")
        if any(a in ["womenscloth", "menscloth", "fashion"] for a in aliases):
            categories.append("clothing")
        if any(a in ["furniture", "homedecor"] for a in aliases):
            categories.append("furniture")
        if "vinylrecords" in aliases:
            categories.append("records")

        if not categories:
            categories.append("vintage")

        return categories

    async def close(self):
        await self.client.aclose()
