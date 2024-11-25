import requests
import logging

logger = logging.getLogger(__name__)

class KrakenAPI:
    def __init__(self):
        """
        Initialize Kraken API class with base URL and hardcoded trading pairs.
        """
        self.base_url = "https://api.kraken.com"
        self.hardcoded_pairs = {
            "DOGE/USD": "XDGUSD",  # DOGE/USD in Kraken's naming convention
            "ETH/USD": "XETHZUSD",  # ETH/USD in Kraken's naming convention
            "BTC/USD": "XXBTZUSD",  # BTC/USD in Kraken's naming convention
        }

    def get_price(self, symbol, currency):
        """
        Fetch the latest price for a given trading pair from Kraken.
        
        Args:
            symbol (str): Cryptocurrency symbol (e.g., 'DOGE').
            currency (str): Quote currency (e.g., 'USD').

        Returns:
            float: The latest price, or None if the request fails.
        """
        pair = f"{symbol}/{currency}".upper()
        kraken_pair = self.hardcoded_pairs.get(pair)

        if not kraken_pair:
            logger.warning(f"Pair {pair} not found in hardcoded pairs.")
            return None

        endpoint = "/0/public/Ticker"
        params = {"pair": kraken_pair}

        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()

            if "result" in data:
                ticker = list(data["result"].keys())[0]
                price = float(data["result"][ticker]["c"][0])
                logger.info(f"Fetched price for {pair} from Kraken: {price}")
                return price
            else:
                logger.warning(f"Unexpected response format from Kraken: {data}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from Kraken: {e}")
            return None
