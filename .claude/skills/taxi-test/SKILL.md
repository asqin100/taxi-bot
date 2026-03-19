---
name: taxi-test
version: 1.0.0
description: |
  Run comprehensive tests for taxi-bot: unit tests, integration tests, load tests,
  and manual QA checklist. Provides detailed test report with coverage and performance metrics.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Taxi-bot Testing Suite

## Step 1: Unit Tests

Run pytest with coverage:

```bash
# Run all unit tests with coverage
python -m pytest tests/ -v --cov=bot --cov-report=term-missing --cov-report=html

# Check coverage percentage
COVERAGE=$(python -m pytest tests/ --cov=bot --cov-report=term | grep TOTAL | awk '{print $4}')
echo "Test Coverage: $COVERAGE"

# Fail if coverage below 70%
if [ "${COVERAGE%\%}" -lt 70 ]; then
  echo "⚠️  Coverage below 70%: $COVERAGE"
fi
```

## Step 2: Integration Tests

Test external API integrations:

```bash
# Test Yandex API
python -c "
from bot.services.yandex_api import fetch_coefficients
import asyncio
result = asyncio.run(fetch_coefficients())
print(f'Yandex API: {\"✅ OK\" if result else \"❌ FAILED\"}')
"

# Test KudaGo API
python -c "
from bot.services.event_parser import parse_kudago_events
import asyncio
result = asyncio.run(parse_kudago_events())
print(f'KudaGo API: {\"✅ OK\" if len(result) > 0 else \"❌ FAILED\"}')
print(f'Events fetched: {len(result)}')
"

# Test database connection
python -c "
from bot.database.db import get_session
from bot.models import User
from sqlalchemy import select
import asyncio

async def test_db():
    async with get_session() as session:
        result = await session.execute(select(User).limit(1))
        return result.scalar_one_or_none() is not None

result = asyncio.run(test_db())
print(f'Database: {\"✅ OK\" if result else \"❌ FAILED\"}')
"
```

## Step 3: Performance Tests

Check database query performance:

```bash
# Test user lookup performance (should be <10ms with indexes)
python -c "
import time
from bot.database.db import get_session
from bot.models import User
from sqlalchemy import select
import asyncio

async def test_perf():
    times = []
    async with get_session() as session:
        for _ in range(100):
            start = time.time()
            result = await session.execute(select(User).where(User.telegram_id == 123456789))
            result.scalar_one_or_none()
            times.append((time.time() - start) * 1000)

    avg = sum(times) / len(times)
    p99 = sorted(times)[98]
    print(f'User lookup - Avg: {avg:.2f}ms, P99: {p99:.2f}ms')
    if avg > 10:
        print('⚠️  Average query time > 10ms')

asyncio.run(test_perf())
"

# Test event notification query performance
python -c "
import time
from bot.database.db import get_session
from bot.models import Event
from sqlalchemy import select
from datetime import datetime, timedelta
import asyncio

async def test_perf():
    start = time.time()
    async with get_session() as session:
        now = datetime.now()
        result = await session.execute(
            select(Event).where(
                Event.end_time <= now + timedelta(minutes=20),
                Event.end_time > now,
                Event.pre_notified == False
            )
        )
        events = result.scalars().all()

    elapsed = (time.time() - start) * 1000
    print(f'Event notification query: {elapsed:.2f}ms ({len(events)} events)')
    if elapsed > 50:
        print('⚠️  Query time > 50ms')

asyncio.run(test_perf())
"
```

## Step 4: Load Test (Optional)

Run load test if available:

```bash
if [ -f "load_test_fixed.py" ]; then
  echo "Running load test with 100 concurrent users..."
  python load_test_fixed.py --users 100 --duration 60
else
  echo "Load test script not found, skipping"
fi
```

## Step 5: Manual QA Checklist

Present this checklist to the user:

```
═══════════════════════════════════════════════════════════════
  MANUAL QA CHECKLIST
═══════════════════════════════════════════════════════════════

Bot Functionality:
  ☐ /start command works
  ☐ User registration creates record in database
  ☐ Promo code activation works
  ☐ Subscription system works
  ☐ AI advisor responds correctly
  ☐ Event notifications sent (for paid users)
  ☐ Coefficient updates every 5 minutes
  ☐ Shift tracking works

Admin Panel:
  ☐ Login works
  ☐ Users tab loads and displays data
  ☐ Events tab loads
  ☐ "Add Event" button works
  ☐ Event creation form submits
  ☐ Events appear in list after creation
  ☐ Statistics tab shows correct data
  ☐ Promo codes tab works

Performance:
  ☐ Bot responds within 2 seconds
  ☐ Admin panel loads within 3 seconds
  ☐ No console errors in browser
  ☐ Database queries under 50ms average

═══════════════════════════════════════════════════════════════
```

Ask user to confirm each item or report issues.

## Step 6: Generate Test Report

```bash
# Create test report
cat > TEST_REPORT_$(date +%Y%m%d_%H%M%S).txt << 'EOF'
═══════════════════════════════════════════════════════════════
  TAXI-BOT TEST REPORT
═══════════════════════════════════════════════════════════════

Date: $(date)
Branch: $(git branch --show-current)
Commit: $(git log -1 --oneline)

UNIT TESTS:
  Status: {PASS/FAIL}
  Coverage: {percentage}
  Tests Run: {count}
  Failures: {count}

INTEGRATION TESTS:
  Yandex API: {✅/❌}
  KudaGo API: {✅/❌}
  Database: {✅/❌}

PERFORMANCE TESTS:
  User Lookup: {avg}ms avg, {p99}ms P99
  Event Query: {time}ms
  Status: {✅ PASS / ⚠️ SLOW / ❌ FAIL}

LOAD TESTS:
  Concurrent Users: {count}
  Success Rate: {percentage}
  Avg Response Time: {time}ms
  P99 Response Time: {time}ms

MANUAL QA:
  Bot Functionality: {items passed}/{total items}
  Admin Panel: {items passed}/{total items}
  Performance: {items passed}/{total items}

OVERALL STATUS: {✅ READY TO SHIP / ⚠️ ISSUES FOUND / ❌ NOT READY}

ISSUES FOUND:
{list of issues}

RECOMMENDATIONS:
{list of recommendations}

═══════════════════════════════════════════════════════════════
EOF

echo "Test report saved to: TEST_REPORT_$(date +%Y%m%d_%H%M%S).txt"
```

## Notes

- Run full test suite before every deployment
- Performance tests should pass with indexes installed
- Load tests are optional but recommended before major releases
- Manual QA checklist should be completed by a human
- Keep test reports for historical tracking
