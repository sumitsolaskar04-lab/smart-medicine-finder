from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re
import requests
import random
from urllib.parse import quote

from medicine_analyzer import process_medicines
from price_tracker import track_price, load_history
from brightdata_client import trigger_scraper, get_collection_result

app = Flask(__name__)
CORS(app)

# OpenStreetMap Overpass API endpoint
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
    """
    Saves or updates the primary local commercial medicine inventory cache.
    """
    file_path = os.path.join("data", "medicines.json")
    os.makedirs("data", exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump({"medicines": medicines_list}, file, indent=4)


def load_jan_aushadhi():
    """
    Loads the government Jan Aushadhi generic catalog.
    """
    file_path = os.path.join("data", "jan_aushadhi.json")

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def normalize_string(text):
    """
    Strips noise characters and formatting words to maximize match accuracy.
    """
    if not text:
        return ""

    text = str(text).lower().strip()

    text = re.sub(
        r'\b(tablets|capsules|ip|bp|usp|sustained release|sr|mg|ml)\b',
        '',
        text
    )

    text = re.sub(r'[^a-z0-9]', '', text)

    return text


def extract_strength(text):
    """
    Extracts explicit dosage patterns from product naming text strings.
    """
    if not text:
        return ""

    match = re.search(
        r'(\d+\s*(mg|ml|mcg|g))',
        str(text),
        re.IGNORECASE
    )

    return match.group(1).replace(" ", "").lower() if match else ""


def calculate_generic_substitution(commercial_med):
    """
    Evaluates cross-dataset chemical matches and calculates target financial savings metrics.
    """
    if not commercial_med:
        return None

    composition = (
        commercial_med.get("composition")
        or commercial_med.get("active_ingredient")
        or commercial_med.get("medicine_name", "")
    )

    try:
        commercial_price = float(
            commercial_med.get("mrp")
            or commercial_med.get("price")
            or 0
        )
    except (ValueError, TypeError):
        commercial_price = 0

    if not composition or commercial_price <= 0:
        return None

    norm_composition = normalize_string(composition)

    brand_strength = (
        extract_strength(commercial_med.get("medicine_name", ""))
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
            or extract_strength(generic.get("generic_name", ""))
        )

        if (
            normalize_string(ja_salt) in norm_composition
            or norm_composition in normalize_string(ja_salt)
        ):
            if (
                not brand_strength
                or brand_strength == ja_strength.lower().replace(" ", "")
            ):
                try:
                    ja_price = float(generic.get("mrp", 0))
                except (ValueError, TypeError):
                    ja_price = 0

                if commercial_price > ja_price:
                    savings_amt = commercial_price - ja_price
                    savings_pct = (
                        savings_amt / commercial_price
                    ) * 100

                    return {
                        "has_generic_alternative": True,
                        "generic_brand_name": generic.get("generic_name"),
                        "drug_code": generic.get("drug_code"),
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


def extract_scraped_price(price_data):
    """
    Bright Data may return price as:
    {"value": 15.9, "currency": "INR", "symbol": "₹"}

    This function safely extracts the numeric price.
    """

    if isinstance(price_data, dict):
        value = price_data.get("value")

        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    try:
        return float(price_data)
    except (ValueError, TypeError):
        return 0


def scrape_from_apollo(query):
    """
    Searches Apollo Pharmacy dynamically using Bright Data.
    """

    encoded_query = quote(query.strip())

    apollo_url = (
        "https://www.apollopharmacy.in/search-medicines/"
        + encoded_query
    )

    trigger_res = trigger_scraper(apollo_url)

    collection_id = trigger_res.get("collection_id")

    if not collection_id:
        raise Exception(
            "Bright Data did not return a collection ID."
        )

    scraped_data = get_collection_result(collection_id)

    if not scraped_data:
        return []

    if isinstance(scraped_data, dict):
        scraped_data = [scraped_data]

    results = []

    for item in scraped_data:
        if not isinstance(item, dict):
            continue

        name = (
            item.get("name")
            or item.get("medicine_name")
        )

        price = extract_scraped_price(
            item.get("price")
            or item.get("mrp")
        )

        package_size = item.get("composition", "")

        if not name or price <= 0:
            continue

        results.append({
            "medicine_name": name,
            "mrp": price,
            "price": price,
            "package_size": package_size,
            "source": "Apollo Pharmacy",
            "source_url": apollo_url
        })

    return results


@app.route("/")
def home():
    """
    Pure Backend Health Status Check Endpoint
    """
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


@app.route("/api/medicines")
def get_medicines():
    medicines = load_medicines()

    results = process_medicines(medicines)
    history = load_history()

    for med in results:
        name = med.get("medicine_name", "")

        med["savings_alert"] = calculate_generic_substitution(
            med
        )

        med["price_history_log"] = history.get(
            name,
            []
        )

    return jsonify({
        "count": len(results),
        "medicines": results
    })


@app.route("/api/search")
def search_medicine():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "query": "",
            "count": 0,
            "medicines": []
        })

    # ---------------------------------------------------------
    # STEP 1: Search existing local medicines.json
    # ---------------------------------------------------------

    medicines = load_medicines()

    results = process_medicines(medicines)

    history = load_history()

    matches = []

    query_lower = query.lower()

    for medicine in results:

        name = medicine.get(
            "medicine_name",
            ""
        ).lower()

        if query_lower in name:

            medicine["savings_alert"] = (
                calculate_generic_substitution(
                    medicine
                )
            )

            medicine["price_history_log"] = history.get(
                medicine.get("medicine_name"),
                []
            )

            matches.append(medicine)

    # ---------------------------------------------------------
    # STEP 2: If local JSON has results, return them
    # ---------------------------------------------------------

    if matches:

        return jsonify({
            "query": query,
            "count": len(matches),
            "source": "local",
            "medicines": matches
        })

    # ---------------------------------------------------------
    # STEP 3: Medicine not found locally
    # Search Apollo Pharmacy using Bright Data
    # ---------------------------------------------------------

    try:

        scraped_results = scrape_from_apollo(query)

        if not scraped_results:

            return jsonify({
                "query": query,
                "count": 0,
                "source": "apollo_pharmacy",
                "medicines": []
            })

        # -----------------------------------------------------
        # STEP 4: Save newly discovered medicines locally
        # -----------------------------------------------------

        current_catalog = load_medicines()

        existing_names = {
            str(med.get("medicine_name", "")).lower()
            for med in current_catalog
        }

        for scraped in scraped_results:

            name = scraped.get(
                "medicine_name",
                ""
            )

            if name.lower() not in existing_names:

                current_catalog.append({
                    "medicine_name": name,
                    "mrp": scraped.get("mrp", 0),
                    "price": scraped.get("price", 0),
                    "package_size": scraped.get(
                        "package_size",
                        ""
                    )
                })

                existing_names.add(
                    name.lower()
                )

        save_medicines(current_catalog)

        # -----------------------------------------------------
        # STEP 5: Prepare response for frontend
        # -----------------------------------------------------

        final_results = []

        for medicine in scraped_results:

            medicine["savings_alert"] = (
                calculate_generic_substitution(
                    medicine
                )
            )

            medicine["price_history_log"] = (
                history.get(
                    medicine.get(
                        "medicine_name"
                    ),
                    []
                )
            )

            final_results.append(medicine)

        return jsonify({
            "query": query,
            "count": len(final_results),
            "source": "apollo_pharmacy",
            "medicines": final_results
        })

    except Exception as e:

        print(
            "Bright Data search error:",
            str(e)
        )

        return jsonify({
            "query": query,
            "count": 0,
            "source": "apollo_pharmacy",
            "medicines": [],
            "error": str(e)
        }), 500


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
                calculate_generic_substitution(
                    medicine
                )
            )

            medicine["price_history_log"] = (
                history.get(
                    medicine.get(
                        "medicine_name"
                    ),
                    []
                )
            )

            return jsonify({
                "status": "success",
                "medicine": medicine
            })

    return jsonify({
        "status": "failed",
        "error": "Medicine not found"
    }), 404


