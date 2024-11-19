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
        self.base_url = "https://api.coinbase.com/v2"  # Updated base URL for price data
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.api_secret = os.getenv("COINBASE_API_SECRET")
        self.api_passphrase = os.getenv("COINBASE_API_PASSPHRASE")

    def get_price(self, symbol, currency):
        """
        Fetches the latest price for the chosen cryptocurrency pair from Coinbase.
        Retries the request up to 3 times in case of temporary failures.
        """
        pair = f"{symbol}-{currency}"
        endpoint = f"{self.base_url}/prices/{pair}/spot"
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



    def place_order(self, side, price, size, product_id="DOGE-USD"):
        """
        Places a limit order on Coinbase Advanced Trade for DOGE/USD.
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
            response = requests.post(f"{self.base_url}/api/v3{request_path}", headers=headers, data=body_json)
            response.raise_for_status()
            logger.info(f"Order placed on Coinbase Advanced Trade: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing order on Coinbase Advanced Trade: {e}")

    def _generate_signature(self, timestamp, method, request_path, body):
        """
        Generates the required HMAC SHA-256 signature for Coinbase Advanced Trade API.
        """
        message = f"{timestamp}{method}{request_path}{body or ''}"
        signature = hmac.new(base64.b64decode(self.api_secret), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()
