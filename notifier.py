import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    response = requests.get(url, params=params)
    response.raise_for_status()
    print("Alert sent.")

if __name__ == "__main__":
    send_alert("Test alert from AirWatch")