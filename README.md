# api-health-monitor

# API Health Monitor

A Python tool that checks websites and APIs every 60 seconds and logs whether each one is up, slow, or failing.

I built this from my experience in technical support, where the first question in many tickets is "Is the service actually down, or is it only this customer?" This tool answers that automatically and keeps a history of every check.

## Features
- Checks a list of URLs continuously (every 60 seconds, configurable)
- Classifies each result into 4 health levels:
  - **UP**: responded with 2xx
  - **SLOW**: responded, but slower than 2000 ms
  - **ERROR**: 4xx client errors (e.g. 404 Not Found)
  - **DOWN**: 5xx server errors, timeouts, or connection/DNS failures
- Records the failure reason (e.g. `ReadTimeout`, `ConnectionError`)
- Writes structured `key=value` logs with timestamps to `monitor.log`
- URLs are configured in `urls.txt`, with no code changes needed
- Clean shutdown with Ctrl+C

## How to run
```bash
git clone https://github.com/yogaraj638/api-health-monitor.git
cd api-health-monitor
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python monitor.py
```
Edit `urls.txt` to choose which sites to monitor.

## Example output
```
2026-10-27 15:56:23,122 INFO Monitor started with 10 URLs
2026-10-27 15:56:24,194 INFO status=UP code=200 time_ms=1071 url=https://www.google.com reason=-
2026-10-27 15:56:34,438 WARNING status=SLOW code=200 time_ms=4673 url=https://httpbin.org/delay/3 reason=-
2026-10-27 15:56:29,764 WARNING status=ERROR code=404 time_ms=1526 url=https://httpbin.org/status/404 reason=-
2026-10-27 15:56:28,235 WARNING status=DOWN code=500 time_ms=1664 url=https://httpbin.org/status/500 reason=-
2026-10-27 15:56:40,702 WARNING status=DOWN code=- time_ms=- url=https://httpbin.org/delay/10 reason=ReadTimeout
2026-10-27 15:56:40,806 WARNING status=DOWN code=- time_ms=- url=https://this-site-does-not-exist-12345.com reason=ConnectionError
```

## What I learned
- How HTTP status code families map to health: 4xx is a client-side problem, 5xx is a server-side problem, the same triage logic I use in support
- Why timeouts matter: without one, a single dead server can freeze the whole monitor
- Response time is more than server time: `/delay/3` took around 4,600 ms because DNS lookup, the TLS handshake and network distance add to the server's 3-second wait
- Python basics in practice: functions, try/except error handling, file reading, and the logging module

## Roadmap
- [x] Run in Docker
- [ ] Deploy on AWS EC2 with Terraform
- [ ] Send logs to CloudWatch
- [ ] Email alerts when a site goes DOWN
- [ ] CI/CD with GitHub Actions

