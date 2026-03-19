"""Migration script to add financial tracker tables."""
import sqlite3
from pathlib import Path

# Hardcoded database path
DB_PATH = Path(__file__).parent / "data" / "bot.db"


def migrate():
    """Create financial tracker tables."""
    print(f"Migrating database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run migrate_event_filters.py first to create the database")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    migrations_applied = []

    # Create user_financial_settings table
    if "user_financial_settings" not in existing_tables:
        print("Creating table: user_financial_settings")
        cursor.execute("""
            CREATE TABLE user_financial_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT UNIQUE NOT NULL,
                fuel_price_per_liter REAL DEFAULT 55.0,
                fuel_consumption_per_100km REAL DEFAULT 8.0,
                rent_per_day REAL DEFAULT 0.0,
                commission_percent REAL DEFAULT 20.0,
                daily_goal REAL DEFAULT 0.0,
                weekly_goal REAL DEFAULT 0.0,
                monthly_goal REAL DEFAULT 0.0
            )
        """)
        cursor.execute("CREATE INDEX idx_user_financial_settings_user_id ON user_financial_settings(user_id)")
        migrations_applied.append("user_financial_settings")
    else:
        print("Table user_financial_settings already exists")

    # Create shifts table
    if "shifts" not in existing_tables:
        print("Creating table: shifts")
        cursor.execute("""
            CREATE TABLE shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                gross_earnings REAL DEFAULT 0.0,
                trips_count INTEGER DEFAULT 0,
                distance_km REAL DEFAULT 0.0,
                fuel_cost REAL DEFAULT 0.0,
                rent_cost REAL DEFAULT 0.0,
                commission REAL DEFAULT 0.0,
                other_expenses REAL DEFAULT 0.0,
                net_earnings REAL DEFAULT 0.0,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_shifts_user_id ON shifts(user_id)")
        cursor.execute("CREATE INDEX idx_shifts_start_time ON shifts(start_time)")
        migrations_applied.append("shifts")
    else:
        print("Table shifts already exists")

    conn.commit()
    conn.close()

    if migrations_applied:
        print(f"\n✅ Migration complete! Created tables: {', '.join(migrations_applied)}")
    else:
        print("\n✅ No migration needed - all tables already exist")


if __name__ == "__main__":
    migrate()
