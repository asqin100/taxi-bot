"""Test script to verify Yandex Pro API connection."""
import asyncio
import logging

from bot.services.yandex_api import fetch_all_coefficients, get_cached_coefficients
from bot.services.zones import get_zones

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main():
    print("=" * 60)
    print("Testing Yandex Pro API Connection")
    print("=" * 60)

    # Show zones
    zones = get_zones()
    print(f"\nConfigured zones: {len(zones)}")
    for zone in zones[:3]:
        print(f"  - {zone.id}: {zone.name}")

    # Fetch coefficients
    print("\nFetching surge coefficients...")
    try:
        results = await fetch_all_coefficients()
        print(f"✅ Successfully fetched {len(results)} data points")

        # Show results
        cached = get_cached_coefficients()
        print(f"\nCached coefficients: {len(cached)}")

        # Group by zone
        by_zone = {}
        for item in cached:
            if item.zone_id not in by_zone:
                by_zone[item.zone_id] = []
            by_zone[item.zone_id].append(item)

        print("\nResults by zone:")
        for zone_id, items in list(by_zone.items())[:5]:
            print(f"\n  {zone_id}:")
            for item in items:
                print(f"    {item.tariff}: {item.coefficient:.2f}x")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
