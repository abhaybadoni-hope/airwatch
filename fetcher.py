import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads your .env file
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def fetch_aqi(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": API_KEY}
    response = requests.get(url, params=params)
    response.raise_for_status()  # crashes loudly if the API returns an error
    data = response.json()

    # dig the useful bits out of the response
    aqi = data["list"][0]["main"]["aqi"]          # a number 1–5
    components = data["list"][0]["components"]     # pm2_5, pm10, etc.
    return {
        "aqi": aqi,
        "pm25": components["pm2_5"],
        "pm10": components["pm10"],
    }

if __name__ == "__main__":
    from database import init_db, save_reading

    init_db()
    reading = fetch_aqi(28.6139, 77.2090)
    save_reading("Delhi", reading["aqi"], reading["pm25"], reading["pm10"])