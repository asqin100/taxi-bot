"""Миграция данных из SQLite в PostgreSQL."""
import asyncio
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Migrate data from SQLite to PostgreSQL."""
    logger.info("🔄 Начало миграции SQLite → PostgreSQL")

    # Проверка наличия старой БД
    sqlite_db = Path("data/bot.db")
    if not sqlite_db.exists():
        logger.info("📝 SQLite БД не найдена, создаем новую PostgreSQL БД")
        await create_fresh_db()
        return

    logger.info("📦 Найдена SQLite БД, начинаем миграцию данных...")

    try:
        # Импорт после проверки файлов
        from sqlalchemy import create_engine, text
        from sqlalchemy.ext.asyncio import create_async_engine
        from bot.config import settings
        from bot.database.db import Base, engine as pg_engine

        # Создание таблиц в PostgreSQL
        logger.info("🏗️  Создание таблиц в PostgreSQL...")
        async with pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы созданы")

        # Подключение к SQLite
        sqlite_engine = create_engine(f"sqlite:///{sqlite_db}")

        # Список таблиц для миграции
        tables = [
            "users",
            "subscriptions",
            "shifts",
            "alerts",
            "referrals",
            "referral_earnings",
            "promo_codes",
            "promo_code_usage",
            "historical_demand_data"
        ]

        # Миграция каждой таблицы
        for table in tables:
            try:
                logger.info(f"📊 Миграция таблицы: {table}")

                # Чтение из SQLite
                with sqlite_engine.connect() as sqlite_conn:
                    result = sqlite_conn.execute(text(f"SELECT * FROM {table}"))
                    rows = result.fetchall()
                    columns = result.keys()

                    if not rows:
                        logger.info(f"  ⚠️  Таблица {table} пуста, пропускаем")
                        continue

                    logger.info(f"  📝 Найдено {len(rows)} записей")

                # Запись в PostgreSQL
                async with pg_engine.begin() as pg_conn:
                    # Формирование INSERT запроса
                    cols = ", ".join(columns)
                    placeholders = ", ".join([f":{col}" for col in columns])
                    insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

                    # Вставка данных
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        await pg_conn.execute(text(insert_sql), row_dict)

                    logger.info(f"  ✅ Таблица {table} мигрирована ({len(rows)} записей)")

            except Exception as e:
                logger.warning(f"  ⚠️  Ошибка миграции таблицы {table}: {e}")
                continue

        logger.info("✅ Миграция завершена успешно!")
        logger.info("💡 Рекомендация: создайте бэкап SQLite БД и удалите её")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise


async def create_fresh_db():
    """Create fresh PostgreSQL database."""
    try:
        from bot.database.db import Base, engine

        logger.info("🏗️  Создание новой БД...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ База данных создана успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
