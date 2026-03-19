#!/bin/bash

OUTPUT_FILE="/opt/taxibot/diagnostic_output.txt"

echo "Сохраняю диагностику в $OUTPUT_FILE..."

bash /opt/taxibot/diagnose_port_8080.sh > "$OUTPUT_FILE" 2>&1

echo "✓ Готово!"
echo ""
echo "Файл сохранён: $OUTPUT_FILE"
echo ""
echo "Скажи мне: 'файл готов' и я его прочитаю."
