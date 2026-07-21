from apscheduler.schedulers.blocking import BlockingScheduler
from fetcher import fetch_aqi
from database import init_db, save_reading

CITIES = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
]

def poll_all_cities():
    for city in CITIES:
        try:
            reading = fetch_aqi(city["lat"], city["lon"])
            save_reading(city["name"], reading["aqi"], reading["pm25"], reading["pm10"])
        except Exception as e:
            print(f"Failed to fetch {city['name']}: {e}")

if __name__ == "__main__":
    init_db()
    poll_all_cities()  # run once immediately so you see it work right away

    scheduler = BlockingScheduler()
    scheduler.add_job(poll_all_cities, "interval", minutes=15)
    print("Scheduler started. Polling every 15 minutes. Press Ctrl+C to stop.")
    scheduler.start()