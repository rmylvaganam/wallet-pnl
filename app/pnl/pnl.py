import argparse
import pandas as pd
import requests
from ..database.database_access import DatabaseAccess
from datetime import datetime, timedelta
from decimal import Decimal

class Wallet:
    def __init__(self, address: str, db_access: DatabaseAccess) -> None:
        self.address = address
        self.db_access = db_access
        self.start_date: datetime = datetime.now() - timedelta(days=7)
        self.end_date = datetime.now()
        self.balance = self.get_starting_balance()
        self.historical_data = {}
        self.preload_historical_data()
        self.value = self.calculate_value(self.start_date)

    def fetch_transactions(self) -> pd.DataFrame:
        """
        Fetches the transaction history of the wallet from a specified API endpoint.

        This method sends a POST request to the API with the wallet's address, retrieves the transaction history,
        and formats it into a pandas DataFrame. The transactions are sorted by 'block_timestamp' in ascending order
        and the timestamp is converted to a datetime object.

        Returns:
            A pandas DataFrame containing the transaction history with columns for token address, balance, block timestamp, and token ID.
        """
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': '5jwLBV9oVitGnSfkGl6rp5hhJzDbBvoKa-4KllVq5L4CoxfIv_-AT8jrNblF16YhXBKiZkdqzG16ZZSZW4m8CA',
        }
        data = {
            'address': self.address,
        }
        response = requests.post(
            'https://api.allium.so/api/v1/explorer/queries/UWHFUe3BPTFpd7EDVIiI/run',
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        wallet_info = response.json()

        if 'data' not in wallet_info:
            raise ValueError("Expected 'data' key in the API response")
        transactions = pd.DataFrame(wallet_info['data']).sort_values(by=['block_timestamp']).reset_index(drop=True)
        transactions['block_timestamp'] = pd.to_datetime(transactions['block_timestamp'], format='%Y-%m-%dT%H:%M:%S')

        return transactions
    
    def get_starting_balance(self) -> dict[str, Decimal]:
        """
        Calculates the initial balance of each token in the wallet at the start date.
        
        Returns:
            A dictionary mapping each token ID to its balance as a Decimal.
        """
        transactions = self.fetch_transactions()

        wallet_balance = dict()
        for _, entry in transactions.iterrows():
            if entry['block_timestamp'] <= self.start_date:
                if entry['token_id'] is not None:
                    wallet_balance[entry['token_id']] = entry['balance']
            else:
                return wallet_balance
        return wallet_balance
    
    def preload_historical_data(self) -> None:
        """
        Preloads historical price data for each coin in the wallet's balance from the database.
        The data is stored in `self.historical_data`.
        """
        coins = list(self.balance.keys())
        historical_data = self.db_access.fetch_historical_data(coins, self.start_date, datetime.now())
        
        self.historical_data = {coin: [] for coin in coins}
        for coin_id, timestamp, price_usd in historical_data:
            if coin_id in self.historical_data:
                self.historical_data[coin_id].append((timestamp, price_usd))

    def binary_search(self, historical_data, timestamp):
        """
        Performs a binary search to find the closest historical price to a given timestamp.

        Parameters:
            historical_data (list[tuple[datetime, Decimal]]): The list of tuples containing timestamps and prices.
            timestamp (datetime): The timestamp for which the closest historical price is needed.

        Returns:
            The closest historical price as a Decimal, or None if no price is available before the timestamp.
        """
        left, right = 0, len(historical_data) - 1
        while left <= right:
            mid = (left + right) // 2
            if historical_data[mid][0] == timestamp:
                return historical_data[mid][1]
            elif historical_data[mid][0] < timestamp:
                left = mid + 1
            else:
                right = mid - 1
        # If the given timestamp is earlier than all entries, return None
        if right < 0:
            return None
        # Return the most recent price if the exact timestamp isn't found
        return historical_data[right][1]
    
    def calculate_value(self, timestamp: datetime) -> Decimal:
        """
        Calculates the total value of the wallet at a specific timestamp.

        Parameters:
            timestamp (datetime): The timestamp for which the wallet value is calculated.

        Returns:
            The total value of the wallet at the given timestamp as a Decimal.
        """
        value = Decimal(0.0)
        for coin, balance in self.balance.items():
            historical_data = self.historical_data.get(coin, [])
            price_usd = self.binary_search(historical_data, timestamp)
            if price_usd is not None:
                value += Decimal(balance) * price_usd
            else:
                print(f"No historical price avaiable for {coin} at/before {timestamp}.")
        return value

    def calculate_hourly_pnl(self) -> pd.DataFrame:
        """
        Calculates the hourly Profit & Loss (PnL) for the wallet over the period from `self.start_date` to `self.end_date`.

        Returns:
            A pandas DataFrame containing the timestamp and PnL for each hour in the period.
        """
        current_time, start_value = self.start_date, self.value
        pnl_data = []

        while current_time <= self.end_date:
            current_value = self.calculate_value(current_time)
            pnl = current_value - start_value
            pnl_data.append({'timestamp': current_time, 'pnl': pnl})
            current_time += timedelta(hours=1)
        
        pnl_df = pd.DataFrame(pnl_data)
        return pnl_df

def calculate_pnl(wallet_address):
    db_params = {
        "dbname": "wallet_pnl",
        "user": "myuser",
        "password": "mypassword",
        "host": "localhost"
    }
    with DatabaseAccess(db_params) as db_access:
        wallet = Wallet(wallet_address, db_access)  # Assuming Wallet class takes wallet_address as a parameter
        pnl_df = wallet.calculate_hourly_pnl()
        print(pnl_df)
        return pnl_df

def main():
    parser = argparse.ArgumentParser(description="Calculate PnL for a wallet address.")
    parser.add_argument("wallet_address", help="The wallet address to calculate PnL for.")
    args = parser.parse_args()

    calculate_pnl(args.wallet_address)   

if __name__ == "__main__":
    main()