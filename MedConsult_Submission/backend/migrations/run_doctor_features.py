"""Run doctor_features.sql migration."""
import MySQLdb, os

conn = MySQLdb.connect(host='localhost', user='root', passwd='YOUR_DB_PASSWORD', db='health_assistant')
cur  = conn.cursor()

sql_file = os.path.join(os.path.dirname(__file__), 'doctor_features.sql')
with open(sql_file) as f:
    statements = [s.strip() for s in f.read().split(';') if s.strip()]

for stmt in statements:
    if stmt.startswith('--'):
        continue
    try:
        cur.execute(stmt)
        print("OK:", stmt[:60])
    except Exception as e:
        print("SKIP:", e)

conn.commit()
cur.close()
conn.close()
print("\nMigration complete.")
