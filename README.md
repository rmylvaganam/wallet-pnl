# wallet-pnl

This repo contains code that takes in crypto wallet addresses and calculates hourly PnL's of the last week for this wallet. First top 10 crypto coins (based on market cap) data is ingested into a local database, then the wallet address is used as input to Allium's API to find its transaction history. Based on this historical data, we can calulcate the PnL since the wallet's starting date. In this demo project, we will only look at the PnL of the last seven days however.

## Requirements
- Postgres 16
- CoinGecko API key (https://support.coingecko.com/hc/en-us/articles/21880397454233-User-Guide-How-to-sign-up-for-CoinGecko-Demo-API-and-generate-an-API-key)
- Python 3.0+ (Probably 3.8+, due to some type hints)

## Instructions on project setup
1. Clone the repository and set the current working directory to `../wallet-pnl`
3. Set the Coingecko API key as an environment variable (In Windows: System Properties -> Environment Variables -> User variables -> Add New...). Alternatively can set it through command line `setx COINGECKO_API_KEY=<value>". Demo Account API privileges suffices.
4. Optional: Set up a virtual env
5. Install the python packages from `requirements.txt` using `pip install -r requirements.txt`
6. Run `setup_db.bat` - You will need to fill in your password for the superuser `postgres` several times. *WARNING*: be aware that it cleans slate before setting up the tables, users and privileges, so take a close look at the resources and their names. These resources can be found in `setup_db.sql`.
7. Running the application:      
  a. To run the ingestion process: `python -m app.ingestion.ingestion`     
  b. To run the pnl script: `python -m app.pnl.pnl <wallet_address>`, e.g. `python -m app.pnl.pnl 0x26a016De7Db2A9e449Fe5b6D13190558d6bBCd5F`   
  c. To start the web server: `uvicorn app.main:app --reload`    

## API Endpoints
`/calculate_pnl`: Calculates the hourly PnL for a given wallet address of the past week.  
Query using curl: `curl -X POST "http://localhost:8000/calculate_pnl" -d '{"wallet_address": "<address>"}' (Substitute <address>)
`. Alternatively use the Python requests module. Example in `wallet-pnl/test_api.py`. The output will be a pandas dataframe with a column for the hours and a column for the corresponding pnl's.

## Scalability
A. 10000 tokens would affect:
  (i) ingestion as for each token, we'd need to store the historical data 
  (ii) pnl calculation as more type of wallets are supported, i.e. not just wallets with the top 10 most popular coins. 

Addressing (i): There will be an initial time investment in storing the historical data, but once it's stored, maintaining new updates is trivial. This is commonly done with message queues (for data that does not need instant/near real time processing), such as Kafka and then combined with stream processing for the data that requires real-time data processing. Furthermore, when using batch operations such as batch inserts and good indices, the ingestion of the token data should be relatively fast. If needed, more custom solutions can be considered such as databases optimized for time series data.

Addressing (ii): The PnL calculation can easily suffer from not using more appropriate data structures as there are some operations that can be optimized even further in the demo project. I've done a fair amount of caching, but scaling to 10000 tokens requires much more caching. For instance, since the amount of data that I worked with is relatively low, I didn't use deltas in between balance changes. Suppose on day 1 a wallet consists of coins c1, c2, ... cn, with corresponding balances b1, b2, ..., bn. Most of the days the balances won't change as most people do not day-trade. This means that it's more efficient to calculate PnL based on changes in balance rather than recomputing the total value of the entire wallet. In order to facilitate calculating based on deltas, it would make sense to store the transactions differently from how it's currently stored. There is a sorting operation in the demo project, that I don't think is strictly neccesary (but it makes for a much more complex design). This could be another area for improvement. Caching coin value lookups could would be beneficial too as multiple customers will be looking at approximately similar times. Distribituting the valuation of balances based on coins, could be an interesting approach too, i.e. asynchronously evaluate a wallet's worth based, by dividing the workload on each type of coin held. This would also lead to a more distributed load on the databases. Then there are other ways to address scalability, but it generally boils down to vectorizing/batching operations, caching lookups/computations and finding ways to distribute the workload for asynchronous processing.

B/C PnL with 5 minute granularity & PnLs up to the start of the coins - There are some potential areas for improvements in the demo project, but it's mostly related to caching (even more) values and how much I can store in memory. There is a time sorting operation applied, but if the dataset is already sorted, then the slowest operation in the PnL calculation has a worst case running time of log(N), which means the application is already quite ready to both calculate with higher granularity and to show PnLs up to the start of the coins. It would be a good cost saving feature to store the data in their appropriate storage categories, i.e. cold data (data that is infrequently accessed) should be stored in data storages that are more optimized for storage, usually at the cost of speed of access.
