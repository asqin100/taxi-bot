#!/usr/bin/env python3
"""Simple test to check if Nominatim API is accessible from production server."""
import sys
import urllib.request
import json
import time

def test_nominatim():
    """Test Nominatim API access."""
    print("Testing Nominatim API access...")
    print("="*60)

    # Test coordinates (Moscow)
    lat, lon = 55.7558, 37.6173

    url = "https://nominatim.openstreetmap.org/search"

    chains = ["Вкусно и точка", "Burger King"]

    for chain in chains:
        print(f"\nSearching: {chain}")

        params = f"?q={chain}&format=json&limit=5&bounded=1&viewbox={lon-0.2},{lat-0.2},{lon+0.2},{lat+0.2}"
        full_url = url + params

        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "KefPulse TaxiBot/1.0"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                data = json.loads(response.read().decode('utf-8'))

                print(f"  Status: {status}")
                print(f"  Results: {len(data)}")

                if len(data) > 0:
                    print(f"  First result: {data[0].get('display_name', '')[:80]}")
                    print("  SUCCESS - API is accessible")
                else:
                    print("  WARNING - No results returned")

        except Exception as e:
            print(f"  ERROR: {e}")
            print("  FAILED - Cannot access Nominatim API")
            return False

        time.sleep(1)  # Rate limiting

    print("\n" + "="*60)
    print("Nominatim API is accessible from this server")
    return True

if __name__ == "__main__":
    success = test_nominatim()
    sys.exit(0 if success else 1)
