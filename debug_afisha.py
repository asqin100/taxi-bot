"""Debug script to see what Yandex.Afisha returns."""
import asyncio
import re
import aiohttp


async def debug_afisha():
    url = "https://afisha.yandex.ru/moscow/concert"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            print(f"Status: {resp.status}")
            html = await resp.text()
            print(f"HTML length: {len(html)} chars")

            # Check for Apollo cache
            apollo_match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.+?});', html, re.DOTALL)
            print(f"\nApollo cache found: {apollo_match is not None}")

            # Check for __NEXT_DATA__
            next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>({.+?})</script>', html, re.DOTALL)
            print(f"__NEXT_DATA__ found: {next_data_match is not None}")

            # Look for any script tags with JSON
            script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html[:50000], re.DOTALL)
            print(f"\nFound {len(script_tags)} script tags in first 50KB")

            # Check for common patterns
            if '"Event"' in html:
                print("Found 'Event' string in HTML")
            if '"concert"' in html:
                print("Found 'concert' string in HTML")
            if '"place"' in html or '"venue"' in html:
                print("Found place/venue references")

            # Save first 100KB to file for manual inspection
            with open('afisha_debug.html', 'w', encoding='utf-8') as f:
                f.write(html[:100000])
            print("\nSaved first 100KB to afisha_debug.html")


if __name__ == "__main__":
    asyncio.run(debug_afisha())
