"""
Migration: fix_hospital_name.py
Backfills NULL hospital_name values in the doctor table.
Run once: python migrations/fix_hospital_name.py
"""
import MySQLdb

conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='YOUR_DB_PASSWORD',
    db='health_assistant'
)
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# Find all doctors with NULL or empty hospital_name but a valid hospital_id
cursor.execute("""
    SELECT d.id, d.name, d.hospital_id, h.name AS hosp_name
    FROM   doctor d
    JOIN   hospitals h ON d.hospital_id = h.id
    WHERE  d.hospital_name IS NULL OR d.hospital_name = ''
""")
rows = cursor.fetchall()

if not rows:
    print("No doctors with NULL hospital_name found -- nothing to fix.")
else:
    for row in rows:
        cursor.execute(
            "UPDATE doctor SET hospital_name = %s WHERE id = %s",
            (row['hosp_name'], row['id'])
        )
        print("Fixed Dr. {} -> hospital_name = '{}'".format(row['name'], row['hosp_name']))
    conn.commit()
    print("\nUpdated {} doctor record(s) successfully.".format(len(rows)))

# Show final state
cursor.execute("SELECT id, name, dept, hospital_id, hospital_name FROM doctor")
doctors = cursor.fetchall()
print("\n--- Current doctor table ---")
for d in doctors:
    print("  ID:{} | {} | {} | hospital_id:{} | hospital_name:{}".format(
        d['id'], d['name'], d['dept'], d['hospital_id'], d['hospital_name']))

cursor.close()
conn.close()
