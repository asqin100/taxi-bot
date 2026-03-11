#!/bin/bash
cd /opt/taxibot

echo "=== ДЕТАЛЬНЫЙ АНАЛИЗ 429 ОШИБОК ==="
echo ""

echo "1. Количество зон:"
python3 -c "from bot.services.zones import get_zones; print(f'Всего зон: {len(get_zones())}')"
echo ""

echo "2. Всего 429 ошибок за всё время:"
grep -i '429' bot.log 2>/dev/null | wc -l
echo ""

echo "3. 429 ошибки по датам (последние 10 дней):"
grep -i '429' bot.log 2>/dev/null | grep -oE '2026-[0-9]{2}-[0-9]{2}' | sort | uniq -c | tail -10
echo ""

echo "4. Последняя 429 ошибка:"
grep -i '429' bot.log 2>/dev/null | tail -1
echo ""

echo "5. Успешные запросы сегодня (2026-03-10):"
grep "Found surge" bot.log 2>/dev/null | grep "2026-03-10" | wc -l
echo ""

echo "6. Последние 5 успешных запросов:"
grep "Found surge" bot.log 2>/dev/null | tail -5
echo ""

echo "7. Текущий интервал парсинга:"
grep "parse_interval_seconds" /opt/taxibot/bot/config.py 2>/dev/null || echo "Не найдено"
echo ""

echo "8. Статус бота:"
ps aux | grep "python.*bot.main" | grep -v grep
