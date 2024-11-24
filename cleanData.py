import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_and_clean_data(file_path):
    """
    Load CSV data and clean it.
    :param file_path: Path to the CSV file.
    :return: Cleaned Pandas DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        df["time"] = pd.to_datetime(df["time"])  # Ensure time column is datetime
        df.set_index("time", inplace=True)  # Set time as index for alignment
        logger.info(f"Loaded and cleaned data from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

def synchronize_data(kraken_df, coinbase_df):
    """
    Synchronize Kraken and Coinbase data by aligning timestamps.
    :param kraken_df: Kraken DataFrame.
    :param coinbase_df: Coinbase DataFrame.
    :return: Merged DataFrame.
    """
    try:
        # Merge on index (timestamp), using inner join to keep only overlapping times
        merged_df = pd.merge(kraken_df, coinbase_df, left_index=True, right_index=True, suffixes=("_kraken", "_coinbase"))
        logger.info("Data synchronized successfully")
        return merged_df
    except Exception as e:
        logger.error(f"Error synchronizing data: {e}")
        return pd.DataFrame()

def main():
    # Load data
    kraken_btc = load_and_clean_data("kraken_BTC_USD.csv")
    coinbase_btc = load_and_clean_data("coinbase_BTC_USD.csv")
    
    kraken_eth = load_and_clean_data("kraken_ETH_USD.csv")
    coinbase_eth = load_and_clean_data("coinbase_ETH_USD.csv")

    # Synchronize data
    btc_data = synchronize_data(kraken_btc, coinbase_btc)
    eth_data = synchronize_data(kraken_eth, coinbase_eth)

    # Save merged data for future use
    btc_data.to_csv("merged_BTC_USD.csv")
    eth_data.to_csv("merged_ETH_USD.csv")
    logger.info("Merged data saved to CSV files")

if __name__ == "__main__":
    main()
