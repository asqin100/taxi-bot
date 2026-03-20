#!/bin/bash
# Быстрое исправление и деплой обновления
# Использование: скопируй и вставь эту команду на сервере

cd /opt/taxibot && \
git fetch origin main && \
git reset --hard origin/main && \
systemctl restart taxibot && \
echo "✅ Бот перезапущен. Проверяем статус..." && \
systemctl status taxibot --no-pager && \
echo "" && \
echo "📋 Последние 30 строк логов:" && \
tail -30 bot.log && \
echo "" && \
echo "✅ ДЕПЛОЙ ЗАВЕРШЕН!" && \
echo "Новые функции:" && \
echo "  - Расширенный парсинг событий (спорт, театр, выставки)" && \
echo "  - Алерты по ночным клубам (пт/сб 05:00)" && \
echo "  - 12 топовых клубов Москвы"
