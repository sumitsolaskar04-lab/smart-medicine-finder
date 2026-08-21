from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re
import requests

from medicine_analyzer import process_medicines
from price_tracker import track_price, load_history
from brightdata_client import trigger_scraper, get_collection_result


app = Flask(__name__)

# Allow frontend applications to access this backend
CORS(app)


# OpenStreetMap Overpass API
OVERPASS_URL = "https://overpass-api.de"


def load_medicines():
    file_path = os.path.join("data", "medicines.json")

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        return data.get("medicines", [])

    return data


def save_medicines(medicines_list):
    file_path = os.path.join("data", "medicines.json")

    os.makedirs("data", exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            {"medicines": medicines_list},
            file,
            indent=4
        )


def load_jan_aushadhi():
    file_path = os.path.join("data", "jan_aushadhi.json")

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return []


def normalize_string(text):
    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(
        r'\b(tablets|capsules|ip|bp|usp|sustained release|sr|mg|ml)\b',
        '',
        text
    )

    text = re.sub(r'[^a-z0-9]', '', text)

    return text


def get_price_value(price):
    """
    Safely converts medicine prices from common formats to float.

    Supports:
    - int / float
    - numeric strings such as "14.65"
    - strings such as "₹1,499.00"
    - dictionaries such as {"value": 14.65, "currency": "INR"}
    """

    if isinstance(price, dict):
        return get_price_value(price.get("value", 0))

    if isinstance(price, (int, float)):
        return float(price)

    if isinstance(price, str):
        try:
            cleaned_price = (
                price
                .replace("₹", "")
                .replace(",", "")
                .strip()
            )
            return float(cleaned_price)
        except ValueError:
            return 0.0

    return 0.0


# =========================================================
# EXTRACT MEDICINE STRENGTH
# =========================================================
def extract_strength(text):
    if not text:
        return ""

    match = re.search(
        r'(\d+\s*(mg|ml|mcg|g))',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).replace(" ", "").lower()

    return ""


def calculate_generic_substitution(commercial_med):
    if not commercial_med:
        return None

    composition = (
        commercial_med.get("composition")
        or commercial_med.get("active_ingredient")
        or commercial_med.get("medicine_name", "")
    )

    commercial_price = get_price_value(
        commercial_med.get("mrp")
        or commercial_med.get("price")
        or 0
    )

    if not composition or commercial_price <= 0:
        return None

    norm_composition = normalize_string(composition)

    brand_strength = (
        extract_strength(
            commercial_med.get("medicine_name", "")
        )
        or extract_strength(composition)
    )

    jan_database = load_jan_aushadhi()

    for generic in jan_database:

        ja_salt = (
            generic.get("clean_salt")
            or generic.get("generic_name", "")
        )

        ja_strength = (
            generic.get("strength")
            or extract_strength(
                generic.get("generic_name", "")
            )
        )

        if (
            normalize_string(ja_salt) in norm_composition
            or norm_composition in normalize_string(ja_salt)
        ):

            if (
                not brand_strength
                or brand_strength == ja_strength.lower().replace(" ", "")
            ):

                ja_price = get_price_value(
                    generic.get("mrp", 0)
                )

                if commercial_price > ja_price:

                    savings_amt = commercial_price - ja_price

                    savings_pct = (
                        savings_amt / commercial_price
                    ) * 100

                    return {
                        "has_generic_alternative": True,
                        "generic_brand_name": generic.get(
                            "generic_name"
                        ),
                        "drug_code": generic.get(
                            "drug_code"
                        ),
                        "unit_size": generic.get(
                            "unit_size",
                            "10 Tablets"
                        ),
                        "jan_aushadhi_mrp": ja_price,
                        "money_saved_rupees": round(
                            savings_amt,
                            2
                        ),
                        "savings_percentage": round(
                            savings_pct,
                            1
                        ),
                        "alert_banner_trigger": savings_pct >= 40.0
                    }

    return {
        "has_generic_alternative": False,
        "message": "No cheaper government generic alternative found."
    }


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "service": "Medicine Aggregator, Geolocation Finder & Price Tracker Engine",
        "version": "2.0.0",
        "architecture_type": "Hybrid Online-Offline Mapping",
        "endpoints_available": [
            "GET /api/medicines",
            "GET /api/search?q=<name>",
            "GET /api/medicines/<name>",
            "POST /api/scrape-and-sync",
            "GET /api/medicine-availability-nearby?medicine=<name>&lat=<lat>&lon=<lon>"
        ]
    })


