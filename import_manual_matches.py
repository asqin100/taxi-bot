#!/usr/bin/env python3
"""Import manually added sports matches from JSON file."""
import json
import asyncio
from datetime import datetime
from pathlib import Path

async def import_manual_matches():
    from bot.services.events import create_event
    from bot.utils.timezone import moscow_tz

    print("=" * 60)
    print("IMPORTING MANUAL SPORTS MATCHES")
    print("=" * 60)
    print()

    # Load matches from JSON
    json_path = Path(__file__).parent / "data" / "manual_sports_matches.json"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return

    matches = data.get("upcoming_matches", [])
    print(f"Found {len(matches)} matches in JSON file")
    print()

    imported_count = 0
    skipped_count = 0

    for match in matches:
        try:
            # Parse date and time
            date_str = match["date"]
            time_str = match["time"]
            datetime_str = f"{date_str} {time_str}"

            # Create datetime in Moscow timezone
            match_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            match_datetime = moscow_tz.localize(match_datetime)

            # Skip past matches
            now = datetime.now(moscow_tz)
            if match_datetime < now:
                print(f"⏭ Skipping past match: {match['name']}")
                skipped_count += 1
                continue

            # Assume match ends 2.5 hours after start
            from datetime import timedelta
            end_time = match_datetime + timedelta(hours=2, minutes=30)

            # Create event
            await create_event(
                name=match["name"],
                zone_id=match["zone_id"],
                event_type="sport",
                end_time=end_time,
                venue_name=match.get("venue"),
                venue_lat=match.get("venue_lat"),
                venue_lon=match.get("venue_lon")
            )

            print(f"✅ Imported: {match['name']}")
            print(f"   Venue: {match['venue']}")
            print(f"   Date: {match_datetime.strftime('%d.%m %H:%M')}")
            print()

            imported_count += 1

        except Exception as e:
            print(f"❌ Failed to import {match.get('name', 'unknown')}: {e}")
            print()

    print("=" * 60)
    print(f"✅ IMPORT COMPLETED!")
    print(f"   Imported: {imported_count}")
    print(f"   Skipped: {skipped_count}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(import_manual_matches())
