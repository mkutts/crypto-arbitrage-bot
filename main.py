# main.py

import logging
from exchanges.kraken import KrakenAPI
from exchanges.coinbase import CoinbaseAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define trading pairs to compare
TRADING_PAIRS = [("BTC", "USD"), ("ETH", "USD")]

# Define arbitrage threshold percentage
ARBITRAGE_THRESHOLD = 0.005  # Example: 0.5% difference

class ArbitrageBot:
    def __init__(self, mode="SIMULATION"):
        self.mode = mode
        self.exchanges = {
            "Kraken": KrakenAPI(),
            "Coinbase": CoinbaseAPI()
        }

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
            logger.info(f"SIMULATION MODE: Hypothetical trade amount = {trade_amount} BTC/ETH, Profit = ${profit:.2f}")
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
        Logs executed trades or simulated trades.
        """
        trade_log = {
            "mode": mode,
            "buy_exchange": opportunity['buy_exchange'],
            "sell_exchange": opportunity['sell_exchange'],
            "buy_price": opportunity['min_price'],
            "sell_price": opportunity['max_price'],
            "profit": profit,
        }
        logger.info(f"Trade Log: {trade_log}")

    def calculate_arbitrage(self, pair, price_kraken, price_coinbase):
        """
        Calculate arbitrage percentage and execute trades if opportunity is detected.
        """
        diff_percentage = abs(price_kraken - price_coinbase) / min(price_kraken, price_coinbase) * 100
        logger.info(
            f"Comparison for {pair}: Kraken: {price_kraken}, Coinbase: {price_coinbase}, "
            f"Difference: {diff_percentage:.2f}%"
        )

        if diff_percentage >= ARBITRAGE_THRESHOLD:
            logger.info(
                f"Arbitrage Opportunity Detected for {pair}!"
                f" Kraken: {price_kraken}, Coinbase: {price_coinbase}, "
                f"Difference: {diff_percentage:.2f}%"
            )

            opportunity = {
                "buy_exchange": "Kraken" if price_kraken < price_coinbase else "Coinbase",
                "sell_exchange": "Coinbase" if price_kraken < price_coinbase else "Kraken",
                "min_price": min(price_kraken, price_coinbase),
                "max_price": max(price_kraken, price_coinbase),
            }
            self.execute_trade(opportunity)

    def run(self):
        logger.info("Starting Arbitrage Detection")

        for symbol, currency in TRADING_PAIRS:
            logger.info(f"Fetching prices for {symbol}/{currency}...")

            # Fetch prices
            price_kraken = self.exchanges["Kraken"].get_price(symbol, currency)
            price_coinbase = self.exchanges["Coinbase"].get_price(symbol, currency)

            if price_kraken is None or price_coinbase is None:
                logger.warning(f"Failed to fetch prices for {symbol}/{currency}")
                continue

            # Calculate arbitrage and execute trades if applicable
            self.calculate_arbitrage(f"{symbol}/{currency}", price_kraken, price_coinbase)


if __name__ == "__main__":
    bot = ArbitrageBot(mode="SIMULATION")  # Change to "LIVE" for live trading
    bot.run()
