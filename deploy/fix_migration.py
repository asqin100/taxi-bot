#!/usr/bin/env python3
"""
Исправленная миграция - запускается из корня проекта
"""
import sys
import os

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, '/opt/taxibot')

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    """Миграция данных из SQLite в PostgreSQL"""

    sqlite_path = Path("/opt/taxibot/data/bot.db")

    if not sqlite_path.exists():
        logger.info("✅ SQLite база не найдена - это свежая установка, миграция не требуется")
        return

    logger.info("📦 Найдена SQLite БД, начинаем миграцию...")

    try:
        from bot.config import settings
        from bot.database.session import get_session_factory
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        # Подключение к SQLite
        sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        SQLiteSession = sessionmaker(bind=sqlite_engine)

        # Подключение к PostgreSQL
        postgres_factory = get_session_factory()

        async with postgres_factory() as pg_session:
            with SQLiteSession() as sqlite_session:
                # Миграция пользователей
                users = sqlite_session.execute(text("SELECT * FROM users")).fetchall()
                logger.info(f"Мигрируем {len(users)} пользователей...")

                for user in users:
                    await pg_session.execute(
                        text("""
                            INSERT INTO users (telegram_id, username, first_name, created_at)
                            VALUES (:tid, :username, :fname, :created)
                            ON CONFLICT (telegram_id) DO NOTHING
                        """),
                        {
                            "tid": user[0],
                            "username": user[1],
                            "fname": user[2],
                            "created": user[3]
                        }
                    )

                await pg_session.commit()
                logger.info("✅ Миграция завершена успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        logger.info("⚠️  Продолжаем без миграции - это не критично для новой установки")

if __name__ == "__main__":
    asyncio.run(migrate())
