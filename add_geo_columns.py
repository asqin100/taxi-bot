"""Add geolocation columns to users table."""
import sqlite3

conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

# Check if columns already exist
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

# Add columns if they don't exist
if 'geo_alerts_enabled' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN geo_alerts_enabled BOOLEAN DEFAULT 0")
    print("Added geo_alerts_enabled column")

if 'last_latitude' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN last_latitude REAL")
    print("Added last_latitude column")

if 'last_longitude' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN last_longitude REAL")
    print("Added last_longitude column")

if 'last_location_update' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN last_location_update TIMESTAMP")
    print("Added last_location_update column")

if 'live_location_expires_at' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN live_location_expires_at TIMESTAMP")
    print("Added live_location_expires_at column")

conn.commit()
conn.close()
print("Migration complete!")
