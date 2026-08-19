import json
import os


HISTORY_FILE = "data/price_history.json"


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r") as file:
        return json.load(file)


def save_history(history):
    os.makedirs("data", exist_ok=True)

    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file, indent=4)


def check_price_change(medicine_name, current_price):
    history = load_history()

    previous_price = history.get(medicine_name)

    if previous_price is None:
        history[medicine_name] = current_price
        save_history(history)

        return {
            "status": "FIRST_RECORD",
            "previous_price": None,
            "current_price": current_price,
            "change_percent": 0
        }

    difference = current_price - previous_price

    if previous_price != 0:
        change_percent = (difference / previous_price) * 100
    else:
        change_percent = 0

    if difference > 0:
        status = "PRICE_INCREASED"
    elif difference < 0:
        status = "PRICE_DECREASED"
    else:
        status = "NO_CHANGE"

    history[medicine_name] = current_price
    save_history(history)

    return {
        "status": status,
        "previous_price": previous_price,
        "current_price": current_price,
        "change_percent": round(change_percent, 2)
    }