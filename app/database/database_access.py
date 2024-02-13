from datetime import datetime
import psycopg2
from psycopg2 import extras

class DatabaseAccess:
    """
    Provides access to the database for fetching historical cryptocurrency data.
    
    Attributes:
        db_params (dict): Database connection parameters.
        db_conn (psycopg2.connection | None): A psycopg2 connection object to the database, initialized as None and set upon entering the context.
    """
    
    def __init__(self, db_params: dict) -> None:
        """
        Initializes the DatabaseAccess class with database connection parameters.
        
        Parameters:
            db_params (dict): Parameters required to establish a database connection, including dbname, user, password, and host.
        """
        self.db_params = db_params
        self.db_conn: psycopg2.connect = None

    def __enter__(self) -> 'DatabaseAccess':
        """
        Establishes a database connection when entering the context manager.
        
        Returns:
            DatabaseAccess: Returns an instance of itself, with the database connection established.
        """
        self.db_conn = psycopg2.connect(**self.db_params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the database connection upon exiting the context manager.
        
        Parameters:
            exc_type: Exception type, if any occurred within the context.
            exc_val: Exception value, if any occurred within the context.
            exc_tb: Exception traceback, if any occurred within the context.
        """
        if self.db_conn:
            self.db_conn.close()
    
    def fetch_historical_data(self, coins: list[str], start_date: datetime, 
                              end_date: datetime) -> list[tuple]:
        """
        Fetches historical price data for specified cryptocurrencies within a given time range.
        
        Parameters:
            coins (list[str]): A list of cryptocurrency identifiers (e.g., 'bitcoin', 'ethereum') for which historical data is to be fetched.
            start_date (datetime): The start date and time of the historical data range.
            end_date (datetime): The end date and time of the historical data range.
        
        Returns:
            list[tuple]: A list of tuples containing the historical data, with each tuple consisting of (coin_id, timestamp, price_usd).
        """
        query = """
        SELECT coin_id, timestamp, price_usd
        FROM historical_data
        WHERE coin_id = ANY(%s) AND timestamp BETWEEN %s AND %s
        ORDER BY coin_id, timestamp;
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(query, (coins, start_date, end_date))
            result = cursor.fetchall()
        return result
    
    def insert_coin_data(self, coin_data: list[dict]) -> None:
        """
        Inserts coin metadata into the database. If a coin already exists, the operation is skipped.

        Parameters:
            coin_data (List[Dict[str, Any]]): A list of dictionaries, each containing the 'id', 'name', and 'symbol' of a coin.

        Returns:
            None
        """
        data = [(coin['id'], coin['name'], coin['symbol']) for coin in coin_data]
        query = """
            INSERT INTO coins (coin_id, name, symbol) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (coin_id) DO NOTHING;
        """
        with self.db_conn.cursor() as cursor:
            extras.execute_batch(cursor, query, data)
        self.db_conn.commit()

    def insert_historical_data(self, coin_id: str, historical_data: list[list[float]]) -> None:
        """
        Inserts historical price data for a specific coin into the database. 
        If an entry for the specific coin and timestamp already exists, the operation is skipped.

        Parameters:
            coin_id (str): The identifier of the cryptocurrency.
            historical_data (List[List[float]]): A list of [timestamp, price] pairs, where 'timestamp' is in milliseconds since epoch and 'price' is the price in USD.

        Returns:
            None
        """
        data = [(coin_id, datetime.fromtimestamp(timestamp / 1000.0), price) for timestamp, price in historical_data]
        query = """
            INSERT INTO historical_data (coin_id, timestamp, price_usd) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (coin_id, timestamp) DO NOTHING;
        """
        with self.db_conn.cursor() as cursor:
            extras.execute_batch(cursor, query, data)
        self.db_conn.commit()