from flask import Flask, jsonify, request
from flask_cors import CORS

import json
import os
import re
import requests

from medicine_analyzer import process_medicines
from price_tracker import track_price, load_history

from brightdata_client import (
    trigger_scraper,
    get_collection_result,
    trigger_multiple_scrapers
)


app = Flask(__name__)

# Allow frontend applications to access this backend
CORS(app)


# =========================================================
# CONFIGURATION
# =========================================================

OVERPASS_URL = "https://overpass-api.de"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = "SmartMedicineFinder/1.0"

# Get the folder where app.py is located.
# This prevents path problems when Flask is started
# from a different working directory.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# =========================================================
# EXISTING MEDICINES.JSON
# =========================================================

def load_medicines():

    file_path = os.path.join(
        DATA_DIR,
        "medicines.json"
    )

    if not os.path.exists(file_path):

        return []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except Exception as e:

        print(
            "Error loading medicines.json:",
            e
        )

        return []

    if isinstance(data, dict):

        return data.get(
            "medicines",
            []
        )

    return data


def save_medicines(
    medicines_list
):

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    file_path = os.path.join(
        DATA_DIR,
        "medicines.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "medicines": medicines_list
            },
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# LARGE INDIAN MEDICINE DATASET
# =========================================================

INDIAN_MEDICINE_DATA = None


def load_indian_medicine_data():

    global INDIAN_MEDICINE_DATA

    # -----------------------------------------------------
    # IMPORTANT:
    # If dataset has already been loaded,
    # do NOT load it again.
    # -----------------------------------------------------

    if INDIAN_MEDICINE_DATA is not None:

        return INDIAN_MEDICINE_DATA

    file_path = os.path.join(
        DATA_DIR,
        "indian_medicine_data.json"
    )

    if not os.path.exists(file_path):

        print(
            "ERROR: indian_medicine_data.json not found."
        )

        print(
            "Expected location:",
            file_path
        )

        INDIAN_MEDICINE_DATA = []

        return INDIAN_MEDICINE_DATA

    try:

        print(
            "Loading Indian medicine dataset..."
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        # Dataset should be a JSON array.
        if isinstance(
            data,
            list
        ):

            INDIAN_MEDICINE_DATA = data

        elif isinstance(
            data,
            dict
        ):

            # Safety in case JSON is wrapped
            # inside a dictionary.
            INDIAN_MEDICINE_DATA = (
                data.get(
                    "medicines",
                    []
                )
            )

        else:

            INDIAN_MEDICINE_DATA = []

        print(
            f"Loaded "
            f"{len(INDIAN_MEDICINE_DATA):,} "
            "medicine records."
        )

    except Exception as e:

        print(
            "Failed to load Indian medicine dataset:",
            e
        )

        INDIAN_MEDICINE_DATA = []

    return INDIAN_MEDICINE_DATA


# =========================================================
# SEARCH LARGE INDIAN MEDICINE DATASET
# =========================================================

def search_indian_medicines(
    query,
    limit=50
):

    dataset = load_indian_medicine_data()

    query = str(
        query
    ).strip().lower()

    if not query:

        return []

    matches = []

    # -----------------------------------------------------
    # SEARCH ALL 253,973 CACHED RECORDS
    # -----------------------------------------------------

    for item in dataset:

        if not isinstance(
            item,
            dict
        ):

            continue

        name = str(
            item.get(
                "name",
                ""
            )
        ).lower()

        composition1 = str(
            item.get(
                "short_composition1",
                ""
            )
        ).lower()

        composition2 = str(
            item.get(
                "short_composition2",
                ""
            )
        ).lower()

        # -------------------------------------------------
        # SEARCH BY:
        # 1. Medicine name
        # 2. Composition 1
        # 3. Composition 2
        # -------------------------------------------------

        if not (
            query in name
            or
            query in composition1
            or
            query in composition2
        ):

            continue

        # -------------------------------------------------
        # BUILD COMPOSITION
        # -------------------------------------------------

        composition_parts = []

        if item.get(
            "short_composition1"
        ):

            composition_parts.append(
                str(
                    item.get(
                        "short_composition1"
                    )
                )
            )

        if item.get(
            "short_composition2"
        ):

            composition_parts.append(
                str(
                    item.get(
                        "short_composition2"
                    )
                )
            )

        composition = " + ".join(
            composition_parts
        )

        # -------------------------------------------------
        # GET PRICE
        # -------------------------------------------------

        raw_price = item.get(
            "price(₹)",
            0
        )

        try:

            price = float(
                raw_price
            )

        except (
            TypeError,
            ValueError
        ):

            price = 0

        # -------------------------------------------------
        # CONVERT DATASET FORMAT
        # INTO YOUR PROJECT FORMAT
        # -------------------------------------------------

        medicine = {

            "medicine_name": item.get(
                "name",
                ""
            ),

            "mrp": price,

            "price": price,

            "manufacturer": item.get(
                "manufacturer_name",
                ""
            ),

            "composition": composition,

            "pack_size": item.get(
                "pack_size_label",
                ""
            ),

            "type": item.get(
                "type",
                ""
            ),

            "discontinued": item.get(
                "Is_discontinued",
                False
            ),

            "dataset_id": item.get(
                "id"
            )
        }

        matches.append(
            medicine
        )

        # -------------------------------------------------
        # DO NOT SEND THOUSANDS OF RECORDS
        # TO FRONTEND
        # -------------------------------------------------

        if len(matches) >= limit:

            break

    return matches


# =========================================================
# JAN AUSHADHI
# =========================================================

JAN_AUSHADHI_DATA = None


def load_jan_aushadhi():

    global JAN_AUSHADHI_DATA

    # Load only once
    if JAN_AUSHADHI_DATA is not None:

        return JAN_AUSHADHI_DATA

    file_path = os.path.join(
        DATA_DIR,
        "jan_aushadhi.json"
    )

    if not os.path.exists(file_path):

        JAN_AUSHADHI_DATA = []

        return JAN_AUSHADHI_DATA

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            list
        ):

            JAN_AUSHADHI_DATA = data

        elif isinstance(
            data,
            dict
        ):

            JAN_AUSHADHI_DATA = data.get(
                "medicines",
                []
            )

        else:

            JAN_AUSHADHI_DATA = []

    except Exception as e:

        print(
            "Error loading Jan Aushadhi data:",
            e
        )

        JAN_AUSHADHI_DATA = []

    return JAN_AUSHADHI_DATA


