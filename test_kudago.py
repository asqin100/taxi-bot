"""Test script for KudaGo API integration."""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from bot.services.event_parser import parse_kudago_events, venue_mapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def test_kudago():
    """Test KudaGo API integration."""
    print("=" * 60)
    print("Testing KudaGo API Integration")
    print("=" * 60)

    # Test venue mapper
    print("\n1. Testing venue mapper...")
    test_venues = ["Лужники", "Крокус", "ВТБ Арена", "Олимпийский"]
    for venue in test_venues:
        zone = venue_mapper.find_zone(venue)
        print(f"   {venue} -> {zone}")

    # Test KudaGo API
    print("\n2. Fetching events from KudaGo API...")
    events = await parse_kudago_events()

    print(f"\n3. Results: Found {len(events)} events")

    if events:
        print("\n4. Sample events (first 5):")
        for i, event in enumerate(events[:5], 1):
            print(f"\n   Event {i}:")
            print(f"   Name: {event['name']}")
            print(f"   Zone: {event['zone_id']}")
            print(f"   Type: {event['event_type']}")
            print(f"   End time: {event['end_time'].strftime('%d.%m.%Y %H:%M')}")
    else:
        print("\n   No events found. This might be normal if:")
        print("   - No events match our venue list")
        print("   - API is temporarily unavailable")
        print("   - No upcoming events in the next 30 days")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_kudago())
