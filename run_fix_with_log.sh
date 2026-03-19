#!/bin/bash

RESULT_FILE="/tmp/robokassa_fix_result.txt"

echo "════════════════════════════════════════════════════════════"
echo "  ЗАПУСК ИСПРАВЛЕНИЯ..."
echo "════════════════════════════════════════════════════════════"
echo ""

# Выполняем fix_all.sh и сохраняем вывод
cd /opt/taxibot
git pull origin main > "$RESULT_FILE" 2>&1
bash fix_all.sh >> "$RESULT_FILE" 2>&1

echo "✓ Скрипт выполнен, результат сохранён в $RESULT_FILE"
echo ""

# Показываем только ключевые строки
echo "════════════════════════════════════════════════════════════"
echo "  КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ:"
echo "════════════════════════════════════════════════════════════"
echo ""

# Ищем важные строки
grep -E "(✓|✗|✅|SUCCESS|FAILED|ERROR|Ошибка)" "$RESULT_FILE" | tail -20

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Полный лог сохранён в: $RESULT_FILE"
echo ""
echo "Чтобы посмотреть полный лог:"
echo "  cat $RESULT_FILE"
echo ""
echo "Чтобы посмотреть последние 50 строк:"
echo "  tail -50 $RESULT_FILE"
echo ""
