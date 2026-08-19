from medicine_data import medicines
from medicine_analyzer import process_medicines
from price_tracker import check_price_change


results = process_medicines(medicines)

for medicine in results:

    print("--------------------------------")
    print("Medicine:", medicine["medicine_name"])

    price = medicine["price"]["value"]
    mrp = medicine["mrp"]["value"]

    print("Price: ₹", price)
    print("MRP: ₹", mrp)
    print("Discount:", medicine["discount_percent"], "%")
    print("Manufacturer:", medicine["manufacturer"])
    print("Availability:", medicine["availability"])
    print("Status:", medicine["data_status"])

    if medicine["missing_fields"]:
        print("Missing:", medicine["missing_fields"])
    else:
        print("Missing: None")

    price_result = check_price_change(
        medicine["medicine_name"],
        price
    )

    print("Price Status:", price_result["status"])

    if price_result["previous_price"] is not None:
        print("Previous Price: ₹", price_result["previous_price"])
        print("Price Change:", price_result["change_percent"], "%")