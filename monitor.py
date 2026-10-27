import requests
import time
import logging
import os

def load_urls(path="urls.txt"):
    urls = []
    with open(path) as file:
        for text in file:
            text = text.strip()
            if text and not text.startswith("#"):
                urls.append(text)
    return urls

# How many seconds to wait between check rounds.
# Reads CHECK_INTERVAL from outside (env variable); if not set, uses 60.
# int() converts the text "60" into the number 60.
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Response time (in ms) above which a site is marked SLOW.
# Reads SLOW_THRESHOLD_MS from outside; if not set, uses 2000.
SLOW_THRESHOLD_MS = int(os.getenv("SLOW_THRESHOLD_MS", "2000"))

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def check(url):
    start = time.time()
    try:
        response = requests.get(url, timeout=5)
        ms = round((time.time() - start) * 1000)
        code = response.status_code

        if code >= 500:
            status = "DOWN"
        elif code >= 400:
            status = "ERROR"
        elif ms > SLOW_THRESHOLD_MS:
            status = "SLOW"
        else:
            status = "UP"
        reason = "-"

    except requests.exceptions.RequestException as error:
        ms = "-"
        code = "-"
        status = "DOWN"
        reason = type(error).__name__

    line = f"status={status} code={code} time_ms={ms} url={url} reason={reason}"
    print(line)

    if status == "UP":
        logging.info(line)
    else:
        logging.warning(line)

URLS = load_urls()
print(f"Monitor started with {len(URLS)} URLs. Press Ctrl+C to stop.")
logging.info(f"Monitor started with {len(URLS)} URLs")

try:
    while True:
        for url in URLS:
            check(url)
        print(f"--- sleeping {CHECK_INTERVAL}s ---")
        time.sleep(CHECK_INTERVAL)
except KeyboardInterrupt:
    print("\nMonitor stopped.")
    logging.info("Monitor stopped by user")