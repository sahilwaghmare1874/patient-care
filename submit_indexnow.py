"""
IndexNow Submission Utility for Bing & Yandex
Pings the IndexNow API to notify search engines of updated public URLs.
"""

import sys
import json
import urllib.request
import urllib.parse

INDEXNOW_KEY = "e4f5a89b71c23d04e5f6a7b8c9d0e1f2"

def submit(host, urls=None):
    if not urls:
        urls = [
            f"https://{host}/",
            f"https://{host}/index.html",
            f"https://{host}/pages/register.html",
            f"https://{host}/pages/login.html"
        ]

    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{host}/{INDEXNOW_KEY}.txt",
        "urlList": urls
    }

    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[SUCCESS] IndexNow submission received by Bing API. HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] IndexNow response: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"[ERROR] IndexNow submission failed: {e}")
        return False

if __name__ == '__main__':
    host_arg = sys.argv[1] if len(sys.argv) > 1 else "patientcare.org"
    # Strip protocol if passed
    host_arg = host_arg.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"Submitting URLs for host: {host_arg} ...")
    submit(host_arg)
