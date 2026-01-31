import requests
from functools import lru_cache
import time

class OpenFIGIService:
    API_URL = "https://api.openfigi.com/v3/mapping"

    def __init__(self, api_key: str):
        self.headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": api_key
        }

    @lru_cache(maxsize=50000)
    def cusip_to_ticker(self, cusip: str) -> str | None:
        payload = [{
            "idType": "ID_CUSIP",
            "idValue": cusip
        }]

        try:
            r = requests.post(self.API_URL, json=payload, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()

            if not data or "data" not in data[0]:
                return None

            # Prefer US common stock
            for item in data[0]["data"]:
                if item.get("securityType") == "Common Stock":
                    return item.get("ticker")

            # fallback
            return data[0]["data"][0].get("ticker")

        except Exception:
            return None
        
    def batch_cusip_to_ticker(self, cusips: list[str]) -> dict[str, str]:
        result = {}

        BATCH_SIZE = 10
        MAX_RETRIES = 5

        for i in range(0, len(cusips), BATCH_SIZE):
            batch = cusips[i:i + BATCH_SIZE]
            payload = [{"idType": "ID_CUSIP", "idValue": c} for c in batch]

            for attempt in range(MAX_RETRIES):
                r = requests.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=15
                )

                if r.status_code == 429:
                    retry_after = int(r.headers.get("Retry-After", 2))
                    time.sleep(retry_after)
                    continue

                r.raise_for_status()
                break
            else:
                # Give up on this batch
                continue

            for cusip, item in zip(batch, r.json()):
                if item.get("data"):
                    result[cusip] = item["data"][0].get("ticker")

            # 🔑 throttle between successful requests
            time.sleep(0.35)

        return result
