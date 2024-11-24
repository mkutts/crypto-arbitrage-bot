import pandas as pd

# Load the merged CSV
input_file = "merged_ETH_USD.csv"  # Adjust the file name if needed
output_file = "simplified_ETH_USD.csv"

# Load the data
data = pd.read_csv(input_file)

# Extract and rename relevant columns
simplified_data = data[["timestamp", "close_kraken", "close_coinbase"]].rename(
    columns={
        "close_kraken": "kraken_price",
        "close_coinbase": "coinbase_price"
    }
)

# Drop rows with missing data (optional but recommended)
simplified_data = simplified_data.dropna()

# Save the simplified CSV
simplified_data.to_csv(output_file, index=False)

print(f"Simplified CSV saved as {output_file}")