# ---------------------------------------------------------
# GET ALL MEDICINES
# ---------------------------------------------------------

@app.route("/api/medicines")
def get_medicines():

    medicines = load_medicines()

    results = process_medicines(medicines)

    history = load_history()

    for med in results:

        name = med.get(
            "medicine_name",
            ""
        )

        med["savings_alert"] = (
            calculate_generic_substitution(med)
        )

        med["price_history_log"] = history.get(
            name,
            []
        )

    return jsonify({
        "count": len(results),
        "medicines": results
    })


# ---------------------------------------------------------
# SEARCH MEDICINE
# ---------------------------------------------------------

@app.route("/api/search")
def search_medicine():

    query = request.args.get(
        "q",
        ""
    ).strip().lower()

    if not query:

        return jsonify({
            "query": "",
            "count": 0,
            "medicines": []
        })

    medicines = load_medicines()

    results = process_medicines(medicines)

    history = load_history()

    matches = []

    for medicine in results:

        name = medicine.get(
            "medicine_name",
            ""
        ).lower()

        if query in name:

            medicine["savings_alert"] = (
                calculate_generic_substitution(medicine)
            )

            medicine["price_history_log"] = history.get(
                medicine.get("medicine_name"),
                []
            )

            matches.append(medicine)

    return jsonify({
        "query": query,
        "count": len(matches),
        "medicines": matches
    })


# ---------------------------------------------------------
# GET SINGLE MEDICINE
# ---------------------------------------------------------

@app.route("/api/medicines/<path:medicine_name>")
def get_medicine(medicine_name):

    medicines = load_medicines()

    results = process_medicines(medicines)

    history = load_history()

    for medicine in results:

        name = medicine.get(
            "medicine_name",
            ""
        ).lower()

        if name == medicine_name.strip().lower():

            medicine["savings_alert"] = (
                calculate_generic_substitution(medicine)
            )

            medicine["price_history_log"] = history.get(
                medicine.get("medicine_name"),
                []
            )

            return jsonify({
                "status": "success",
                "medicine": medicine
            })

    return jsonify({
        "status": "failed",
        "error": "Medicine not found"
    }), 404


# ---------------------------------------------------------
# BRIGHT DATA SCRAPE AND SYNC
# ---------------------------------------------------------

@app.route("/api/scrape-and-sync", methods=["POST"])
def scrape_and_sync():

    data = request.get_json() or {}

    target_url = data.get("url")

    if not target_url:

        return jsonify({
            "status": "failed",
            "error": "Missing target extraction URL parameter"
        }), 400

    try:

        trigger_res = trigger_scraper(
            target_url
        )

        collection_id = trigger_res.get(
            "collection_id"
        )

        if not collection_id:

            return jsonify({
                "status": "failed",
                "error": "No collection ID returned from scraper client"
            }), 500

        scraped_data_list = get_collection_result(
            collection_id
        )

        current_catalog = load_medicines()

        catalog_updated = False

        sync_summary = []

        for item in scraped_data_list:

            med_name = (
                item.get("name")
                or item.get("medicine_name")
            )

            scraped_price = (
                item.get("price")
                or item.get("mrp")
            )

            composition = (
                item.get("composition")
                or item.get("active_ingredient", "")
            )

            if not med_name or scraped_price is None:
                continue

            # Safely normalize Bright Data price values.
            scraped_price = get_price_value(
                scraped_price
            )

            tracking_metrics = track_price(
                med_name,
                scraped_price
            )

            matched_in_catalog = False

            for med in current_catalog:

                if med.get(
                    "medicine_name",
                    ""
                ).lower() == med_name.lower():

                    med["mrp"] = scraped_price

                    if composition:
                        med["composition"] = composition

                    matched_in_catalog = True

                    catalog_updated = True

                    break

            if not matched_in_catalog:

                current_catalog.append({
                    "medicine_name": med_name,
                    "mrp": scraped_price,
                    "composition": composition
                })

                catalog_updated = True

            sync_summary.append({
                "medicine_name": med_name,
                "price_metrics": tracking_metrics
            })

        if catalog_updated:

            save_medicines(
                current_catalog
            )

        return jsonify({
            "status": "success",
            "message": (
                f"Successfully parsed and tracked "
                f"{len(sync_summary)} items using Bright Data."
            ),
            "updates": sync_summary
        })

    except Exception as e:

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# ---------------------------------------------------------
# NEARBY PHARMACIES
# ---------------------------------------------------------

@app.route(
    "/api/medicine-availability-nearby",
    methods=["GET"]
)
def get_medicine_availability_nearby():

    """
    Finds nearby pharmacies using OpenStreetMap.

    NOTE:
    This endpoint finds nearby pharmacy locations only.
    It does NOT check medicine stock or medicine prices.
    """

    query_medicine = request.args.get(
        "medicine",
        ""
    ).strip()

    lat = request.args.get(
        "lat"
    )

    lon = request.args.get(
        "lon"
    )

    radius = request.args.get(
        "radius",
        3000
    )

    # Validate medicine and location
    if not query_medicine or not lat or not lon:

        return jsonify({
            "status": "failed",
            "error": (
                "Missing required query parameters: "
                "medicine, lat, lon"
            )
        }), 400

    # Convert values
    try:

        lat = float(lat)

        lon = float(lon)

        radius = int(radius)

        if radius <= 0:
            radius = 3000

    except ValueError:

        return jsonify({
            "status": "failed",
            "error": (
                "lat, lon and radius must be valid numbers"
            )
        }), 400

    # OpenStreetMap Overpass query
    overpass_query = f"""
    [out:json];
    (
        node["amenity"="pharmacy"](around:{radius},{lat},{lon});
        way["amenity"="pharmacy"](around:{radius},{lat},{lon});
        relation["amenity"="pharmacy"](around:{radius},{lat},{lon});
    );
    out center;
    """

    try:

        response = requests.post(
            f"{OVERPASS_URL}/api/interpreter",
            data={
                "data": overpass_query
            },
            headers={
                "User-Agent": "SmartMedicineFinder/1.0",
                "Accept": "application/json"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        return jsonify({
            "status": "failed",
            "error": (
                f"Unable to find nearby pharmacies: {str(e)}"
            )
        }), 500

    stores = []

    # Process pharmacy results
    for element in data.get(
        "elements",
        []
    ):

        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name",
            "Unnamed Pharmacy"
        )

        # For nodes
        if (
            "lat" in element
            and "lon" in element
        ):

            store_lat = element["lat"]

            store_lon = element["lon"]

        # For ways/relations
        elif "center" in element:

            store_lat = element["center"].get(
                "lat"
            )

            store_lon = element["center"].get(
                "lon"
            )

        else:

            continue

        if (
            store_lat is None
            or store_lon is None
        ):

            continue

        stores.append({
            "name": name,
            "latitude": store_lat,
            "longitude": store_lon
        })

    return jsonify({
        "status": "success",
        "medicine": query_medicine,
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "radius": radius,
        "stores": stores,
        "count": len(stores)
    })


# ---------------------------------------------------------
# START FLASK SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )