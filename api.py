from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AirWatch API")

DB_NAME = "airwatch.db"

def query_db(query, args=()):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    rows = conn.execute(query, args).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/")
def home():
    return {"message": "AirWatch API is running"}

@app.get("/cities/{city}/current")
def get_current(city: str):
    rows = query_db(
        "SELECT * FROM readings WHERE city = ? ORDER BY timestamp DESC LIMIT 1",
        (city,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for city '{city}'")
    return rows[0]
@app.get("/cities/{city}/history")
def get_history(city: str, hours: int = 24):
    rows = query_db(
        """SELECT * FROM readings
           WHERE city = ?
           AND timestamp >= datetime('now', ?, 'localtime')
           ORDER BY timestamp ASC""",
        (city, f"-{hours} hours")
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for city '{city}'")
    return rows
class Subscription(BaseModel):
    city: str
    lat: float
    lon: float
    threshold: float = 150.0

@app.post("/subscriptions")
def add_subscription(sub: Subscription):
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT INTO subscriptions (city, lat, lon, threshold) VALUES (?, ?, ?, ?)",
        (sub.city, sub.lat, sub.lon, sub.threshold)
    )
    conn.commit()
    conn.close()
    return {"message": f"Subscribed to {sub.city}", "subscription": sub}

@app.get("/subscriptions")
def list_subscriptions():
    return query_db("SELECT * FROM subscriptions")

app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")