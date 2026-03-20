#!/usr/bin/env python3
"""Delete all loadtest_user accounts from database."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"

print("=" * 60)
print("DELETING LOADTEST USERS")
print("=" * 60)
print()

if not DB_PATH.exists():
    print(f"❌ Database not found at: {DB_PATH}")
    sys.exit(1)

print(f"📁 Database: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("[1/3] Finding loadtest users...")
cursor.execute("SELECT id, telegram_id, username FROM users WHERE username LIKE '%loadtest_user%'")
users = cursor.fetchall()

if not users:
    print("✅ No loadtest users found!")
    conn.close()
    sys.exit(0)

print(f"Found {len(users)} loadtest users:")
for user_id, telegram_id, username in users:
    print(f"  - ID: {user_id}, Telegram ID: {telegram_id}, Username: {username}")
print()

print("[2/3] Deleting loadtest users...")

try:
    # Delete from users table
    cursor.execute("DELETE FROM users WHERE username LIKE '%loadtest_user%'")
    deleted_count = cursor.rowcount

    conn.commit()
    print(f"✅ Deleted {deleted_count} users")
    print()

except Exception as e:
    print(f"❌ Error deleting users: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

print("[3/3] Verifying deletion...")
cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE '%loadtest_user%'")
remaining = cursor.fetchone()[0]

if remaining == 0:
    print("=" * 60)
    print("✅ ALL LOADTEST USERS DELETED!")
    print("=" * 60)
else:
    print(f"❌ Still {remaining} loadtest users remaining")
    conn.close()
    sys.exit(1)

conn.close()
