"""
Quick NYC discovery using OpenStreetMap only (no API keys needed)
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discovery.osm import OSMDiscovery


# NYC neighborhoods with bounding boxes (south, west, north, east)
NYC_AREAS = {
    # Manhattan
    "Lower East Side": (40.7130, -73.9920, 40.7240, -73.9750),
    "East Village": (40.7220, -73.9920, 40.7340, -73.9780),
    "West Village": (40.7280, -74.0100, 40.7400, -73.9950),
    "SoHo": (40.7180, -74.0050, 40.7280, -73.9920),
    "NoLita": (40.7200, -73.9980, 40.7260, -73.9900),
    "Tribeca": (40.7140, -74.0120, 40.7220, -74.0020),
    "Chelsea": (40.7380, -74.0100, 40.7550, -73.9900),
    "Flatiron": (40.7380, -73.9950, 40.7450, -73.9820),
    "Gramercy": (40.7330, -73.9900, 40.7420, -73.9780),
    "Upper West Side": (40.7750, -73.9900, 40.8000, -73.9650),
    "Upper East Side": (40.7630, -73.9700, 40.7850, -73.9500),
    "Harlem": (40.8000, -73.9600, 40.8200, -73.9350),
    "Chinatown": (40.7130, -74.0020, 40.7200, -73.9920),

    # Brooklyn
    "Williamsburg": (40.7000, -73.9700, 40.7200, -73.9400),
    "Greenpoint": (40.7200, -73.9650, 40.7380, -73.9400),
    "Bushwick": (40.6850, -73.9350, 40.7050, -73.9050),
    "Park Slope": (40.6600, -73.9900, 40.6850, -73.9650),
    "DUMBO": (40.7000, -73.9950, 40.7070, -73.9800),
    "Brooklyn Heights": (40.6900, -74.0050, 40.7020, -73.9900),
    "Cobble Hill": (40.6850, -74.0000, 40.6930, -73.9880),
    "Carroll Gardens": (40.6750, -74.0050, 40.6870, -73.9920),
    "Red Hook": (40.6700, -74.0150, 40.6820, -74.0000),
    "Fort Greene": (40.6850, -73.9800, 40.6950, -73.9650),
    "Bed-Stuy": (40.6750, -73.9550, 40.6950, -73.9250),
    "Crown Heights": (40.6650, -73.9600, 40.6800, -73.9250),

    # Queens
    "Astoria": (40.7600, -73.9450, 40.7800, -73.9150),
    "Long Island City": (40.7400, -73.9600, 40.7600, -73.9350),
    "Ridgewood": (40.6950, -73.9150, 40.7150, -73.8900),
}


async def discover_osm():
    """Run OSM discovery for NYC vintage/antique shops"""

    osm = OSMDiscovery()
    all_shops = []

    print("=" * 50)
    print("Dusty - NYC Vintage Shop Discovery")
    print("Using OpenStreetMap (no API key needed)")
    print("=" * 50)

    try:
        for neighborhood, bbox in NYC_AREAS.items():
            print(f"\nSearching {neighborhood}...")

            south, west, north, east = bbox
            places = await osm.search_area(south, west, north, east)

            if places:
                print(f"  Found {len(places)} places")

                for place in places:
                    shop = {
                        "id": str(uuid.uuid4()),
                        "name": place.name,
                        "address": place.address or f"{neighborhood}, NYC",
                        "neighborhood": neighborhood,
                        "city": "NYC",
                        "lat": place.lat,
                        "lng": place.lng,
                        "categories": place.categories or ["vintage"],
                        "phone": place.phone,
                        "website": place.website,
                        "osm_id": f"{place.osm_type}/{place.osm_id}",
                        "is_active": True,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    all_shops.append(shop)
                    print(f"    - {place.name}")
            else:
                print(f"  No results")

            # Small delay between requests
            await asyncio.sleep(0.5)

    finally:
        await osm.close()

    print("\n" + "=" * 50)
    print(f"Total shops discovered: {len(all_shops)}")
    print("=" * 50)

    return all_shops


def save_to_db(shops):
    """Save discovered shops to the database"""
    import sqlite3
    import json

    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'api', 'dusty.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inserted = 0

    for shop in shops:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO shops
                (id, name, address, neighborhood, city, lat, lng, categories,
                 phone, website, osm_id, is_active, is_verified, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shop["id"],
                shop["name"],
                shop["address"],
                shop["neighborhood"],
                shop["city"],
                shop["lat"],
                shop["lng"],
                json.dumps(shop["categories"]),
                shop.get("phone"),
                shop.get("website"),
                shop.get("osm_id"),
                1,
                0,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting {shop['name']}: {e}")

    conn.commit()
    conn.close()
    print(f"\nInserted {inserted} shops into database")


async def main():
    shops = await discover_osm()

    if shops:
        print("\nSaving to database...")
        save_to_db(shops)
        print("\nDone! Refresh the map to see the shops.")
    else:
        print("\nNo shops found. Try adding some manually or check OSM coverage.")


if __name__ == "__main__":
    asyncio.run(main())
