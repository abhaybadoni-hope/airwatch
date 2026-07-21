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

def init_alert_state():
    """Table remembering whether each city is currently in an alerted state."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_state (
            city TEXT PRIMARY KEY,
            is_alerted INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_alert_state(city):
    """Return True if we've already alerted for this city, else False."""
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT is_alerted FROM alert_state WHERE city = ?", (city,)
    ).fetchone()
    conn.close()
    return bool(row[0]) if row else False

def set_alert_state(city, is_alerted):
    """Record whether this city is currently alerted (uses UPSERT)."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT INTO alert_state (city, is_alerted) VALUES (?, ?)
        ON CONFLICT(city) DO UPDATE SET is_alerted = excluded.is_alerted
    """, (city, 1 if is_alerted else 0))
    conn.commit()
    conn.close()