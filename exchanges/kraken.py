import requests
import logging
import os
import time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class KrakenAPI:
    def __init__(self):
        self.api_key = os.getenv("KRAKEN_API_KEY")
        self.api_secret = os.getenv("KRAKEN_API_SECRET")
        self.base_url = "https://api.kraken.com"

        # Hardcoded trading pairs
        self.hardcoded_pairs = {
            "ETH/USD": "XETHZUSD",  # ETH/USD in Kraken's naming convention
            "BTC/USD": "XXBTZUSD"  # BTC/USD in Kraken's naming convention
        }

    def get_price(self, symbol, currency):
        """
        Fetches the latest price for the chosen trading pair from Kraken.
        Uses hardcoded pair mapping for stability.
        """
        pair = f"{symbol}/{currency}".upper()
        kraken_pair = self.hardcoded_pairs.get(pair)

        if not kraken_pair:
            logger.warning(f"Pair {pair} not found in hardcoded pairs.")
            return None

        endpoint = "/0/public/Ticker"
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params={"pair": kraken_pair})
            response.raise_for_status()
            data = response.json()
            if "result" in data:
                ticker = list(data["result"].keys())[0]
                price = float(data["result"][ticker]['c'][0])
                logger.info(f"Fetched price for {pair} from Kraken: {price}")
                return price
            else:
                logger.warning(f"Unexpected response format from Kraken: {data}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from Kraken: {e}")
            return None

