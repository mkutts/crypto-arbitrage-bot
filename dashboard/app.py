from flask import Flask, jsonify, render_template
import os
import json

app = Flask(__name__)

# Paths for log files
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LIVE_DATA_PATH = os.path.join(LOG_DIR, "prices.json")
OPPORTUNITIES_LOG_PATH = os.path.join(LOG_DIR, "opportunities.json")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/live-data')
def live_data():
    try:
        with open(LIVE_DATA_PATH, "r") as file:
            data = json.load(file)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error reading live data: {e}"})

@app.route('/api/arbitrage-log')
def arbitrage_log():
    try:
        if os.path.exists(OPPORTUNITIES_LOG_PATH):
            with open(OPPORTUNITIES_LOG_PATH, "r") as file:
                data = json.load(file)
                return jsonify(data)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": f"Error reading arbitrage log: {e}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)