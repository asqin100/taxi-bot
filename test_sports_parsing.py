#!/usr/bin/env python3
"""Test sports events parsing."""
import asyncio
import sys

async def test_parsing():
    from bot.services.event_parser import fetch_and_store_events
    from bot.services.events import get_upcoming_events_by_type
    
    print("=" * 60)
    print("TESTING SPORTS EVENTS PARSING")
    print("=" * 60)
    print()
    
    print("[1/3] Fetching and parsing events from KudaGo...")
    try:
        stored_count = await fetch_and_store_events()
        print(f"✅ Stored {stored_count} new events")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("[2/3] Checking sports events in database...")
    try:
        sports_events = await get_upcoming_events_by_type(event_type="sport", limit=50)
        print(f"✅ Found {len(sports_events)} sports events:")
        for event in sports_events[:10]:
            print(f"   - {event.name}")
            print(f"     Venue: {event.venue_name or 'N/A'}")
            print(f"     Zone: {event.zone_id}")
            print(f"     End: {event.end_time.strftime('%d.%m %H:%M')}")
            print()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("[3/3] Summary by event type...")
    try:
        from bot.services.events import get_upcoming_events
        all_events = await get_upcoming_events(limit=200)
        
        types_count = {}
        for event in all_events:
            types_count[event.event_type] = types_count.get(event.event_type, 0) + 1
        
        print("Event types distribution:")
        for event_type, count in sorted(types_count.items(), key=lambda x: x[1], reverse=True):
            emoji = {"sport": "⚽", "concert": "🎵", "theater": "🎭", "conference": "🎤", "other": "📅"}.get(event_type, "📍")
            print(f"   {emoji} {event_type}: {count}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("✅ TEST COMPLETED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_parsing())
    sys.exit(0 if result else 1)
