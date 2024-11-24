import logging
from exchanges.kraken import KrakenAPI
from exchanges.coinbase import CoinbaseAPI
import yaml
import os

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config["logging"]["level"].upper()),
    filename=config["logging"]["filename"] if config["logging"]["output"] == "file" else None,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def fetch_prices(kraken, coinbase, pair):
    """
    Fetch prices for a trading pair from Kraken and Coinbase.
    """
    symbol, currency = pair.split("/")
    kraken_price = kraken.get_price(symbol, currency)
    logger.info(f"Kraken price for {pair}: {kraken_price}")

    coinbase_price = coinbase.get_price(symbol, currency)
    logger.info(f"Coinbase price for {pair}: {coinbase_price}")

    return kraken_price, coinbase_price

def calculate_threshold(buy_exchange, sell_exchange, profit_margin=0.1, order_type="limit"):
    """
    Calculate the dynamic threshold for arbitrage detection based on maker/taker fees.
    :param buy_exchange: Name of the exchange to buy from.
    :param sell_exchange: Name of the exchange to sell on.
    :param profit_margin: Desired profit margin in percentage.
    :param order_type: 'limit' (maker) or 'market' (taker).
    :return: Minimum percentage difference for a profitable trade.
    """
    # Fetch fee structure from config
    exchange_fees = {exchange["name"]: exchange for exchange in config["exchanges"]}

    buy_fees = exchange_fees.get(buy_exchange, {})
    sell_fees = exchange_fees.get(sell_exchange, {})

    # Use maker or taker fees based on order type
    buy_fee = buy_fees.get("maker_fee" if order_type == "limit" else "taker_fee", 0)
    sell_fee = sell_fees.get("taker_fee", 0)  # Selling is usually a taker action

    # Total threshold = buy fee + sell fee + desired profit margin
    return buy_fee + sell_fee + profit_margin

def compare_prices(kraken_price, coinbase_price, pair, threshold):
    """
    Compare prices between Kraken and Coinbase to identify arbitrage opportunities.
    Includes a dynamic threshold for detection.
    """
    if kraken_price and coinbase_price:
        diff = abs(kraken_price - coinbase_price)
        diff_percent = (diff / ((kraken_price + coinbase_price) / 2)) * 100

        # Log raw difference, percentage difference, and threshold
        logger.info(
            f"Comparison for {pair}: Kraken: {kraken_price}, Coinbase: {coinbase_price}, "
            f"Raw Difference: {diff}, Percentage Difference: {diff_percent:.2f}%, "
            f"Threshold: {threshold:.2f}%"
        )

        if diff_percent >= threshold:
            logger.info(f"Arbitrage opportunity detected for {pair}: Kraken: {kraken_price}, Coinbase: {coinbase_price}")
            return {
                "pair": pair,
                "kraken_price": kraken_price,
                "coinbase_price": coinbase_price,
                "difference": diff_percent,
            }
        else:
            logger.info(f"No Arbitrage for {pair}: Difference {diff_percent:.2f}% is below Threshold {threshold:.2f}%")
    return None

def find_arbitrage_opportunities(pairs, kraken, coinbase):
    """
    Find arbitrage opportunities between Kraken and Coinbase.
    """
    opportunities = []
    for pair_config in pairs:
        pair = pair_config["symbol"]
        logger.info(f"Fetching prices for {pair}...")
        symbol, currency = pair.split("/")
        kraken_price = kraken.get_price(symbol, currency)
        coinbase_price = coinbase.get_price(symbol, currency)

        # Calculate dynamic threshold for the pair
        threshold = calculate_threshold("kraken", "coinbase")

        opportunity = compare_prices(kraken_price, coinbase_price, pair, threshold)
        if opportunity:
            opportunities.append(opportunity)

    return opportunities

def main():
    logger.info("Starting Arbitrage Detection")

    # Initialize API clients
    kraken = KrakenAPI()
    coinbase = CoinbaseAPI()

    # Find arbitrage opportunities
    opportunities = find_arbitrage_opportunities(config["pairs"], kraken, coinbase)

    if opportunities:
        logger.info("Arbitrage Opportunities Detected:")
        for opp in opportunities:
            logger.info(f"Pair: {opp['pair']}, Kraken: {opp['kraken_price']}, Coinbase: {opp['coinbase_price']}, Difference: {opp['difference']:.2f}%")
    else:
        logger.info("No Arbitrage Opportunities Detected.")

if __name__ == "__main__":
    main()
