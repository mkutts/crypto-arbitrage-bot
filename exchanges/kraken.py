# exchanges/kraken.py

import requests
import time
import hashlib
import hmac
import base64
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class KrakenAPI:
    def __init__(self):
        self.api_key = os.getenv("KRAKEN_API_KEY")
        self.api_secret = os.getenv("KRAKEN_API_SECRET")
        self.base_url = "https://api.kraken.com"

    def _sign_request(self, endpoint, data):
        """
        Generates the required HMAC SHA-512 signature for Kraken API requests.
        """
        data['nonce'] = str(int(1000 * time.time()))
        postdata = data['nonce'] + '&'.join([f"{key}={value}" for key, value in data.items()])
        encoded = hashlib.sha256(postdata.encode()).digest()
        message = endpoint.encode() + encoded
        secret = base64.b64decode(self.api_secret)
        signature = hmac.new(secret, message, hashlib.sha512).digest()
        return base64.b64encode(signature).decode()

    def get_price(self, symbol, currency):
        """
        Fetches the latest price for the chosen trading pair from Kraken.
        """
        pair = f"{symbol}{currency}".upper()
        if symbol.upper() == "DOGE":  # Adjust for Kraken's naming convention
            pair = "XDGUSD"
        elif symbol.upper() == "ETH":
            pair = "XETHZUSD"  # ETH/USD pair in Kraken's format
        elif symbol.upper() == "BTC":
            pair = "XXBTZUSD"  # BTC/USD pair in Kraken's format
        
        endpoint = "/0/public/Ticker"
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params={"pair": pair})
            response.raise_for_status()
            data = response.json()
            if "result" in data:
                ticker = list(data["result"].keys())[0]  # Get the correct key for the pair
                price = float(data["result"][ticker]['c'][0])
                logger.info(f"Fetched {symbol}/{currency} price from Kraken: {price}")
                return price
            else:
                logger.warning(f"Unexpected response format from Kraken: {data}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from Kraken: {e}")
            return None


    def place_order(self, side, price, volume, pair="DOGEUSD"):
        """
        Places a limit order on Kraken for the specified pair.
        """
        endpoint = "/0/private/AddOrder"

        # Ensure volume meets minimum requirements
        if pair.upper() == "DOGEUSD" and volume < 50:  # Example: Minimum 50 DOGE for DOGE/USD
            logger.error(f"Volume {volume} is below the minimum required for {pair}. Adjusting volume.")
            volume = 50.0

        data = {
            "pair": pair.upper(),
            "type": side.lower(),
            "ordertype": "limit",
            "price": f"{price:.4f}",
            "volume": f"{volume:.6f}",
        }
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign_request(endpoint, data),
        }

        try:
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, data=data)
            response.raise_for_status()
            logger.info(f"Order placed on Kraken: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing order on Kraken: {e}")
            return None


    def get_balance(self):
        """
        Fetches the account balance from Kraken.
        """
        endpoint = "/0/private/Balance"
        data = {}
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign_request(endpoint, data)
        }
        
        try:
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, data=data)
            response.raise_for_status()
            balance = response.json()
            logger.info(f"Account balance fetched from Kraken: {balance}")
            return balance
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching balance from Kraken: {e}")
            return None
    
    def get_minimum_volume(self, pair):
        """
        Fetches the minimum volume required for a trading pair from Kraken.
        """
        endpoint = "/0/public/AssetPairs"
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            data = response.json()

            if pair.upper() in data["result"]:
                min_volume = float(data["result"][pair.upper()]["ordermin"])
                logger.info(f"Minimum volume for {pair.upper()} is {min_volume}")
                return min_volume
            else:
                logger.warning(f"Pair {pair.upper()} not found in Kraken asset pairs.")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching minimum volume from Kraken: {e}")
            return None

