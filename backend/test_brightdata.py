from brightdata_client import (
    trigger_scraper,
    get_collection_result
)


MEDICINE_URL = (
    "https://pharmeasy.in/online-medicine-order/"
    "p-500-strip-of-15-tablets-3378"
)


print("Starting Bright Data scraper...")

job = trigger_scraper(MEDICINE_URL)

print("Trigger response:")
print(job)


collection_id = job["collection_id"]

print("\nCollection ID:")
print(collection_id)

print("\nWaiting for Bright Data results...")

results = get_collection_result(collection_id)

print("\nScraping completed!")

print("Number of records:", len(results))

print("\nMedicine JSON:")
print(results)