# =========================================================
# STRING HELPERS
# =========================================================

def normalize_string(
    text
):

    if not text:

        return ""

    text = str(
        text
    ).lower().strip()

    text = re.sub(
        r"\b(tablets|capsules|tablet|capsule|ip|bp|usp|"
        r"sustained release|sr|mg|ml|mcg|g)\b",
        "",
        text
    )

    text = re.sub(
        r"[^a-z0-9]",
        "",
        text
    )

    return text


def extract_strength(
    text
):

    if not text:

        return ""

    match = re.search(
        r"(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))",
        str(text),
        re.IGNORECASE
    )

    if match:

        return match.group(
            1
        ).replace(
            " ",
            ""
        ).lower()

    return ""


# =========================================================
# GENERIC SUBSTITUTION
# =========================================================

def calculate_generic_substitution(
    commercial_med
):

    if not commercial_med:

        return None

    composition = (

        commercial_med.get(
            "composition"
        )

        or

        commercial_med.get(
            "active_ingredient"
        )

        or

        commercial_med.get(
            "medicine_name",
            ""
        )
    )

    try:

        commercial_price = float(

            commercial_med.get(
                "mrp"
            )

            or

            commercial_med.get(
                "price"
            )

            or

            0
        )

    except (
        TypeError,
        ValueError
    ):

        commercial_price = 0

    if (
        not composition
        or
        commercial_price <= 0
    ):

        return None

    norm_composition = normalize_string(
        composition
    )

    brand_strength = (

        extract_strength(
            commercial_med.get(
                "medicine_name",
                ""
            )
        )

        or

        extract_strength(
            composition
        )
    )

    jan_database = load_jan_aushadhi()

    for generic in jan_database:

        if not isinstance(
            generic,
            dict
        ):

            continue

        ja_salt = (

            generic.get(
                "clean_salt"
            )

            or

            generic.get(
                "generic_name",
                ""
            )
        )

        ja_strength = (

            generic.get(
                "strength"
            )

            or

            extract_strength(
                generic.get(
                    "generic_name",
                    ""
                )
            )
        )

        normalized_ja_salt = normalize_string(
            ja_salt
        )

        if not normalized_ja_salt:

            continue

        composition_matches = (

            normalized_ja_salt
            in
            norm_composition

            or

            norm_composition
            in
            normalized_ja_salt
        )

        if not composition_matches:

            continue

        normalized_ja_strength = (

            str(
                ja_strength
            )
            .lower()
            .replace(
                " ",
                ""
            )
        )

        if (
            brand_strength
            and
            brand_strength
            !=
            normalized_ja_strength
        ):

            continue

        try:

            ja_price = float(
                generic.get(
                    "mrp",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            ja_price = 0

        if ja_price <= 0:

            continue

        if commercial_price > ja_price:

            savings_amt = (
                commercial_price
                -
                ja_price
            )

            savings_pct = (
                savings_amt
                /
                commercial_price
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

                "alert_banner_trigger": (
                    savings_pct >= 40.0
                )
            }

    return {

        "has_generic_alternative": False,

        "message": (
            "No cheaper government generic "
            "alternative found."
        )
    }


# =========================================================
# ENRICH MEDICINE
# =========================================================

def enrich_medicine(
    medicine
):

    medicine_copy = dict(
        medicine
    )

    medicine_copy[
        "savings_alert"
    ] = calculate_generic_substitution(
        medicine_copy
    )

    history = load_history()

    medicine_name = medicine_copy.get(
        "medicine_name",
        ""
    )

    medicine_copy[
        "price_history_log"
    ] = history.get(
        medicine_name,
        []
    )

    return medicine_copy


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({

        "status": "online",

        "service": (
            "Medicine Aggregator, "
            "Offline Pharmacy Finder, "
            "Geolocation Finder & "
            "Price Tracker Engine"
        ),

        "version": "4.0.0",

        "architecture_type": (
            "Large Indian Medicine Dataset Search + "
            "Offline Pharmacy Discovery + "
            "Bright Data Enrichment"
        ),

        "endpoints_available": [

            "GET /api/medicines",

            "GET /api/search?q=<name>",

            "GET /api/search?q=<name>&lat=<lat>&lon=<lon>",

            "GET /api/medicines/<name>",

            "POST /api/scrape-and-sync",

            (
                "GET /api/medicine-availability-nearby"
                "?medicine=<name>"
                "&lat=<lat>"
                "&lon=<lon>"
                "&radius=<radius>"
            )
        ]
    })


# =========================================================
# GET EXISTING MEDICINES.JSON
# =========================================================

@app.route(
    "/api/medicines",
    methods=["GET"]
)
def get_medicines():

    medicines = load_medicines()

    results = process_medicines(
        medicines
    )

    results = [
        enrich_medicine(
            medicine
        )
        for medicine in results
    ]

    return jsonify({

        "count": len(
            results
        ),

        "medicines": results
    })


# =========================================================
# SEARCH MEDICINE + OFFLINE STORES
# =========================================================

@app.route(
    "/api/search",
    methods=["GET"]
)
def search_medicine():

    original_query = request.args.get(
        "q",
        ""
    ).strip()

    # -----------------------------------------------------
    # EMPTY QUERY
    # -----------------------------------------------------

    if not original_query:

        return jsonify({

            "status": "success",

            "query": "",

            "medicine_query": "",

            "location": {

                "latitude": None,

                "longitude": None
            },

            "medicine_count": 0,

            "medicines": [],

            "offline_store_count": 0,

            "offline_stores": [],

            "stock_verified": False
        })


    # =====================================================
    # GET LOCATION PARAMETERS
    # =====================================================

    lat = request.args.get(
        "lat"
    )

    lon = request.args.get(
        "lon"
    )

    radius = request.args.get(
        "radius",
        "3000"
    )


    # =====================================================
    # SEPARATE MEDICINE FROM LOCATION
    # =====================================================

    medicine_query = original_query

    location_query = ""

    words = original_query.split()

    common_location_words = [

        "pune",

        "mumbai",

        "delhi",

        "nashik",

        "nagpur",

        "thane",

        "kolhapur",

        "satara",

        "aurangabad",

        "hyderabad",

        "bangalore",

        "bengaluru",

        "chennai",

        "kolkata",

        "ahmedabad",

        "pimpri",

        "chinchwad"
    ]

    if len(words) >= 2:

        medicine_words = []

        location_words = []

        for word in words:

            if word.lower() in common_location_words:

                location_words.append(
                    word
                )

            else:

                medicine_words.append(
                    word
                )

        if location_words:

            medicine_query = " ".join(
                medicine_words
            )

            location_query = " ".join(
                location_words
            )


    # =====================================================
    # IMPORTANT:
    # SEARCH THE LARGE 253,973 MEDICINE DATASET
    #
    # NOT medicines.json
    # =====================================================

    matches = search_indian_medicines(
        medicine_query,
        limit=50
    )

    # -----------------------------------------------------
    # ENRICH ONLY THE 50 MATCHING RESULTS
    # -----------------------------------------------------

    enriched_matches = []

    for medicine in matches:

        enriched_matches.append(
            enrich_medicine(
                medicine
            )
        )

    matches = enriched_matches


    # =====================================================
    # LOCATION
    # =====================================================

    if not lat or not lon:

        if location_query:

            coordinates = geocode_location(
                location_query
            )

            if coordinates:

                lat = coordinates[
                    "latitude"
                ]

                lon = coordinates[
                    "longitude"
                ]


    # =====================================================
    # OFFLINE PHARMACIES
    # =====================================================

    offline_stores = []

    if lat and lon:

        try:

            offline_stores = (
                find_nearby_pharmacies(

                    medicine_query,

                    float(lat),

                    float(lon),

                    int(radius)
                )
            )

        except Exception as e:

            print(
                "Offline pharmacy search failed:",
                e
            )

            offline_stores = []


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return jsonify({

        "status": "success",

        "query": original_query,

        "medicine_query": medicine_query,

        "location": {

            "latitude": (

                float(lat)

                if lat

                else None
            ),

            "longitude": (

                float(lon)

                if lon

                else None
            )
        },

        "medicine_count": len(
            matches
        ),

        "medicines": matches,

        "offline_store_count": len(
            offline_stores
        ),

        "offline_stores": offline_stores,

        "stock_verified": False
    })


# =========================================================
# GET SINGLE MEDICINE
# =========================================================

@app.route(
    "/api/medicines/<path:medicine_name>",
    methods=["GET"]
)
def get_medicine(
    medicine_name
):

    results = search_indian_medicines(
        medicine_name,
        limit=50
    )

    # -----------------------------------------------------
    # FIRST TRY EXACT MEDICINE NAME
    # -----------------------------------------------------

    for medicine in results:

        name = medicine.get(
            "medicine_name",
            ""
        ).strip().lower()

        if (
            name
            ==
            medicine_name.strip().lower()
        ):

            medicine = enrich_medicine(
                medicine
            )

            return jsonify({

                "status": "success",

                "medicine": medicine
            })


    # -----------------------------------------------------
    # MEDICINE NOT FOUND
    # -----------------------------------------------------

    return jsonify({

        "status": "failed",

        "error": "Medicine not found"

    }), 404


# =========================================================
# BRIGHT DATA MEDICINE SCRAPE AND SYNC
# =========================================================

@app.route(
    "/api/scrape-and-sync",
    methods=["POST"]
)
def scrape_and_sync():

    data = request.get_json() or {}

    target_url = data.get(
        "url"
    )

    if not target_url:

        return jsonify({

            "status": "failed",

            "error": (
                "Missing target extraction "
                "URL parameter"
            )

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

                "error": (
                    "No collection ID returned "
                    "from Bright Data scraper"
                ),

                "brightdata_response": trigger_res

            }), 500

        scraped_data_list = (
            get_collection_result(
                collection_id
            )
        )

        current_catalog = load_medicines()

        catalog_updated = False

        sync_summary = []

        for item in scraped_data_list:

            if not isinstance(
                item,
                dict
            ):

                continue

            med_name = (

                item.get(
                    "name"
                )

                or

                item.get(
                    "medicine_name"
                )

                or

                item.get(
                    "title"
                )
            )

            scraped_price = (

                item.get(
                    "price"
                )

                or

                item.get(
                    "mrp"
                )
            )

            composition = (

                item.get(
                    "composition"
                )

                or

                item.get(
                    "active_ingredient"
                )

                or

                item.get(
                    "salt_content"
                )

                or

                ""
            )

            if (
                not med_name
                or
                scraped_price is None
            ):

                continue

            if isinstance(
                scraped_price,
                dict
            ):

                scraped_price = (

                    scraped_price.get(
                        "value"
                    )

                    or

                    scraped_price.get(
                        "amount"
                    )
                )

            try:

                scraped_price = float(
                    scraped_price
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            tracking_metrics = track_price(

                med_name,

                scraped_price
            )

            matched_in_catalog = False

            for med in current_catalog:

                existing_name = str(
                    med.get(
                        "medicine_name",
                        ""
                    )
                )

                if (
                    existing_name.lower()
                    ==
                    str(
                        med_name
                    ).lower()
                ):

                    med["mrp"] = (
                        scraped_price
                    )

                    med["price"] = (
                        scraped_price
                    )

                    if composition:

                        med["composition"] = (
                            composition
                        )

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

            save_medicines(
                current_catalog
            )

        return jsonify({

            "status": "success",

            "message": (
                f"Successfully parsed and tracked "
                f"{len(sync_summary)} items using "
                f"Bright Data."
            ),

            "updates": sync_summary
        })

    except Exception as e:

        print(
            "Medicine scrape error:",
            e
        )

        return jsonify({

            "status": "failed",

            "error": str(e)

        }), 500


# =========================================================
# GEOCODE LOCATION
# =========================================================

def geocode_location(
    location
):

    try:

        response = requests.get(

            NOMINATIM_URL,

            params={

                "q": location,

                "format": "json",

                "limit": 1,

                "countrycodes": "in"
            },

            headers={

                "User-Agent": USER_AGENT
            },

            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not results:

            return None

        return {

            "latitude": float(
                results[0]["lat"]
            ),

            "longitude": float(
                results[0]["lon"]
            )
        }

    except Exception as e:

        print(
            "Geocoding failed:",
            e
        )

        return None


# =========================================================
# GET PHARMACY WEBSITE
# =========================================================

def get_pharmacy_website(
    tags
):

    website = (

        tags.get(
            "website"
        )

        or

        tags.get(
            "contact:website"
        )

        or

        tags.get(
            "url"
        )
    )

    if not website:

        return None

    website = website.strip()

    if not website:

        return None

    if not website.startswith(
        (
            "http://",
            "https://"
        )
    ):

        website = (
            "https://"
            +
            website
        )

    return website


# =========================================================
# FIND NEARBY PHARMACIES
# =========================================================

def find_nearby_pharmacies(
    medicine,
    lat,
    lon,
    radius=3000
):

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

                "User-Agent": USER_AGENT,

                "Accept": "application/json"
            },

            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        raise RuntimeError(
            f"Unable to find nearby pharmacies: {e}"
        )

    stores = []

    seen = set()

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

        # -------------------------------------------------
        # LOCATION
        # -------------------------------------------------

        if (
            "lat" in element
            and
            "lon" in element
        ):

            store_lat = element[
                "lat"
            ]

            store_lon = element[
                "lon"
            ]

        elif "center" in element:

            store_lat = (
                element["center"].get(
                    "lat"
                )
            )

            store_lon = (
                element["center"].get(
                    "lon"
                )
            )

        else:

            continue

        if (
            store_lat is None
            or
            store_lon is None
        ):

            continue

        website = get_pharmacy_website(
            tags
        )

        # -------------------------------------------------
        # PREVENT DUPLICATES
        # -------------------------------------------------

        unique_key = (

            name.lower().strip(),

            round(
                float(store_lat),
                5
            ),

            round(
                float(store_lon),
                5
            )
        )

        if unique_key in seen:

            continue

        seen.add(
            unique_key
        )

        store = {

            "name": name,

            "latitude": float(
                store_lat
            ),

            "longitude": float(
                store_lon
            ),

            "website": website,

            "source": "OpenStreetMap",

            "brightdata_enriched": False
        }

        stores.append(
            store
        )

    # -----------------------------------------------------
    # BRIGHT DATA ENRICHMENT
    # -----------------------------------------------------

    stores = (
        enrich_pharmacies_with_brightdata(
            stores
        )
    )

    return stores


# =========================================================
# BRIGHT DATA PHARMACY WEBSITE ENRICHMENT
# =========================================================

def enrich_pharmacies_with_brightdata(
    stores
):

    website_urls = []

    # -----------------------------------------------------
    # COLLECT UNIQUE WEBSITES
    # -----------------------------------------------------

    for store in stores:

        website_url = store.get(
            "website"
        )

        if not website_url:

            continue

        website_url = website_url.strip()

        if not website_url:

            continue

        if not website_url.startswith(
            (
                "http://",
                "https://"
            )
        ):

            website_url = (
                "https://"
                +
                website_url
            )

        if website_url not in website_urls:

            website_urls.append(
                website_url
            )

    # -----------------------------------------------------
    # NO WEBSITES
    # -----------------------------------------------------

    if not website_urls:

        return stores

    try:

        print(
            f"Sending {len(website_urls)} "
            "pharmacy website(s) to Bright Data..."
        )

        trigger_res = (
            trigger_multiple_scrapers(
                website_urls
            )
        )

        collection_id = (
            trigger_res.get(
                "collection_id"
            )
        )

        if not collection_id:

            print(
                "Bright Data did not return "
                "a collection ID."
            )

            return stores

        scraped_results = (
            get_collection_result(
                collection_id
            )
        )

        # -------------------------------------------------
        # MAP RESULTS BY URL
        # -------------------------------------------------

        scraped_by_url = {}

        for item in scraped_results:

            if not isinstance(
                item,
                dict
            ):

                continue

            input_data = item.get(
                "input",
                {}
            )

            if isinstance(
                input_data,
                dict
            ):

                input_url = (
                    input_data.get(
                        "url"
                    )
                )

            else:

                input_url = None

            if not input_url:

                input_url = item.get(
                    "url"
                )

            if input_url:

                scraped_by_url[
                    normalize_url(
                        input_url
                    )
                ] = item

        # -------------------------------------------------
        # ATTACH BRIGHT DATA INFORMATION
        # -------------------------------------------------

        for store in stores:

            website_url = store.get(
                "website"
            )

            if not website_url:

                continue

            result = scraped_by_url.get(
                normalize_url(
                    website_url
                )
            )

            if not result:

                continue

            store["brightdata"] = {

                "phone_number": first_value(

                    result,

                    [
                        "phone_number",
                        "phone",
                        "telephone",
                        "contact_number"
                    ]
                ),

                "website_url": first_value(

                    result,

                    [
                        "website_url",
                        "website",
                        "url"
                    ]

                ) or website_url,

                "opening_hours": first_value(

                    result,

                    [
                        "opening_hours",
                        "hours",
                        "business_hours"
                    ]
                ),

                "services_offered": (
                    first_value(

                        result,

                        [
                            "services_offered",
                            "services",
                            "service"
                        ]
                    )
                    or
                    []
                ),

                "source": "Bright Data"
            }

            store[
                "brightdata_enriched"
            ] = True

    except Exception as e:

        print(
            "Bright Data pharmacy enrichment "
            f"failed: {e}"
        )

    return stores


# =========================================================
# NORMALIZE URL
# =========================================================

def normalize_url(
    url
):

    if not url:

        return ""

    url = str(
        url
    ).strip().lower()

    url = url.rstrip(
        "/"
    )

    return url


# =========================================================
# FIRST AVAILABLE VALUE
# =========================================================

def first_value(
    data,
    keys
):

    for key in keys:

        value = data.get(
            key
        )

        if value is not None:

            if isinstance(
                value,
                str
            ):

                if value.strip():

                    return value.strip()

            elif value != "":

                return value

    return None


# =========================================================
# DIRECT NEARBY PHARMACY ENDPOINT
# =========================================================

@app.route(
    "/api/medicine-availability-nearby",
    methods=["GET"]
)
def get_medicine_availability_nearby():

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
        "3000"
    )

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    if (
        not query_medicine
        or
        not lat
        or
        not lon
    ):

        return jsonify({

            "status": "failed",

            "error": (
                "Missing required query parameters: "
                "medicine, lat, lon"
            )

        }), 400

    try:

        lat = float(
            lat
        )

        lon = float(
            lon
        )

        radius = int(
            radius
        )

        if radius <= 0:

            radius = 3000

    except ValueError:

        return jsonify({

            "status": "failed",

            "error": (
                "lat, lon and radius "
                "must be valid numbers"
            )

        }), 400

    try:

        stores = find_nearby_pharmacies(

            query_medicine,

            lat,

            lon,

            radius
        )

    except Exception as e:

        return jsonify({

            "status": "failed",

            "error": str(e)

        }), 500

    return jsonify({

        "status": "success",

        "medicine": query_medicine,

        "location": {

            "latitude": lat,

            "longitude": lon
        },

        "radius": radius,

        "stores": stores,

        "count": len(
            stores
        ),

        "stock_verified": False
    })


# =========================================================
# START FLASK SERVER
# =========================================================

if __name__ == "__main__":

    print(
        "Starting Smart Medicine Finder backend..."
    )

    # Load the large dataset when the server starts.
    # It will remain cached in memory.
    dataset = load_indian_medicine_data()

    print(
        "Indian medicine dataset ready."
    )

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )