import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Function to fetch historical data from Kraken
def fetch_kraken_ohlc(pair, interval, since):
    """
    Fetch OHLC data from Kraken API.
    :param pair: Trading pair (e.g., "XBTUSD").
    :param interval: Time interval in minutes (e.g., 1).
    :param since: Starting timestamp (UNIX time).
    :return: Pandas DataFrame containing OHLC data.
    """
    url = "https://api.kraken.com/0/public/OHLC"
    params = {
        "pair": pair,
        "interval": interval,
        "since": since
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        ohlc_data = data["result"][pair]

        # Create a DataFrame
        df = pd.DataFrame(ohlc_data, columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"])
        df["time"] = pd.to_datetime(df["time"], unit="s")
        logger.info(f"Fetched {len(df)} rows of data for {pair} from Kraken.")
        return df
    except Exception as e:
        logger.error(f"Error fetching data from Kraken: {e}")
        return pd.DataFrame()

# Function to fetch historical data from CryptoCompare for Coinbase
def fetch_coinbase_ohlc(symbol, currency, interval, limit=2000):
    """
    Fetch OHLC data from CryptoCompare for Coinbase.
    :param symbol: Cryptocurrency symbol (e.g., "BTC").
    :param currency: Quote currency (e.g., "USD").
    :param interval: Time interval (e.g., "minute").
    :param limit: Number of data points to fetch (default: 2000).
    :return: Pandas DataFrame containing OHLC data.
    """
    url = f"https://min-api.cryptocompare.com/data/v2/histo{interval}"
    params = {
        "fsym": symbol,
        "tsym": currency,
        "limit": limit,
        "aggregate": 1,
        "api_key": "13fea2ef47fef412f1518b06c4fe8de6bfed8d92b825370348a0dc1c39cb992f"  # Replace with your API key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()["Data"]["Data"]

        # Create a DataFrame
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        logger.info(f"Fetched {len(df)} rows of data for {symbol}/{currency} from CryptoCompare.")
        return df
    except Exception as e:
        logger.error(f"Error fetching data from CryptoCompare: {e}")
        return pd.DataFrame()

# Save data locally
def save_to_csv(df, filename):
    """
    Save a DataFrame to a CSV file.
    :param df: Pandas DataFrame.
    :param filename: File name for the CSV.
    """
    try:
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")

# Main function to orchestrate the fetching process
def main():
    # Define parameters
    kraken_pairs = {"BTC/USD": "XXBTZUSD", "ETH/USD": "XETHZUSD"}
    coinbase_pairs = [("BTC", "USD"), ("ETH", "USD")]
    interval = 1  # 1-minute interval
    since = int((datetime.now() - timedelta(days=180)).timestamp())  # Last 6 months

    # Fetch Kraken data
    for pair_name, kraken_pair in kraken_pairs.items():
        logger.info(f"Fetching Kraken data for {pair_name}...")
        kraken_df = fetch_kraken_ohlc(kraken_pair, interval, since)
        if not kraken_df.empty:
            save_to_csv(kraken_df, f"kraken_{pair_name.replace('/', '_')}.csv")

    # Fetch Coinbase data
    for symbol, currency in coinbase_pairs:
        logger.info(f"Fetching Coinbase data for {symbol}/{currency}...")
        coinbase_df = fetch_coinbase_ohlc(symbol, currency, "minute", limit=720)  # Fetch for 720 minutes (12 hours) at a time
        if not coinbase_df.empty:
            save_to_csv(coinbase_df, f"coinbase_{symbol}_{currency}.csv")

if __name__ == "__main__":
    main()
