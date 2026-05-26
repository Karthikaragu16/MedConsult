"""
Migration: Creates doctor_slots table and auto-populates slots
for all existing doctors for the next 14 days.
Run: python backend/migrations/populate_slots.py
"""
import MySQLdb
import datetime

conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='YOUR_DB_PASSWORD',
    db='health_assistant'
)
cursor = conn.cursor()

# --- Step 1: Create the doctor_slots table ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_slots (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        doctor_id   INT NOT NULL,
        slot_date   DATE NOT NULL,
        slot_time   VARCHAR(20) NOT NULL,
        is_booked   BOOLEAN DEFAULT FALSE,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE,
        UNIQUE KEY uq_slot (doctor_id, slot_date, slot_time)
    )
""")
conn.commit()
print("[OK] doctor_slots table ready.")

# --- Step 2: Fetch all doctors ---
cursor.execute("SELECT id FROM doctor")
doctors = [row[0] for row in cursor.fetchall()]

if not doctors:
    print("[SKIP] No doctors found in database. Add doctors first.")
else:
    # Standard time slots per day
    TIME_SLOTS = [
        "09:00 AM", "10:00 AM", "11:00 AM",
        "12:00 PM", "02:00 PM", "03:00 PM",
        "04:00 PM", "05:00 PM"
    ]

    today = datetime.date.today()
    inserted = 0

    for doctor_id in doctors:
        for day_offset in range(0, 15):           # next 14 days
            slot_date = today + datetime.timedelta(days=day_offset)
            # Skip Sundays (weekday() == 6)
            if slot_date.weekday() == 6:
                continue
            for slot_time in TIME_SLOTS:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO doctor_slots (doctor_id, slot_date, slot_time, is_booked)
                        VALUES (%s, %s, %s, FALSE)
                    """, (doctor_id, slot_date, slot_time))
                    inserted += cursor.rowcount
                except Exception as e:
                    print(f"  [WARN] {e}")

    conn.commit()
    print(f"[OK] Inserted {inserted} new slots for {len(doctors)} doctor(s) over 14 days.")

cursor.close()
conn.close()
print("\nSlot population complete.")
