import requests
import time
import logging

URLS = [
    "https://www.google.com",
    "https://github.com",
    "https://httpbin.org/status/500",
    "https://this-site-does-not-exist-12345.com",
]

CHECK_INTERVAL = 60        # seconds between rounds
SLOW_THRESHOLD_MS = 2000   # slower than this = SLOW

logging.basicConfig(
    filename="monitor.log",
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

print("Monitor started. Press Ctrl+C to stop.")
while True:
    for url in URLS:
        check(url)
    print(f"--- sleeping {CHECK_INTERVAL}s ---")
    time.sleep(CHECK_INTERVAL)