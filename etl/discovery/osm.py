"""
OpenStreetMap Overpass API integration for shop discovery
"""

import httpx
import asyncio
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class OSMPlace:
    """Standardized OSM place result"""
    osm_id: str
    osm_type: str  # node, way, relation
    name: str
    address: str
    lat: float
    lng: float
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    categories: Optional[List[str]] = None


class OSMDiscovery:
    """Discover vintage/antique shops using OpenStreetMap Overpass API"""

    # Multiple Overpass API endpoints for load balancing
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=90.0)
        self.current_endpoint = 0
        self.request_count = 0

    def _get_endpoint(self) -> str:
        """Rotate through endpoints to avoid rate limits"""
        endpoint = self.OVERPASS_ENDPOINTS[self.current_endpoint]
        self.current_endpoint = (self.current_endpoint + 1) % len(self.OVERPASS_ENDPOINTS)
        return endpoint

    async def _request_with_retry(self, query: str, max_retries: int = 3) -> dict:
        """Make request with retry logic and endpoint rotation"""
        import asyncio

        for attempt in range(max_retries):
            endpoint = self._get_endpoint()
            self.request_count += 1

            # Add delay between requests (longer after more requests)
            delay = min(2 + (self.request_count * 0.5), 10)
            await asyncio.sleep(delay)

            try:
                response = await self.client.post(
                    endpoint,
                    data={"data": query},
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print(f"  Rate limited on {endpoint}, trying another...")
                    await asyncio.sleep(5)  # Extra delay on rate limit
                    continue
                elif response.status_code == 504:
                    print(f"  Timeout on {endpoint}, retrying...")
                    continue
                else:
                    print(f"  Error {response.status_code} on {endpoint}")
                    continue

            except Exception as e:
                print(f"  Request error: {e}")
                await asyncio.sleep(2)
                continue

        return {"elements": []}  # Return empty on all failures

    async def search_area(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> List[OSMPlace]:
        """
        Search for vintage/antique shops in a bounding box.
        Bounding box: (south, west, north, east)
        """

        # Build Overpass QL query
        bbox = f"{south},{west},{north},{east}"

        query = f"""
        [out:json][timeout:60];
        (
          // Antique shops
          node["shop"="antiques"]({bbox});
          way["shop"="antiques"]({bbox});

          // Second hand / charity shops
          node["shop"="second_hand"]({bbox});
          way["shop"="second_hand"]({bbox});
          node["shop"="charity"]({bbox});
          way["shop"="charity"]({bbox});

          // Vintage in name
          node["name"~"[Vv]intage"]({bbox});
          way["name"~"[Vv]intage"]({bbox});

          // Thrift in name
          node["name"~"[Tt]hrift"]({bbox});
          way["name"~"[Tt]hrift"]({bbox});

          // Consignment
          node["name"~"[Cc]onsignment"]({bbox});
          way["name"~"[Cc]onsignment"]({bbox});

          // Record shops
          node["shop"="music"]["second_hand"="yes"]({bbox});
          way["shop"="music"]["second_hand"="yes"]({bbox});
        );
        out center;
        """

        data = await self._request_with_retry(query)
        return [self._parse_element(e) for e in data.get("elements", [])]

    async def search_around_point(
        self,
        lat: float,
        lng: float,
        radius_meters: int = 5000,
    ) -> List[OSMPlace]:
        """Search for shops around a point"""

        query = f"""
        [out:json][timeout:60];
        (
          node["shop"="antiques"](around:{radius_meters},{lat},{lng});
          node["shop"="second_hand"](around:{radius_meters},{lat},{lng});
          node["shop"="charity"](around:{radius_meters},{lat},{lng});
          node["name"~"[Vv]intage"](around:{radius_meters},{lat},{lng});
          node["name"~"[Tt]hrift"](around:{radius_meters},{lat},{lng});
        );
        out;
        """

        data = await self._request_with_retry(query)
        return [self._parse_element(e) for e in data.get("elements", [])]

    def _parse_element(self, element: dict) -> OSMPlace:
        """Parse an OSM element into a standardized place"""

        tags = element.get("tags", {})

        # Get coordinates (different for nodes vs ways)
        if element["type"] == "node":
            lat = element.get("lat", 0)
            lng = element.get("lon", 0)
        else:
            # For ways/relations, use center point
            center = element.get("center", {})
            lat = center.get("lat", 0)
            lng = center.get("lon", 0)

        # Build address from tags
        address_parts = []
        if tags.get("addr:housenumber"):
            address_parts.append(tags["addr:housenumber"])
        if tags.get("addr:street"):
            address_parts.append(tags["addr:street"])
        if tags.get("addr:city"):
            address_parts.append(tags["addr:city"])
        if tags.get("addr:postcode"):
            address_parts.append(tags["addr:postcode"])

        address = " ".join(address_parts) if address_parts else ""

        # Infer categories
        categories = self._infer_categories(tags)

        return OSMPlace(
            osm_id=str(element.get("id", "")),
            osm_type=element.get("type", "node"),
            name=tags.get("name", "Unknown"),
            address=address,
            lat=lat,
            lng=lng,
            phone=tags.get("phone") or tags.get("contact:phone"),
            website=tags.get("website") or tags.get("contact:website"),
            hours=tags.get("opening_hours"),
            categories=categories,
        )

    def _infer_categories(self, tags: dict) -> List[str]:
        """Infer Dusty categories from OSM tags"""

        categories = []
        shop_type = tags.get("shop", "")
        name = tags.get("name", "").lower()

        if shop_type == "antiques" or "antique" in name:
            categories.append("antique")

        if shop_type == "second_hand" or "vintage" in name:
            categories.append("vintage")

        if shop_type == "charity" or "thrift" in name or "goodwill" in name:
            categories.append("thrift")

        if "consignment" in name:
            categories.append("consignment")

        if "clothing" in name or "fashion" in name or tags.get("clothes"):
            categories.append("clothing")

        if "furniture" in name or tags.get("furniture"):
            categories.append("furniture")

        if "record" in name or "vinyl" in name or shop_type == "music":
            categories.append("records")

        if not categories:
            categories.append("vintage")

        return categories

    async def close(self):
        await self.client.aclose()
