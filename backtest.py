import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Example fees (update as per actual rates)
EXCHANGE_FEES = {
    'kraken': {'maker': 0, 'taker': 0},  # In percentage
    'coinbase': {'maker': 0, 'taker': 0}   # In percentage
}

def calculate_threshold(buy_exchange, sell_exchange, profit_margin=0.1):
    """
    Calculate the dynamic threshold for arbitrage detection.
    :param buy_exchange: Name of the exchange to buy from.
    :param sell_exchange: Name of the exchange to sell on.
    :param profit_margin: Desired profit margin in percentage.
    :return: Minimum percentage difference for a profitable trade.
    """
    buy_fee = EXCHANGE_FEES[buy_exchange]['taker']
    sell_fee = EXCHANGE_FEES[sell_exchange]['taker']
    return buy_fee + sell_fee + profit_margin

def analyze_opportunities(data, buy_exchange, sell_exchange, pair):
    """
    Identify arbitrage opportunities based on price differences.
    :param data: DataFrame with relevant price data.
    :param buy_exchange: Name of the buy exchange.
    :param sell_exchange: Name of the sell exchange.
    :param pair: Trading pair (e.g., BTC/USD).
    :return: DataFrame of arbitrage opportunities.
    """
    opportunities = []

    for index, row in data.iterrows():
        buy_price = row["kraken_price"]
        sell_price = row["coinbase_price"]

        if pd.isna(buy_price) or pd.isna(sell_price):
            logger.debug(f"Missing data at {index}")
            continue

        price_diff = sell_price - buy_price
        percent_diff = (price_diff / buy_price) * 100

        threshold = calculate_threshold(buy_exchange, sell_exchange)

        if percent_diff > threshold:  # Arbitrage opportunity
            opportunities.append({
                'timestamp': index,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'percent_diff': percent_diff,
                'threshold': threshold,
                'profit_margin': percent_diff - threshold,
            })

    return pd.DataFrame(opportunities)

def simulate_trades(opportunities, initial_balance, trade_size):
    """
    Simulate trades based on arbitrage opportunities.
    :param opportunities: DataFrame of arbitrage opportunities.
    :param initial_balance: Initial balance for trading.
    :param trade_size: Amount to trade in each arbitrage.
    :return: Final balance and list of profitable trades.
    """
    balance = initial_balance
    profitable_trades = []

    for _, opp in opportunities.iterrows():
        buy_price = opp['buy_price']
        sell_price = opp['sell_price']
        profit_margin = opp['profit_margin']

        # Calculate profit for the trade
        profit = trade_size * (sell_price - buy_price) - trade_size * (buy_price * opp['threshold'] / 100)

        if profit > 0:
            balance += profit
            profitable_trades.append(opp)

    return balance, profitable_trades

def main():
    logger.info("Starting Backtest Simulation")

    # Load BTC and ETH data
    btc_data = pd.read_csv("simplified_BTC_USD.csv", index_col="timestamp", parse_dates=True)
    eth_data = pd.read_csv("simplified_ETH_USD.csv", index_col="timestamp", parse_dates=True)

    # Analyze opportunities for BTC and ETH
    btc_opportunities = analyze_opportunities(btc_data, 'kraken', 'coinbase', 'BTC/USD')
    eth_opportunities = analyze_opportunities(eth_data, 'kraken', 'coinbase', 'ETH/USD')

    # Save opportunities to CSV
    btc_opportunities.to_csv("BTC_USD_opportunities.csv", index=False)
    eth_opportunities.to_csv("ETH_USD_opportunities.csv", index=False)

    # Simulate trades
    initial_balance = 10000  # Starting with $10,000
    trade_size = 0.1  # Example trade size (1 mBTC or equivalent ETH)

    btc_balance, btc_trades = simulate_trades(btc_opportunities, initial_balance, trade_size)
    eth_balance, eth_trades = simulate_trades(eth_opportunities, initial_balance, trade_size)

    # Log results
    logger.info(f"Simulated Trades Completed: {len(btc_trades)} profitable BTC trades.")
    logger.info(f"Simulated Trades Completed: {len(eth_trades)} profitable ETH trades.")
    logger.info(f"Final Balance for BTC: ${btc_balance:.2f}")
    logger.info(f"Final Balance for ETH: ${eth_balance:.2f}")
    logger.info("Simulation Complete. Results saved to CSV.")

if __name__ == "__main__":
    main()
