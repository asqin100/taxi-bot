#!/usr/bin/env python3
"""Test admin panel functions."""
import asyncio
import sys

print("=" * 60)
print("TESTING ADMIN PANEL FUNCTIONS")
print("=" * 60)
print()

async def test_admin_functions():
    try:
        from bot.services.admin import get_recent_users, get_dashboard_stats

        print("[1/2] Testing get_recent_users()...")
        users = await get_recent_users(limit=5)
        print(f"✅ Found {len(users)} recent users:")
        for user in users:
            print(f"   - ID: {user['telegram_id']}, Username: {user.get('username', 'N/A')}")
        print()

        print("[2/2] Testing get_dashboard_stats()...")
        stats = await get_dashboard_stats()
        print(f"✅ Dashboard stats:")
        print(f"   - Total users: {stats['users']['total']}")
        print(f"   - Active users: {stats['users']['active']}")
        print(f"   - New today: {stats['users']['new_today']}")
        print()

        print("=" * 60)
        print("✅ ALL ADMIN FUNCTIONS WORK!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_admin_functions())
    sys.exit(0 if result else 1)
