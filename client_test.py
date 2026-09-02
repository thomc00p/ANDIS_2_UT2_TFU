import urllib.request
import json
import time
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost/process"
HEADERS = {
    "Authorization": "Bearer TFU-UT2-SECRET-KEY",
    "Content-Type": "application/json"
}
DATA = json.dumps({
    "item_id": 101,
    "name": "ResilienceTest"
}).encode()

def request_with_retry(req_id):
    attempts = 3
    for i in range(attempts):
        try:
            req = urllib.request.Request(URL, data=DATA, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=1) as resp:
                result = json.loads(resp.read().decode())
                print(f"[Req {req_id:03d}] Success: {result['processed_by']}")
                return True
        except Exception as e:
            print(f"[Req {req_id:03d}] Attempt {i+1} failed ({e}). Retrying in 1s...")
            time.sleep(1)
    print(f"[Req {req_id:03d}] CRITICAL FAILURE after all attempts.")
    return False

if __name__ == "__main__":
    print("Starting concurrent load test (100 requests, 10 workers)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(request_with_retry, range(100)))

    success_rate = (sum(results) / len(results)) * 100
    print(f"\nFinal Success Rate: {success_rate}%")
