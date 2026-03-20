#!/bin/bash
# Test manual sports matches import

cd /opt/taxibot && \
echo "========================================" && \
echo "  ТЕСТ ИМПОРТА СПОРТИВНЫХ МАТЧЕЙ" && \
echo "========================================" && \
echo "" && \
echo "[1/3] Получение изменений..." && \
git pull origin main && \
echo "" && \
echo "[2/3] Импорт матчей из JSON..." && \
source venv/bin/activate && \
python import_manual_matches.py && \
echo "" && \
echo "[3/3] Проверка добавленных матчей..." && \
python -c "
import asyncio
from bot.services.events import get_upcoming_events_by_type

async def check():
    sports = await get_upcoming_events_by_type('sport', limit=20)
    print(f'Всего спортивных событий: {len(sports)}')
    print()
    for event in sports:
        print(f'- {event.name}')
        print(f'  Место: {event.venue_name or event.zone_id}')
        print(f'  Дата: {event.end_time.strftime(\"%d.%m %H:%M\")}')
        print()

asyncio.run(check())
" && \
echo "========================================" && \
echo "  ✅ ТЕСТ ЗАВЕРШЕН!" && \
echo "========================================" && \
echo "" && \
echo "Теперь проверь в админ панели → Мероприятия → Спорт"
