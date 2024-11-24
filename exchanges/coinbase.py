# exchanges/coinbase.py

import logging
import requests
import time
import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv
import json
import logging

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

class CoinbaseAPI:
    def __init__(self):
        """
        Initialize Coinbase API class with endpoints, keys, and secrets.
        """
        self.price_url = "https://api.coinbase.com/v2"  # General API for prices
        self.pair_url = "https://api.exchange.coinbase.com"  # API for trading pairs and orders

        self.api_key = os.getenv("COINBASE_API_KEY")
        self.api_secret = os.getenv("COINBASE_API_SECRET")
        self.api_passphrase = os.getenv("COINBASE_API_PASSPHRASE")

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
                    logger.error(f"Failed to fetch price from Coinbase after {retries} attempts.")
                    return None

    def get_trading_pairs(self):
        """
        Fetch all trading pairs available on Coinbase Pro.
        
        Returns:
            list: A list of trading pairs (e.g., ['BTC-USD', 'ETH-USD']).
        """
        endpoint = f"{self.pair_url}/products"
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            data = response.json()
            pairs = [product['id'] for product in data if product['status'] == 'online']
            logger.info(f"Fetched {len(pairs)} trading pairs from Coinbase Pro.")
            return pairs
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trading pairs from Coinbase Pro: {e}")
            return []

    def place_order(self, side, price, size, product_id="BTC-USD"):
        """
        Place a limit order on Coinbase Pro.

        Args:
            side (str): 'buy' or 'sell'.
            price (float): Price per unit in quote currency.
            size (float): Order size in base currency.
            product_id (str): Trading pair (e.g., 'BTC-USD').

        Returns:
            dict: Order confirmation response from Coinbase Pro, or None if the request fails.
        """
        timestamp = str(int(time.time()))
        request_path = "/orders"
        body = {
            'product_id': product_id,
            'side': side,
            'price': f"{price:.4f}",
            'size': f"{size:.2f}",
            'type': 'limit',
        }

        body_json = json.dumps(body)
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': self._generate_signature(timestamp, 'POST', request_path, body_json),
            'CB-ACCESS-PASSPHRASE': self.api_passphrase,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(f"{self.pair_url}{request_path}", headers=headers, data=body_json)
            response.raise_for_status()
            order_response = response.json()
            logger.info(f"Order placed on Coinbase Pro: {order_response}")
            return order_response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing order on Coinbase Pro: {e}")
            return None

    def _generate_signature(self, timestamp, method, request_path, body):
        """
        Generate HMAC SHA-256 signature for Coinbase Pro API authentication.

        Args:
            timestamp (str): Unix timestamp of the request.
            method (str): HTTP method (e.g., 'POST', 'GET').
            request_path (str): API endpoint path.
            body (str): JSON body as a string.

        Returns:
            str: The generated signature.
        """
        message = f"{timestamp}{method}{request_path}{body or ''}"
        secret = base64.b64decode(self.api_secret)
        signature = hmac.new(secret, message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()
