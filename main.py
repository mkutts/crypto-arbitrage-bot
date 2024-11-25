import logging
import os
import time
import json
import requests
from datetime import datetime
from exchanges.kraken import KrakenAPI
from exchanges.coinbase import CoinbaseAPI
import yaml

# Load configuration
CONFIG_FILE = os.path.join("config.yaml")
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

# Define log paths
PRICES_LOG_PATH = os.path.join("dashboard", "logs", "prices.json")
OPPORTUNITIES_LOG_PATH = os.path.join("dashboard", "logs", "opportunities.json")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def calculate_threshold(buy_exchange, sell_exchange, profit_margin=0.1):
    """
    Calculate the dynamic threshold for arbitrage detection using config.yaml.
    """
    try:
        # Locate the correct exchanges in the list
        buy_exchange_config = next(e for e in config["exchanges"] if e["name"] == buy_exchange)
        sell_exchange_config = next(e for e in config["exchanges"] if e["name"] == sell_exchange)
        
        buy_fee = buy_exchange_config["taker_fee"]
        sell_fee = sell_exchange_config["taker_fee"]

        logger.debug(f"Buy fee for {buy_exchange}: {buy_fee}%, Sell fee for {sell_exchange}: {sell_fee}%")
        return buy_fee + sell_fee + profit_margin
    except StopIteration as e:
        logger.error(f"Exchange not found in configuration: {e}")
        return float("inf")  # Return an impossibly high threshold if config is missing

def log_prices(pair, kraken_price, coinbase_price):
    """
    Logs the prices for a trading pair into the prices.json file.
    """
    if not os.path.exists(PRICES_LOG_PATH) or os.stat(PRICES_LOG_PATH).st_size == 0:
        with open(PRICES_LOG_PATH, "w") as file:
            json.dump([], file)

    try:
        with open(PRICES_LOG_PATH, "r+") as file:
            try:
                prices = json.load(file)
            except json.JSONDecodeError:
                logger.warning("prices.json is not a valid JSON file. Resetting to empty list.")
                prices = []
            
            prices.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pair": pair,
                "kraken_price": kraken_price,
                "coinbase_price": coinbase_price,
            })

            # Keep only the latest 100 prices
            file.seek(0)
            json.dump(prices[-100:], file, indent=4)
            file.truncate()
    except Exception as e:
        logger.error(f"Error logging prices: {e}")

def log_opportunity(opportunity):
    """
    Logs arbitrage opportunities to opportunities.json.
    """
    try:
        if not os.path.exists(OPPORTUNITIES_LOG_PATH):
            with open(OPPORTUNITIES_LOG_PATH, "w") as file:
                json.dump([], file)

        with open(OPPORTUNITIES_LOG_PATH, "r+") as file:
            try:
                opportunities = json.load(file)
                if not isinstance(opportunities, list):
                    logger.warning("opportunities.json is not a list. Resetting to an empty list.")
                    opportunities = []
            except json.JSONDecodeError:
                logger.warning("opportunities.json is not valid JSON. Resetting to an empty list.")
                opportunities = []

            opportunities.append(opportunity)
            opportunities = opportunities[-100:]  # Keep only the latest 100 opportunities

            file.seek(0)
            json.dump(opportunities, file, indent=4)
            file.truncate()

        logger.info(f"Logged opportunity: {opportunity}")
    except Exception as e:
        logger.error(f"Error logging opportunity: {e}")

def send_slack_alert(opportunity):
    """
    Send an alert to Slack for a viable arbitrage opportunity.
    """
    try:
        # Access notifications and webhook URL from the updated config structure
        slack_urls = config["notifications"]["slack_webhook_url"]

        # Ensure Slack notifications are enabled and URLs are provided
        if not slack_urls:
            logger.warning("No Slack webhook URLs provided in configuration.")
            return

        # Prepare the message
        message = (
            f"*Arbitrage Opportunity Detected!*\n"
            f"Pair: {opportunity['pair']}\n"
            f"Kraken Price: {opportunity['kraken_price']:.4f}\n"
            f"Coinbase Price: {opportunity['coinbase_price']:.4f}\n"
            f"Difference: {opportunity['price_difference']:.4f} ({opportunity['percentage_difference']:.2f}%)\n"
            f"Threshold: {opportunity['threshold']:.2f}%\n"
            f"Timestamp: {opportunity['timestamp']}"
        )

        # Send message to each Slack URL
        payload = {"text": message}
        for url in slack_urls:
            response = requests.post(url, json=payload)
            response.raise_for_status()

        logger.info("Slack alert sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")

def main():
    """
    Main function to start the arbitrage bot.
    """
    logger.info("Starting Arbitrage Bot")

    # Initialize API clients
    kraken = KrakenAPI()
    coinbase = CoinbaseAPI()

    while True:
        for pair_config in config["pairs"]:
            pair = pair_config["symbol"]
            logger.info(f"Fetching prices for {pair}...")

            kraken_price = kraken.get_price(pair.split('/')[0], pair.split('/')[1])
            coinbase_price = coinbase.get_price(pair.split('/')[0], pair.split('/')[1])

            if kraken_price is not None and coinbase_price is not None:
                logger.info(f"Kraken {pair} price: {kraken_price}")
                logger.info(f"Coinbase {pair} price: {coinbase_price}")

                threshold = calculate_threshold("kraken", "coinbase", profit_margin=pair_config.get("profit_margin", 0.1))
                price_difference = abs(kraken_price - coinbase_price)
                percentage_difference = (price_difference / ((kraken_price + coinbase_price) / 2)) * 100

                log_prices(pair, kraken_price, coinbase_price)

                opportunity = {
                    "pair": pair,
                    "kraken_price": kraken_price,
                    "coinbase_price": coinbase_price,
                    "price_difference": price_difference,
                    "percentage_difference": percentage_difference,
                    "threshold": threshold,
                    "is_viable": percentage_difference >= threshold,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                log_opportunity(opportunity)

                if opportunity["is_viable"]:
                    logger.info(f"Arbitrage Opportunity Detected: {opportunity}")
                    send_slack_alert(opportunity)
                else:
                    logger.info(f"No Arbitrage: {pair} | Diff: {percentage_difference:.2f}% < Threshold: {threshold:.2f}%")
            else:
                logger.warning(f"Failed to fetch prices for {pair}")

        time.sleep(config.get("poll_interval", 10))

if __name__ == "__main__":
    main()
