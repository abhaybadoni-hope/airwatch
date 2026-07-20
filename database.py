import sqlite3
from datetime import datetime

DB_NAME = "airwatch.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            aqi INTEGER NOT NULL,
            pm25 REAL,
            pm10 REAL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_reading(city, aqi, pm25, pm10):
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT INTO readings (city, aqi, pm25, pm10, timestamp) VALUES (?, ?, ?, ?, ?)",
        (city, aqi, pm25, pm10, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    print(f"Saved: {city} AQI={aqi} at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    init_db()
    save_reading("Delhi", 3, 89.3, 142.1)  # fake data to test storage — delete later