from flask import Flask, jsonify
import os
import json
import logging

app = Flask(__name__)

# Set the correct log directory
LOGS_DIR = os.path.join(os.getcwd(), "logs")
PRICES_FILE = os.path.join(LOGS_DIR, "prices.json")
OPPORTUNITIES_FILE = os.path.join(LOGS_DIR, "opportunities.json")

@app.route("/")
def home():
    return "<h1>Crypto Arbitrage Dashboard</h1><p>Visit /api/live-data or /api/arbitrage-log</p>"

@app.route("/api/live-data", methods=["GET"])
def live_data():
    try:
        if not os.path.exists(PRICES_FILE):
            return jsonify({"error": f"JSON file not found at {PRICES_FILE}"}), 404

        with open(PRICES_FILE, "r") as file:
            data = json.load(file)
            return jsonify(data)

    except Exception as e:
        logging.error(f"Error reading live data file: {e}")
        return jsonify({"error": f"Error reading live data file: {e}"}), 500

@app.route("/api/arbitrage-log", methods=["GET"])
def arbitrage_log():
    try:
        if not os.path.exists(OPPORTUNITIES_FILE):
            return jsonify({"error": f"JSON file not found at {OPPORTUNITIES_FILE}"}), 404

        with open(OPPORTUNITIES_FILE, "r") as file:
            data = json.load(file)
            return jsonify(data)

    except Exception as e:
        logging.error(f"Error reading arbitrage log file: {e}")
        return jsonify({"error": f"Error reading arbitrage log file: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
