"""Manually trigger coefficient fetch for testing."""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/Пользо/taxi-bot')

from bot.services.yandex_api import fetch_all_coefficients


async def fetch():
    print("Fetching coefficients...")
    await fetch_all_coefficients()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(fetch())
