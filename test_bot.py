#!/usr/bin/env python3
"""Diagnostic script to test bot imports and functionality."""
import sys
import asyncio
import traceback

print("=" * 60)
print("TAXI BOT DIAGNOSTIC TEST")
print("=" * 60)
print()

# Test 1: Basic imports
print("[1/6] Testing basic imports...")
try:
    from bot.config import settings
    print("✅ bot.config imported")
except Exception as e:
    print(f"❌ bot.config failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Database
print("\n[2/6] Testing database...")
try:
    from bot.database.db import session_factory
    print("✅ Database module imported")
except Exception as e:
    print(f"❌ Database failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Event parser
print("\n[3/6] Testing event parser...")
try:
    from bot.services.event_parser import parse_kudago_events
    print("✅ Event parser imported")
except Exception as e:
    print(f"❌ Event parser failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Nightclub alerts
print("\n[4/6] Testing nightclub alerts...")
try:
    from bot.services.nightclub_alerts import check_and_send_nightclub_alerts, nightclub_manager
    clubs = nightclub_manager.nightclubs
    print(f"✅ Nightclub alerts imported ({len(clubs)} clubs loaded)")
except Exception as e:
    print(f"❌ Nightclub alerts failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Events service
print("\n[5/6] Testing events service...")
try:
    from bot.services.events import get_upcoming_events
    print("✅ Events service imported")
except Exception as e:
    print(f"❌ Events service failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Async test - get events from database
print("\n[6/6] Testing database query...")
async def test_db():
    try:
        from bot.services.events import get_upcoming_events
        events = await get_upcoming_events(limit=5)
        print(f"✅ Database query successful ({len(events)} events found)")
        for event in events:
            print(f"   - {event.name} ({event.event_type}) at {event.zone_id}")
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        traceback.print_exc()
        return False
    return True

try:
    result = asyncio.run(test_db())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"❌ Async test failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("The bot should work correctly. If you're seeing errors,")
print("check the bot.log file for more details:")
print("  tail -100 bot.log")
