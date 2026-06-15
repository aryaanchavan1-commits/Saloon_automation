"""
Keep Awake script for Streamlit Cloud.
Deploy as a separate service (e.g., cron job, UptimeRobot, or Kaffeine)
to ping the app every 10-15 minutes and prevent it from sleeping.
"""

import requests
import time
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def ping_app(app_url: str, interval: int = 600):
    """
    Ping the Streamlit Cloud app every `interval` seconds.

    Args:
        app_url: Your Streamlit Cloud app URL (e.g., https://your-app.streamlit.app)
        interval: Seconds between pings (default 600 = 10 min)
    """
    logging.info(f"Keep Awake started — pinging {app_url} every {interval}s")
    while True:
        try:
            r = requests.get(app_url, timeout=30)
            logging.info(f"Pinged {app_url} → status {r.status_code}")
        except Exception as e:
            logging.warning(f"Ping failed: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python keep_awake.py <STREAMLIT_APP_URL> [interval_seconds]")
        print("Example: python keep_awake.py https://saloon-pro.streamlit.app 600")
        sys.exit(1)

    url = sys.argv[1].rstrip("/")
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    ping_app(url, interval)
