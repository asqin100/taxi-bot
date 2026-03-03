"""
Apply coefficient_history migration (003_coefficient_history.sql)
Run this script to create the coefficient_history table for ML predictions
"""
import sqlite3
import sys
from pathlib import Path


def apply_migration():
    db_path = Path(__file__).parent / "data" / "bot.db"
    migration_path = Path(__file__).parent / "data" / "003_coefficient_history.sql"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run the bot first to create the database")
        sys.exit(1)

    if not migration_path.exists():
        print(f"Error: Migration file not found at {migration_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Read and execute migration
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor.executescript(migration_sql)
        conn.commit()
        print("✅ Migration 003_coefficient_history.sql applied successfully!")

        # Verify table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coefficient_history'")
        if cursor.fetchone():
            print("✅ Table 'coefficient_history' created")

            # Show table structure
            cursor.execute("PRAGMA table_info(coefficient_history)")
            columns = cursor.fetchall()
            print("\nTable structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Show indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='coefficient_history'")
            indexes = cursor.fetchall()
            print(f"\nIndexes created: {len(indexes)}")
            for idx in indexes:
                print(f"  - {idx[0]}")

    except sqlite3.Error as e:
        print(f"❌ Error applying migration: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migration()
