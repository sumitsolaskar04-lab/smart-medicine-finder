import json
import os
from datetime import datetime


HISTORY_FILE = "data/price_history.json"


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_history(history):

    os.makedirs("data", exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)


def track_price(medicine_name, current_price):

    history = load_history()

    if medicine_name not in history:
        history[medicine_name] = []

    previous_price = None

    if history[medicine_name]:
        previous_price = history[medicine_name][-1]["price"]

    price_change = None

    if previous_price is not None:
        price_change = round(current_price - previous_price, 2)

    record = {
        "timestamp": datetime.now().isoformat(),
        "price": current_price,
        "price_change": price_change
    }

    history[medicine_name].append(record)

    save_history(history)

    return {
        "current_price": current_price,
        "previous_price": previous_price,
        "price_change": price_change
    }