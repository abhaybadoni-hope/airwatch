import os
import logging
import requests
import json
import redis
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


cache = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), decode_responses=True)
CACHE_TTL = 900  # 15 minutes in seconds

load_dotenv()  # reads your .env file
API_KEY = os.getenv("OPENWEATHER_API_KEY")

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True
)
def _fetch_aqi_from_api(lat, lon):
    # ... your existing fetch body stays exactly the same ...
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": API_KEY}
    logger.info(f"Fetching AQI for ({lat}, {lon})")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    aqi = data["list"][0]["main"]["aqi"]
    components = data["list"][0]["components"]
    return {"aqi": aqi, "pm25": components["pm2_5"], "pm10": components["pm10"]}


def fetch_aqi(lat, lon):
    cache_key = f"aqi:{lat}:{lon}"

    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Cache HIT for ({lat}, {lon})")
        return json.loads(cached)

    logger.info(f"Cache MISS for ({lat}, {lon}) — calling API")
    reading = _fetch_aqi_from_api(lat, lon)
    cache.setex(cache_key, CACHE_TTL, json.dumps(reading))
    return reading

if __name__ == "__main__":
    from database import init_db, save_reading

    init_db()
    reading = fetch_aqi(28.6139, 77.2090)
    save_reading("Delhi", reading["aqi"], reading["pm25"], reading["pm10"])