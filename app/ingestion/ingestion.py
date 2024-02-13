import requests
import os
from ..database.database_access import DatabaseAccess
from time import sleep, time
from collections import deque
from typing import Any

API_KEY = os.environ.get('COINGECKO_API_KEY')

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def wait(self):
        now = time()
        while self.calls and now - self.calls[0] > self.period:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            sleep(sleep_time)
        self.calls.append(time())

# CoinGecko demo account: 30 calls per 60 seconds
rate_limiter = RateLimiter(30, 60)

def fetch_top_10_tokens() -> list[dict[str, Any]]:
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&x_cg_demo_api_key={API_KEY}"
    response = requests.get(url)
    return response.json()

def fetch_historical_data(coin_id: str) -> dict[str, list[list[int, float]]]:
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7&x_cg_demo_api_key={API_KEY}"
    response = requests.get(url)
    return response.json()

def run_ingestion():
    db_params = {
        "dbname": "wallet_pnl",
        "user": "myuser",
        "password": "mypassword",
        "host": "localhost"
    }
    
    try:
        top_coins = fetch_top_10_tokens()
        with DatabaseAccess(db_params) as db_access:
            db_access.insert_coin_data(top_coins)
            for coin in top_coins:
                coin_id = coin['id']
                rate_limiter.wait()
                historical_data = fetch_historical_data(coin_id)
                prices = historical_data.get("prices", [])
                if prices:
                    db_access.insert_historical_data(coin_id, prices)
                    print(f'Inserted historical data for {coin_id}')
                else:
                    print(f"No historical data found for {coin_id}")
        print("Successfully inserted top 10 coins and their historical data.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_ingestion()
