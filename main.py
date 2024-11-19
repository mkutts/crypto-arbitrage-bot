import time
import logging
import csv
from exchanges.kraken import KrakenAPI
from exchanges.coinbase import CoinbaseAPI
from exchanges.binance import BinanceAPI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("arbitrage_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)  # Create a logger object


class CryptoArbitrageBot:
    def __init__(self, exchanges, crypto_symbol, currency, mode, base_threshold=0.1):
        self.exchanges = exchanges  # Exchange API instances
        self.crypto_symbol = crypto_symbol  # E.g., BTC, DOGE
        self.currency = currency  # E.g., USD
        self.mode = mode  # SIMULATION or LIVE
        self.base_threshold = base_threshold  # Minimum profit threshold as percentage

    def get_prices(self):
        """
        Fetches prices for the chosen cryptocurrency pair from each exchange.
        """
        prices = {}
        for exchange_name, api in self.exchanges.items():
            try:
                price = api.get_price(self.crypto_symbol, self.currency)
                if price is not None:
                    prices[exchange_name] = price
                    logger.info(f"Fetched price from {exchange_name}: {price}")
                else:
                    logger.warning(f"Failed to fetch price from {exchange_name}.")
            except Exception as e:
                logger.error(f"Error fetching price from {exchange_name}: {e}")
        return prices

    def detect_arbitrage_opportunity(self, prices):
        """
        Detects arbitrage opportunities based on a profit threshold.
        """
        if not prices:
            logger.warning("No prices available to check for arbitrage.")
            return None

        max_price = max(prices.values())
        min_price = min(prices.values())
        spread = (max_price - min_price) / min_price * 100
        logger.info(f"Detected price spread: {spread:.2f}%")

        if spread > self.base_threshold:
            buy_exchange = min(prices, key=prices.get)
            sell_exchange = max(prices, key=prices.get)
            logger.info(f"Arbitrage Opportunity: Buy on {buy_exchange} at ${min_price}, Sell on {sell_exchange} at ${max_price}")
            return {
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "min_price": min_price,
                "max_price": max_price
            }
        else:
            logger.info("No profitable arbitrage opportunity detected.")
        return None

    def execute_trade(self, opportunity):
        """
        Executes a trade in the chosen mode.
        """
        buy_exchange = opportunity['buy_exchange']
        sell_exchange = opportunity['sell_exchange']
        buy_price = opportunity['min_price']
        sell_price = opportunity['max_price']
        trade_amount = 0.001  # Example trade amount

        logger.info(f"Executing trade: Buy on {buy_exchange} at {buy_price}, Sell on {sell_exchange} at {sell_price}")

        if self.mode == "SIMULATION":
            # Simulate the trade
            profit = (sell_price - buy_price) * trade_amount
            logger.info(f"SIMULATION MODE: Hypothetical trade amount = {trade_amount} {self.crypto_symbol}, Profit = ${profit:.2f}")
            self.log_trade(opportunity, profit, "SIMULATION")
        elif self.mode == "LIVE":
            try:
                # Execute buy order
                if buy_exchange in self.exchanges:
                    self.exchanges[buy_exchange].place_order("buy", buy_price, trade_amount)
                else:
                    logger.error(f"Buy exchange {buy_exchange} not supported.")

                # Execute sell order
                if sell_exchange in self.exchanges:
                    self.exchanges[sell_exchange].place_order("sell", sell_price, trade_amount)
                else:
                    logger.error(f"Sell exchange {sell_exchange} not supported.")

                logger.info("LIVE TRADE EXECUTED.")
                self.log_trade(opportunity, None, "LIVE")
            except Exception as e:
                logger.error(f"Error executing live trade: {e}")
        else:
            logger.error(f"Invalid mode: {self.mode}")

    def log_trade(self, opportunity, profit, mode):
        """
        Logs trade details to a CSV file.
        """
        try:
            with open("trade_log.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    opportunity["buy_exchange"],
                    opportunity["sell_exchange"],
                    opportunity["min_price"],
                    opportunity["max_price"],
                    profit if profit is not None else "N/A",
                    mode,
                    time.strftime("%Y-%m-%d %H:%M:%S")
                ])
            logger.info(f"Trade logged successfully: {opportunity} with profit {profit}")
        except Exception as e:
            logger.error(f"Error logging trade: {e}")

    def run(self):
        """
        Main loop to continuously check for arbitrage opportunities and execute trades.
        """
        logger.info("Arbitrage bot is now running.")
        while True:
            try:
                prices = self.get_prices()
                logger.info(f"Current prices: {prices}")

                opportunity = self.detect_arbitrage_opportunity(prices)
                if opportunity:
                    self.execute_trade(opportunity)

                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in main bot loop: {e}")


def validate_pair(crypto_symbol, currency, exchanges):
    """
    Validates the trading pair across all exchanges, with detailed logging.
    """
    crypto_symbol = crypto_symbol.upper()
    currency = currency.upper()
    valid_pairs = {}

    for exchange_name, api in exchanges.items():
        try:
            pairs = api.get_trading_pairs()
            logger.info(f"Fetched {len(pairs)} pairs from {exchange_name}. Validating...")
            for pair in pairs:
                if crypto_symbol in pair and currency in pair:
                    logger.info(f"Matched pair {pair} on {exchange_name}.")
                    valid_pairs[exchange_name] = pair
                    break
            else:
                logger.warning(f"No matching pair for {crypto_symbol}/{currency} on {exchange_name}.")
        except Exception as e:
            logger.error(f"Error validating pairs on {exchange_name}: {e}")

    if valid_pairs:
        logger.info(f"Valid pairs for {crypto_symbol}/{currency}: {valid_pairs}")
    else:
        logger.warning(f"Pair {crypto_symbol}/{currency} is not available on any exchange.")
    return valid_pairs


# Initialize APIs for exchanges
kraken_api = KrakenAPI()
coinbase_api = CoinbaseAPI()
binance_api = BinanceAPI()
exchanges = {
    "Kraken": kraken_api,
    "CoinbasePro": coinbase_api,
    "Binance": binance_api
}

# Prompt user for cryptocurrency and currency input
crypto_symbol = input("Enter the cryptocurrency symbol (e.g., BTC, DOGE): ").upper()
currency = input("Enter the currency (e.g., USD): ").upper()

# Validate the user input trading pair
valid_pairs = validate_pair(crypto_symbol, currency, exchanges)
if not valid_pairs:
    print(f"Error: {crypto_symbol}/{currency} is not supported on any exchange.")
    exit()
print(f"Valid trading pairs found: {valid_pairs}")

# Prompt user for trading mode (SIMULATION or LIVE)
mode = input("Enter mode (SIMULATION or LIVE): ").strip().upper()
if mode not in {"SIMULATION", "LIVE"}:
    print("Invalid mode. Defaulting to SIMULATION.")
    mode = "SIMULATION"

# Start the bot
print(f"Running in {mode} mode.")
bot = CryptoArbitrageBot(exchanges, crypto_symbol, currency, mode)
bot.run()
