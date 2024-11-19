import requests
import time
import hmac
import hashlib
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self):
        self.base_url = "https://api.binance.us/api/v3"
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")

    def _sign_request(self, params):
        """
        Signs the request with HMAC SHA256.
        """
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def get_price(self, symbol, currency):
        """
        Fetches the latest price for the given trading pair.
        """
        # Map USD to USDT for Binance
        if currency.upper() == "USD":
            currency = "USDT"  # Binance does not use USD directly

        pair = f"{symbol.upper()}{currency.upper()}"

        try:
            response = requests.get(f"{self.base_url}/ticker/price", params={"symbol": pair})
            response.raise_for_status()
            data = response.json()

            if "price" not in data:
                logger.error(f"Invalid response from Binance for pair {pair}: {data}")
                return None

            price = float(data["price"])
            logger.info(f"Fetched {symbol}/{currency} price from Binance: {price}")
            return price
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from Binance: {e}")
            return None


    def place_order(self, side, price, quantity, symbol="BTCUSDT"):
        """
        Places a limit order on Binance.
        """
        endpoint = "/order"
        url = f"{self.base_url}{endpoint}"
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.6f}",
            "price": f"{price:.2f}",
            "timestamp": int(time.time() * 1000),
        }
        headers = {"X-MBX-APIKEY": self.api_key}
        params = self._sign_request(params)
        try:
            response = requests.post(url, headers=headers, params=params)
            response.raise_for_status()
            logger.info(f"Order placed on Binance: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing order on Binance: {e}")
            return None
