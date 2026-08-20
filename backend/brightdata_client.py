import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BRIGHTDATA_API_TOKEN = os.getenv("BRIGHTDATA_API_TOKEN")
BRIGHTDATA_COLLECTOR_ID = os.getenv("BRIGHTDATA_COLLECTOR_ID")

TRIGGER_URL = "https://api.brightdata.com/dca/trigger"
DATASET_URL = "https://api.brightdata.com/dca/dataset"


def trigger_scraper(url):

    if not BRIGHTDATA_API_TOKEN:
        raise RuntimeError("BRIGHTDATA_API_TOKEN is missing")

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "url": url
        }
    ]

    params = {
        "collector": BRIGHTDATA_COLLECTOR_ID,
        "queue_next": 1
    }

    response = requests.post(
        TRIGGER_URL,
        params=params,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_collection_result(collection_id, max_attempts=30):

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_attempts):

        response = requests.get(
            DATASET_URL,
            params={"id": collection_id},
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        # Collection is ready
        if isinstance(data, list):
            return data

        # Collection is still running
        status = data.get("status")

        if status in ("building", "collecting"):
            print(
                f"Collection still running ({status}). "
                f"Attempt {attempt + 1}/{max_attempts}"
            )

            time.sleep(5)
            continue

        # Unexpected response
        raise RuntimeError(
            f"Unexpected Bright Data response: {data}"
        )

    raise TimeoutError(
        "Bright Data collection did not finish in time."
    )

def trigger_multiple_scrapers(urls):

    if not BRIGHTDATA_API_TOKEN:
        raise RuntimeError("BRIGHTDATA_API_TOKEN is missing")

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "url": url
        }
        for url in urls
    ]

    params = {
        "collector": BRIGHTDATA_COLLECTOR_ID,
        "queue_next": 1
    }

    response = requests.post(
        TRIGGER_URL,
        params=params,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()