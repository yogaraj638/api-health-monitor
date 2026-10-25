import requests
import time

URLS = [
    "https://www.google.com",
    "https://github.com",
    "https://this-site-does-not-exist-12345.com",
]

def check(url):
    start = time.time()
    try:
        response = requests.get(url, timeout=5)
        ms = round((time.time() - start) * 1000)
        print(f"UP    {response.status_code}  {ms}ms  {url}")
    except requests.exceptions.RequestException as error:
        print(f"DOWN  ---  ----   {url}  ({type(error).__name__})")

for url in URLS:
    check(url)