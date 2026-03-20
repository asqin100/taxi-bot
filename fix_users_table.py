#!/usr/bin/env python3
"""Fix missing preferred_tariff column in users table."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"

print("=" * 60)
print("FIXING USERS TABLE - ADDING PREFERRED_TARIFF COLUMN")
print("=" * 60)
print()

if not DB_PATH.exists():
    print(f"❌ Database not found at: {DB_PATH}")
    sys.exit(1)

print(f"📁 Database: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("[1/3] Checking current table structure...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"Current columns: {', '.join(column_names)}")
print()

if 'preferred_tariff' in column_names:
    print("✅ preferred_tariff column already exists!")
    print("No migration needed.")
    conn.close()
    sys.exit(0)

print("[2/3] Adding preferred_tariff column...")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN preferred_tariff VARCHAR(64)")
    conn.commit()
    print("  ✅ preferred_tariff added")
    print()

except Exception as e:
    print(f"❌ Error adding column: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

print("[3/3] Verifying changes...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"New columns count: {len(column_names)}")
print()

if 'preferred_tariff' in column_names:
    print("=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart the bot: systemctl restart taxibot")
    print("2. Check status: systemctl status taxibot")
    print("3. Test bot: send any message to the bot")
else:
    print("❌ Verification failed - column was not added")
    conn.close()
    sys.exit(1)

conn.close()
