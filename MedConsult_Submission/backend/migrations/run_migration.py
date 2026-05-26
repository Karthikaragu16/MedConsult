"""
Safe migration: adds 'answer' and 'answered_by' columns to the queries table.
Skips gracefully if columns already exist (no data loss).
Run: python backend/migrations/run_migration.py
"""
import MySQLdb

conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='YOUR_DB_PASSWORD',
    db='health_assistant'
)
cursor = conn.cursor()

def column_exists(table, column):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'health_assistant'
          AND TABLE_NAME   = %s
          AND COLUMN_NAME  = %s
    """, (table, column))
    return cursor.fetchone()[0] > 0

migrations = [
    ("queries", "answer",      "ALTER TABLE queries ADD COLUMN answer TEXT"),
    ("queries", "answered_by", "ALTER TABLE queries ADD COLUMN answered_by INT"),
]

print("Running migrations...\n")
for table, column, sql in migrations:
    if not column_exists(table, column):
        cursor.execute(sql)
        conn.commit()
        print(f"  [OK] Added column '{column}' to '{table}'")
    else:
        print(f"  [SKIP] Column '{column}' in '{table}' already exists")

print("\nAll migrations complete.")
cursor.close()
conn.close()
