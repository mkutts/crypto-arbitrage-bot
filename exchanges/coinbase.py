import logging
import requests
import time

logger = logging.getLogger(__name__)

class CoinbaseAPI:
    def __init__(self):
        """
        Initialize Coinbase API class with endpoints.
        """
        self.price_url = "https://api.coinbase.com/v2"  # General API for prices
        self.products_url = "https://api.exchange.coinbase.com/products"  # API for trading pairs

    def get_price(self, symbol, currency):
        """
        Fetch the latest price for a given trading pair from Coinbase.
        
        Args:
            symbol (str): Cryptocurrency symbol (e.g., 'BTC').
            currency (str): Quote currency (e.g., 'USD').

        Returns:
            float: The latest price, or None if the request fails.
        """
        pair = f"{symbol}-{currency}"
        endpoint = f"{self.price_url}/prices/{pair}/spot"
        retries = 3

        for attempt in range(retries):
            try:
                response = requests.get(endpoint)
                response.raise_for_status()
                price_data = response.json()
                price = float(price_data['data']['amount'])
                logger.info(f"Fetched {symbol}/{currency} price from Coinbase: {price}")
                return price
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for Coinbase price fetch: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch price for {symbol}/{currency} after {retries} attempts.")
                    return None

    def get_trading_pairs(self):
        """
        Fetch all trading pairs available on Coinbase Pro.
        
        Returns:
            list: A list of trading pairs (e.g., ['BTC-USD', 'ETH-USD']).
        """
        try:
            response = requests.get(self.products_url)
            response.raise_for_status()
            data = response.json()
            pairs = [product['id'] for product in data if product['status'] == 'online']
            logger.info(f"Fetched {len(pairs)} trading pairs from Coinbase.")
            return pairs
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trading pairs from Coinbase: {e}")
            return []
