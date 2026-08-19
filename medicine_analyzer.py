REQUIRED_FIELDS = [
    "medicine_name",
    "price",
    "mrp",
    "manufacturer",
    "availability"
]


def calculate_discount(price, mrp):
    if mrp <= 0:
        return 0

    discount = ((mrp - price) / mrp) * 100
    return round(discount, 2)


def find_missing_fields(medicine):
    missing = []

    for field in REQUIRED_FIELDS:
        if field not in medicine or medicine[field] in (None, "", {}):
            missing.append(field)

    return missing


def validate_price(price, mrp):
    if price <= 0:
        return False

    if mrp <= 0:
        return False

    if price > mrp:
        return False

    return True


def analyze_medicine(medicine):
    missing_fields = find_missing_fields(medicine)

    result = medicine.copy()

    if "price" in medicine and isinstance(medicine["price"], dict):
        price = medicine["price"].get("value")
    else:
        price = None

    if "mrp" in medicine and isinstance(medicine["mrp"], dict):
        mrp = medicine["mrp"].get("value")
    else:
        mrp = None

    result["discount_percent"] = None
    result["data_status"] = "COMPLETE"
    result["missing_fields"] = missing_fields

    if price is not None and mrp is not None:
        if validate_price(price, mrp):
            result["discount_percent"] = calculate_discount(price, mrp)
        else:
            result["data_status"] = "INVALID"

    if missing_fields:
        result["data_status"] = "INCOMPLETE"

    return result


def process_medicines(medicines):
    results = []

    for medicine in medicines:
        analyzed = analyze_medicine(medicine)
        results.append(analyzed)

    return results