@app.route("/api/scrape-and-sync", methods=["POST"])
def scrape_and_sync():
    """
    On-Demand Scraper Pipeline using Bright Data.
    Acts as the master repository builder to populate medicine definitions and baseline prices.
    """

    data = request.get_json() or {}

    target_url = data.get("url")

    if not target_url:
        return jsonify({
            "status": "failed",
            "error": "Missing target extraction URL parameter"
        }), 400

    try:

        trigger_res = trigger_scraper(target_url)

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

            scraped_price = extract_scraped_price(
                item.get("price")
                or item.get("mrp")
            )

            composition = (
                item.get("composition")
                or item.get("active_ingredient", "")
            )

            if not med_name or scraped_price <= 0:
                continue

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
                    med["price"] = scraped_price

                    if composition:
                        med["composition"] = composition

                    matched_in_catalog = True
                    catalog_updated = True

                    break

            if not matched_in_catalog:

                current_catalog.append({
                    "medicine_name": med_name,
                    "mrp": scraped_price,
                    "price": scraped_price,
                    "composition": composition
                })

                catalog_updated = True

            sync_summary.append({
                "medicine_name": med_name,
                "price_metrics": tracking_metrics
            })

        if catalog_updated:
            save_medicines(current_catalog)

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


@app.route(
    "/api/medicine-availability-nearby",
    methods=["GET"]
)
def get_medicine_availability_nearby():

    """
    Finds real offline storefronts within a radius,
    evaluates their pricing, cross-references the
    Jan Aushadhi substitution dataset, and sorts from
    cheapest to dearest.
    """

    query_medicine = request.args.get(
        "medicine",
        ""
    ).strip().lower()

    lat = request.args.get("lat")
    lon = request.args.get("lon")

    radius = request.args.get(
        "radius",
        3000
    )

    if not query_medicine or not lat or not lon:

        return jsonify({
            "status": "failed",
            "error": (
                "Missing required query parameters: "
                "medicine, lat, lon"
            )
        }), 400


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )