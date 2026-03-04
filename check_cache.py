import time
from bot.services.yandex_api import cache

data = cache.get_all()
print(f'Cached coefficients: {len(data)}')

if data:
    latest = max(d.timestamp for d in data)
    age = time.time() - latest
    print(f'Latest timestamp: {latest}')
    print(f'Current time: {time.time()}')
    print(f'Age: {age:.0f} seconds ({age/60:.1f} minutes)')

    # Show some recent coefficients
    print('\nRecent coefficients:')
    for d in sorted(data, key=lambda x: x.timestamp, reverse=True)[:10]:
        print(f'  {d.zone_id} / {d.tariff}: {d.coefficient}')
else:
    print('No cached data found')
