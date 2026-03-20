#!/usr/bin/env python3
"""Fix missing venue columns in events table."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"

print("=" * 60)
print("FIXING EVENTS TABLE - ADDING VENUE COLUMNS")
print("=" * 60)
print()

# Check if database exists
if not DB_PATH.exists():
    print(f"❌ Database not found at: {DB_PATH}")
    sys.exit(1)

print(f"📁 Database: {DB_PATH}")
print()

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check current table structure
print("[1/3] Checking current table structure...")
cursor.execute("PRAGMA table_info(events)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"Current columns: {', '.join(column_names)}")
print()

# Check if venue columns already exist
has_venue_name = 'venue_name' in column_names
has_venue_lat = 'venue_lat' in column_names
has_venue_lon = 'venue_lon' in column_names

if has_venue_name and has_venue_lat and has_venue_lon:
    print("✅ All venue columns already exist!")
    print("No migration needed.")
    conn.close()
    sys.exit(0)

# Add missing columns
print("[2/3] Adding missing venue columns...")

try:
    if not has_venue_name:
        print("  Adding venue_name...")
        cursor.execute("ALTER TABLE events ADD COLUMN venue_name VARCHAR(256)")
        print("  ✅ venue_name added")

    if not has_venue_lat:
        print("  Adding venue_lat...")
        cursor.execute("ALTER TABLE events ADD COLUMN venue_lat FLOAT")
        print("  ✅ venue_lat added")

    if not has_venue_lon:
        print("  Adding venue_lon...")
        cursor.execute("ALTER TABLE events ADD COLUMN venue_lon FLOAT")
        print("  ✅ venue_lon added")

    conn.commit()
    print()
    print("✅ All columns added successfully!")

except Exception as e:
    print(f"❌ Error adding columns: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

# Verify the changes
print()
print("[3/3] Verifying changes...")
cursor.execute("PRAGMA table_info(events)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"New columns: {', '.join(column_names)}")
print()

# Check if all venue columns are present
if 'venue_name' in column_names and 'venue_lat' in column_names and 'venue_lon' in column_names:
    print("=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart the bot: systemctl restart taxibot")
    print("2. Check status: systemctl status taxibot")
    print("3. Test events: python test_bot.py")
else:
    print("❌ Verification failed - not all columns were added")
    conn.close()
    sys.exit(1)

conn.close()
