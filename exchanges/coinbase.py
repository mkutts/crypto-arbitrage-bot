# exchanges/coinbase.py

import requests
import time
import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class CoinbaseAPI:
    def __init__(self):
        self.price_url = "https://api.coinbase.com/v2"  # For fetching prices
        self.pair_url = "https://api.exchange.coinbase.com"  # For fetching pairs

        self.api_key = os.getenv("COINBASE_API_KEY")
        self.api_secret = os.getenv("COINBASE_API_SECRET")
        self.api_passphrase = os.getenv("COINBASE_API_PASSPHRASE")

    def get_price(self, symbol, currency):
        """
        Fetches the latest price for the chosen cryptocurrency pair from Coinbase's general API.
        Retries the request up to 3 times in case of temporary failures.
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
        Fetches all trading pairs available on Coinbase Pro (via the pair API URL).
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
        Places a limit order on Coinbase Pro for the specified trading pair.
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
            logger.info(f"Order placed on Coinbase Pro: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing order on Coinbase Pro: {e}")

    def _generate_signature(self, timestamp, method, request_path, body):
        """
        Generates the required HMAC SHA-256 signature for Coinbase Pro API.
        """
        message = f"{timestamp}{method}{request_path}{body or ''}"
        signature = hmac.new(base64.b64decode(self.api_secret), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()
