from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from database import get_connection
import psycopg2.extras

app = FastAPI(title="AirWatch API")

def query_db(query, args=()):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/")
def home():
    return {"message": "AirWatch API is running"}

@app.get("/cities/{city}/current")
def get_current(city: str):
    rows = query_db(
        "SELECT * FROM readings WHERE city = %s ORDER BY timestamp DESC LIMIT 1",
        (city,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for city '{city}'")
    return rows[0]

@app.get("/cities/{city}/history")
def get_history(city: str, hours: int = 24):
    rows = query_db(
        """SELECT * FROM readings
           WHERE city = %s
           AND timestamp >= NOW() - INTERVAL '1 hour' * %s
           ORDER BY timestamp ASC""",
        (city, hours)
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
    conn = get_connection()
    conn.cursor().execute(
        "INSERT INTO subscriptions (city, lat, lon, threshold) VALUES (%s, %s, %s, %s)",
        (sub.city, sub.lat, sub.lon, sub.threshold)
    )
    conn.commit()
    conn.close()
    return {"message": f"Subscribed to {sub.city}", "subscription": sub}

@app.get("/subscriptions")
def list_subscriptions():
    return query_db("SELECT * FROM subscriptions")

app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")