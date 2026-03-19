#!/bin/bash
# Database migration script
# Run this script to apply database migrations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="${SCRIPT_DIR}/../data/bot.db"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           DATABASE MIGRATION                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "✗ Database not found: $DB_PATH"
    exit 1
fi

echo "✓ Database found: $DB_PATH"
echo ""

# Create backup
BACKUP_FILE="${DB_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_FILE"
echo "✓ Backup created: $BACKUP_FILE"
echo ""

# Apply migration
echo "Applying migration: add_geo_alerts_columns.sql"
sqlite3 "$DB_PATH" < "${SCRIPT_DIR}/add_geo_alerts_columns.sql"

if [ $? -eq 0 ]; then
    echo "✓ Migration applied successfully"
else
    echo "⚠ Migration failed (columns may already exist)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✓ MIGRATION COMPLETE                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
