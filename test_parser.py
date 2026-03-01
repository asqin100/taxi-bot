"""Test event parser to debug Yandex.Afisha parsing."""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/Пользо/taxi-bot')

from bot.services.event_parser import parse_yandex_afisha, fetch_and_store_events


async def test_parser():
    print("Testing Yandex.Afisha parser...")
    events = await parse_yandex_afisha()

    print(f"\nFound {len(events)} events:")
    for i, event in enumerate(events[:10], 1):
        print(f"\n{i}. {event['name']}")
        print(f"   Zone: {event['zone_id']}")
        print(f"   Type: {event['event_type']}")
        print(f"   End time: {event['end_time']}")


if __name__ == "__main__":
    asyncio.run(test_parser())
