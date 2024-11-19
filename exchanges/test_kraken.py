# test_kraken.py

from kraken import KrakenAPI  # Assuming the import path is correct

def test_get_balance(api):
    print("Testing get_balance...")
    api.get_balance()
    print("Balance test completed.\n")

def test_get_price(api):
    print("Testing get_price for DOGE/USD...")
    price = api.get_price("DOGE", "USD")
    if price is not None:
        print(f"Fetched DOGE/USD price: {price}")
    else:
        print("Failed to fetch DOGE/USD price.")
    print("Price test completed.\n")

def test_place_order(api):
    print("Testing place_order...")
    
    # Adjusted volume for Kraken's minimum requirements
    test_side = "buy"  # You can change to "sell" for testing selling functionality
    test_price = 0.38  # Example price, set close to the current market price
    test_volume = 50   # Adjusted to meet Kraken's minimum order size for DOGE

    print(f"Placing a {test_side} order for {test_volume} DOGE at ${test_price} each.")
    api.place_order(test_side, test_price, test_volume)
    print("Order test completed.\n")

if __name__ == "__main__":
    kraken_api = KrakenAPI()
    
    print("Running Kraken API tests...\n")
    
    test_get_balance(kraken_api)
    test_get_price(kraken_api)
    test_place_order(kraken_api)
    
    print("Kraken API tests completed.")
