CREATE TABLE IF NOT EXISTS coins (
    coin_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_data (
    coin_id VARCHAR(255) NOT NULL REFERENCES coins(coin_id),
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    price_usd NUMERIC,
    PRIMARY KEY (coin_id, timestamp)
);

GRANT ALL PRIVILEGES ON TABLE coins TO myuser;
GRANT ALL PRIVILEGES ON TABLE historical_data TO myuser;
