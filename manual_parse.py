#!/usr/bin/env python3
"""Скрипт для ручного запуска парсинга событий"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.services.event_parser import fetch_and_store_events
from bot.database import init_db

async def main():
    print("Инициализация базы данных...")
    await init_db()

    print("Запуск парсинга событий...")
    await fetch_and_store_events()

    print("Парсинг завершен!")

if __name__ == "__main__":
    asyncio.run(main())
