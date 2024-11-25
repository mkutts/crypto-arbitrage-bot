from flask import Flask, jsonify, render_template
import os
import json

app = Flask(__name__)

# Paths for log files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
PRICES_FILE = os.path.join(LOG_DIR, "prices.json")
OPPORTUNITIES_FILE = os.path.join(LOG_DIR, "opportunities.json")

@app.route("/")
def home():
    return render_template("index.html")  # Serve the dashboard HTML

@app.route("/api/live-data")
def live_data():
    try:
        if not os.path.exists(PRICES_FILE):
            return jsonify({"error": f"JSON file not found at {PRICES_FILE}"})
        with open(PRICES_FILE, "r") as file:
            data = json.load(file)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error reading log file: {e}"})

@app.route("/api/arbitrage-log")
def arbitrage_log():
    try:
        if not os.path.exists(OPPORTUNITIES_FILE):
            return jsonify({"error": f"JSON file not found at {OPPORTUNITIES_FILE}"})
        with open(OPPORTUNITIES_FILE, "r") as file:
            data = json.load(file)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error reading log file: {e}"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
