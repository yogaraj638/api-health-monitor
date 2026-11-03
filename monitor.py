import requests
import time
import logging
import os
import signal
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()  # load settings from .env (if the file exists)

# ---------- Settings (from environment, with defaults) ----------
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))        # seconds between rounds
SLOW_THRESHOLD_MS = int(os.getenv("SLOW_THRESHOLD_MS", "2000"))  # slower = SLOW
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))                    # dashboard port
RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() == "true"      # one round, then exit

# ---------- Logging ----------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def load_urls(path="urls.txt"):
    """Read URLs from a file, skipping blank lines and # comments."""
    urls = []
    with open(path) as file:
        for text in file:
            text = text.strip()
            if text and not text.startswith("#"):
                urls.append(text)
    return urls


def check(url):
    """Check one URL, log the result, and return it as a dictionary."""
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
        ms, code, status = "-", "-", "DOWN"
        reason = type(error).__name__

    line = f"status={status} code={code} time_ms={ms} url={url} reason={reason}"
    print(line)
    if status == "UP":
        logging.info(line)
    else:
        logging.warning(line)

    return {"status": status, "code": code, "ms": ms, "url": url, "reason": reason}


def write_dashboard(results):
    """Fill the HTML template with results and save public/index.html."""
    counts = {"UP": 0, "SLOW": 0, "ERROR": 0, "DOWN": 0}
    rows = ""
    for r in results:
        counts[r["status"]] += 1
        rows += (
            f"<tr><td class='{r['status']}'>{r['status']}</td>"
            f"<td>{r['url']}</td><td>{r['code']}</td>"
            f"<td>{r['ms']}</td><td>{r['reason']}</td></tr>\n"
        )

    with open("dashboard_template.html") as file:
        html = file.read()

    html = html.replace("__ROWS__", rows)
    for name in counts:
        html = html.replace(f"__{name}__", str(counts[name]))
    html = html.replace("__REFRESH__", str(CHECK_INTERVAL))
    html = html.replace("__CHECKED_AT__", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()))

    with open("public/index.html", "w") as file:
        file.write(html)


def run_round(urls):
    """Check every URL once, then rebuild the dashboard."""
    results = []
    for url in urls:
        results.append(check(url))
    write_dashboard(results)


def start_web_server():
    """Serve the public/ folder at http://localhost:WEB_PORT in the background."""
    handler = partial(SimpleHTTPRequestHandler, directory="public")
    server = HTTPServer(("0.0.0.0", WEB_PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Dashboard running at http://localhost:{WEB_PORT}")


def handle_stop(signum, frame):
    """Treat SIGTERM (docker stop) like Ctrl+C for a clean shutdown."""
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, handle_stop)

# ---------- Main ----------
URLS = load_urls()
os.makedirs("public", exist_ok=True)

if RUN_ONCE:
    # Used by GitHub Actions: one round, write the page, exit.
    run_round(URLS)
else:
    start_web_server()
    print(f"Monitor started with {len(URLS)} URLs.")
    logging.info(f"Monitor started with {len(URLS)} URLs")
    try:
        while True:
            run_round(URLS)
            print(f"--- sleeping {CHECK_INTERVAL}s ---")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
        logging.info("Monitor stopped by user")