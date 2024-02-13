import requests

url = "http://localhost:8000/calculate_pnl"
data = {"wallet_address": "0x9bDfefdBc7aBB69aA2B26491b3B4408fE28Af134"}

response = requests.post(url, params=data)

if response.status_code == 200:
    json_response = response.json()
    print(f"PnL: {json_response["pnl"]}")
else:
    print(f"Error: {response.text}")