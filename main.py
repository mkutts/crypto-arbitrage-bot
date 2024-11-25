import os
import json
import logging
from exchanges.kraken import KrakenAPI
from exchanges.coinbase import CoinbaseAPI
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths for the dashboard log files
DASHBOARD_LOGS_DIR = os.path.join(os.getcwd(), "dashboard", "logs")
PRICES_FILE = os.path.join(DASHBOARD_LOGS_DIR, "prices.json")
OPPORTUNITIES_FILE = os.path.join(DASHBOARD_LOGS_DIR, "opportunities.json")

# Ensure the dashboard logs directory exists
os.makedirs(DASHBOARD_LOGS_DIR, exist_ok=True)

def write_json(data, file_path):
    """
    Writes data to a JSON file.
    """
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        logger.info(f"Updated JSON file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to write to {file_path}: {e}")

def fetch_prices(kraken, coinbase, pair):
    """
    Fetches prices for a trading pair from Kraken and Coinbase.
    """
    symbol, currency = pair.split("/")
    kraken_price = kraken.get_price(symbol, currency)
    coinbase_price = coinbase.get_price(symbol, currency)

    logger.info(f"Kraken {pair} price: {kraken_price}")
    logger.info(f"Coinbase {pair} price: {coinbase_price}")

    return kraken_price, coinbase_price

def detect_arbitrage(kraken_price, coinbase_price, pair, threshold):
    """
    Detects arbitrage opportunities based on prices and a threshold.
    """
    if kraken_price and coinbase_price:
        diff = abs(kraken_price - coinbase_price)
        diff_percent = (diff / ((kraken_price + coinbase_price) / 2)) * 100

        logger.info(f"Dynamic Threshold for {pair}: {threshold:.2f}%")
        if diff_percent >= threshold:
            logger.info(f"Arbitrage Opportunity Detected: {pair} | Diff: {diff_percent:.2f}%")
            return {
                "pair": pair,
                "kraken_price": kraken_price,
                "coinbase_price": coinbase_price,
                "diff_percent": diff_percent,
                "threshold": threshold,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            logger.info(f"No Arbitrage: {pair} | Diff: {diff_percent:.2f}% < Threshold: {threshold:.2f}%")
    return None

def main():
    logger.info("Starting Arbitrage Bot")
    kraken = KrakenAPI()
    coinbase = CoinbaseAPI()

    prices_log = []
    opportunities_log = []

    while True:
        for pair in ["DOGE/USD"]:
            logger.info(f"Fetching prices for {pair}...")
            kraken_price, coinbase_price = fetch_prices(kraken, coinbase, pair)

            # Write live price data
            price_entry = {
                "pair": pair,
                "kraken_price": kraken_price,
                "coinbase_price": coinbase_price,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            prices_log.append(price_entry)
            write_json(prices_log, PRICES_FILE)

            # Detect arbitrage
            threshold = 0.5  # Example threshold
            opportunity = detect_arbitrage(kraken_price, coinbase_price, pair, threshold)
            if opportunity:
                opportunities_log.append(opportunity)
                write_json(opportunities_log, OPPORTUNITIES_FILE)

        time.sleep(10)  # Adjust as needed

if __name__ == "__main__":
    main()
