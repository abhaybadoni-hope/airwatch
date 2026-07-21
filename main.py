from apscheduler.schedulers.blocking import BlockingScheduler
from fetcher import fetch_aqi
import logging
from database import init_db, save_reading
from notifier import send_alert
from database import init_db, save_reading, init_alert_state, get_alert_state, set_alert_state

CITIES = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
]

PM25_THRESHOLD = 150 # µg/m³ — above this, air is unhealthy
logger = logging.getLogger(__name__)

def poll_all_cities():
    for city in CITIES:
        name = city["name"]
        try:
            reading = fetch_aqi(city["lat"], city["lon"])
            save_reading(name, reading["aqi"], reading["pm25"], reading["pm10"])

            currently_bad = reading["pm25"] > PM25_THRESHOLD
            already_alerted = get_alert_state(name)

            if currently_bad and not already_alerted:
                send_alert(f"⚠️ {name}: PM2.5 is {reading['pm25']} — unhealthy air!")
                set_alert_state(name, True)
            elif not currently_bad and already_alerted:
                send_alert(f"✅ {name}: PM2.5 back to {reading['pm25']} — air improved.")
                set_alert_state(name, False)

        except Exception as e:
            logger.error(f"Failed to fetch {name}: {e}")

if __name__ == "__main__":
    init_db()
    init_alert_state()
    poll_all_cities()

    scheduler = BlockingScheduler()
    scheduler.add_job(poll_all_cities, "interval", minutes=15)
    print("Scheduler started. Polling every 15 minutes. Press Ctrl+C to stop.")
    scheduler.start()