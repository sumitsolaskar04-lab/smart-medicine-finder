from flask import Flask, jsonify
from medicine_data import medicines
from medicine_analyzer import process_medicines


app = Flask(__name__)


@app.route("/")
def home():
    return "Medicine Intelligence API is running"


@app.route("/api/medicines")
def get_medicines():

    results = process_medicines(medicines)

    return jsonify({
        "medicines": results
    })


@app.route("/api/medicines/<medicine_name>")
def get_medicine(medicine_name):

    results = process_medicines(medicines)

    for medicine in results:
        if medicine["medicine_name"].lower() == medicine_name.lower():
            return jsonify(medicine)

    return jsonify({
        "error": "Medicine not found"
    }), 404


if __name__ == "__main__":
    app.run(debug=True)