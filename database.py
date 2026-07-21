import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def init_db():
    conn = get_connection()
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id SERIAL PRIMARY KEY,
            city TEXT NOT NULL,
            aqi INTEGER NOT NULL,
            pm25 REAL,
            pm10 REAL,
            timestamp TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_reading(city, aqi, pm25, pm10):
    conn = get_connection()
    conn.cursor().execute(
        "INSERT INTO readings (city, aqi, pm25, pm10, timestamp) VALUES (%s, %s, %s, %s, %s)",
        (city, aqi, pm25, pm10, datetime.now())
    )
    conn.commit()
    conn.close()
    print(f"Saved: {city} AQI={aqi} at {datetime.now().strftime('%H:%M:%S')}")

def init_alert_state():
    conn = get_connection()
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS alert_state (
            city TEXT PRIMARY KEY,
            is_alerted INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_alert_state(city):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_alerted FROM alert_state WHERE city = %s", (city,))
    row = cur.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def set_alert_state(city, is_alerted):
    conn = get_connection()
    conn.cursor().execute("""
        INSERT INTO alert_state (city, is_alerted) VALUES (%s, %s)
        ON CONFLICT(city) DO UPDATE SET is_alerted = excluded.is_alerted
    """, (city, 1 if is_alerted else 0))
    conn.commit()
    conn.close()

def init_subscriptions():
    conn = get_connection()
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            city TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            threshold REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()