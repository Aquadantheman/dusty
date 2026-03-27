"""
Google Places API integration for shop discovery
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
import os


@dataclass
class PlaceResult:
    """Standardized place result"""
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    photos: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class GooglePlacesDiscovery:
    """Discover vintage/antique shops using Google Places API"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    # Search queries for different shop types
    SEARCH_QUERIES = [
        "vintage shop",
        "vintage store",
        "vintage clothing",
        "antique shop",
        "antique store",
        "thrift store",
        "consignment shop",
        "secondhand store",
        "resale shop",
        "vintage furniture",
        "record store vinyl",
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius_meters: int = 5000,
        query: str = "vintage shop",
    ) -> List[PlaceResult]:
        """Search for shops near a location"""

        url = f"{self.BASE_URL}/nearbysearch/json"
        params = {
            "key": self.api_key,
            "location": f"{lat},{lng}",
            "radius": radius_meters,
            "keyword": query,
            "type": "store",
        }

        response = await self.client.get(url, params=params)
        data = response.json()

        if data.get("status") != "OK":
            print(f"Google Places error: {data.get('status')}")
            return []

        results = []
        for place in data.get("results", []):
            results.append(self._parse_place(place))

        return results

    async def search_text(
        self,
        query: str,
        location: Optional[tuple] = None,
        radius_meters: int = 10000,
    ) -> List[PlaceResult]:
        """Text search for shops"""

        url = f"{self.BASE_URL}/textsearch/json"
        params = {
            "key": self.api_key,
            "query": query,
        }

        if location:
            params["location"] = f"{location[0]},{location[1]}"
            params["radius"] = radius_meters

        response = await self.client.get(url, params=params)
        data = response.json()

        if data.get("status") != "OK":
            return []

        return [self._parse_place(p) for p in data.get("results", [])]

    async def get_place_details(self, place_id: str) -> Optional[PlaceResult]:
        """Get detailed information about a specific place"""

        url = f"{self.BASE_URL}/details/json"
        params = {
            "key": self.api_key,
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,rating,user_ratings_total,"
                      "price_level,formatted_phone_number,website,opening_hours,photos,types",
        }

        response = await self.client.get(url, params=params)
        data = response.json()

        if data.get("status") != "OK":
            return None

        return self._parse_place_details(data.get("result", {}), place_id)

    async def discover_all(
        self,
        center_lat: float,
        center_lng: float,
        radius_meters: int = 5000,
    ) -> List[PlaceResult]:
        """Run all search queries and dedupe results"""

        all_results: Dict[str, PlaceResult] = {}

        # Run searches concurrently
        tasks = [
            self.search_nearby(center_lat, center_lng, radius_meters, query)
            for query in self.SEARCH_QUERIES
        ]

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        for results in results_lists:
            if isinstance(results, Exception):
                print(f"Search error: {results}")
                continue

            for place in results:
                if place.place_id not in all_results:
                    all_results[place.place_id] = place

        # Get details for each unique place
        detail_tasks = [
            self.get_place_details(place_id)
            for place_id in all_results.keys()
        ]

        detailed_results = await asyncio.gather(*detail_tasks, return_exceptions=True)

        final_results = []
        for result in detailed_results:
            if isinstance(result, PlaceResult):
                final_results.append(result)

        return final_results

    def _parse_place(self, data: dict) -> PlaceResult:
        """Parse a place from search results"""

        location = data.get("geometry", {}).get("location", {})

        return PlaceResult(
            place_id=data.get("place_id", ""),
            name=data.get("name", ""),
            address=data.get("formatted_address", data.get("vicinity", "")),
            lat=location.get("lat", 0),
            lng=location.get("lng", 0),
            rating=data.get("rating"),
            review_count=data.get("user_ratings_total"),
            price_level=data.get("price_level"),
        )

    def _parse_place_details(self, data: dict, place_id: str) -> PlaceResult:
        """Parse detailed place info"""

        location = data.get("geometry", {}).get("location", {})

        # Parse opening hours
        hours = None
        if "opening_hours" in data:
            weekday_text = data["opening_hours"].get("weekday_text", [])
            hours = {}
            day_map = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, text in enumerate(weekday_text):
                if i < len(day_map):
                    # Remove day name prefix
                    time_part = text.split(": ", 1)[-1] if ": " in text else text
                    hours[day_map[i]] = time_part

        # Parse photos
        photos = None
        if "photos" in data:
            photos = [
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=800&photo_reference={p['photo_reference']}&key={self.api_key}"
                for p in data["photos"][:5]
            ]

        # Infer categories from types
        categories = self._infer_categories(data.get("types", []), data.get("name", ""))

        return PlaceResult(
            place_id=place_id,
            name=data.get("name", ""),
            address=data.get("formatted_address", ""),
            lat=location.get("lat", 0),
            lng=location.get("lng", 0),
            rating=data.get("rating"),
            review_count=data.get("user_ratings_total"),
            price_level=data.get("price_level"),
            phone=data.get("formatted_phone_number"),
            website=data.get("website"),
            hours=hours,
            photos=photos,
            categories=categories,
        )

    def _infer_categories(self, types: List[str], name: str) -> List[str]:
        """Infer shop categories from Google types and name"""

        categories = []
        name_lower = name.lower()

        # Check name for category hints
        if any(w in name_lower for w in ["vintage", "retro"]):
            categories.append("vintage")
        if any(w in name_lower for w in ["antique", "antiquarian"]):
            categories.append("antique")
        if any(w in name_lower for w in ["thrift", "goodwill", "salvation army"]):
            categories.append("thrift")
        if any(w in name_lower for w in ["consignment", "resale"]):
            categories.append("consignment")
        if any(w in name_lower for w in ["clothing", "fashion", "apparel", "wear"]):
            categories.append("clothing")
        if any(w in name_lower for w in ["furniture", "decor", "home"]):
            categories.append("furniture")
        if any(w in name_lower for w in ["record", "vinyl", "music"]):
            categories.append("records")

        # Default to vintage if no specific category found
        if not categories:
            categories.append("vintage")

        return categories

    async def close(self):
        await self.client.aclose()
