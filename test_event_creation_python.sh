#!/bin/bash
# Тест создания мероприятий напрямую через Python

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ТЕСТ СОЗДАНИЯ МЕРОПРИЯТИЙ (Python)                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/taxibot

echo "1. Проверка таблицы events..."
sqlite3 data/bot.db "SELECT COUNT(*) as total FROM events;" 2>/dev/null || echo "Ошибка доступа к БД"

echo ""
echo "2. Тест создания мероприятия через Python..."

python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
from datetime import datetime, timedelta

# Add bot directory to path
sys.path.insert(0, '/opt/taxibot')

async def test_create_event():
    try:
        from bot.services.events import create_event

        # Create event for tomorrow at 20:00
        tomorrow = datetime.now() + timedelta(days=1)
        end_time = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)

        print(f"   Создаём мероприятие с end_time: {end_time}")
        print(f"   Текущее время: {datetime.now()}")
        print(f"   Разница: {(end_time - datetime.now()).total_seconds() / 3600:.1f} часов")

        event = await create_event(
            name="Тест из скрипта",
            zone_id="luzhniki",
            event_type="concert",
            end_time=end_time
        )

        print(f"   ✅ Мероприятие создано!")
        print(f"   ID: {event.id}")
        print(f"   Название: {event.name}")
        print(f"   Зона: {event.zone_id}")
        print(f"   Окончание: {event.end_time}")

        return True

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the test
result = asyncio.run(test_create_event())
sys.exit(0 if result else 1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "3. Проверка созданного мероприятия..."
    sqlite3 data/bot.db "SELECT id, name, zone_id, datetime(end_time) FROM events ORDER BY id DESC LIMIT 1;"

    echo ""
    echo "✅ ТЕСТ ПРОЙДЕН! Создание мероприятий работает."
else
    echo ""
    echo "❌ ТЕСТ НЕ ПРОЙДЕН! Смотрите ошибку выше."
fi

echo ""
echo "4. Все мероприятия в БД:"
sqlite3 data/bot.db "SELECT id, name, zone_id, datetime(end_time) FROM events ORDER BY id DESC LIMIT 5;"
