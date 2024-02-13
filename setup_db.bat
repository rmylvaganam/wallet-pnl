@echo off
echo Resetting the PostgreSQL environment...

set PSQL_PATH=C:\Program Files\PostgreSQL\16\bin

:: Drop the existing database (if exists) and the user (if exists)
"%PSQL_PATH%\psql" -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'wallet_pnl';"
"%PSQL_PATH%\psql" -U postgres -c "DROP DATABASE IF EXISTS wallet_pnl;"
"%PSQL_PATH%\psql" -U postgres -c "DROP ROLE IF EXISTS myuser;"

:: Create the user
"%PSQL_PATH%\psql" -U postgres -c "CREATE USER myuser WITH PASSWORD 'mypassword'"

:: Create the database
"%PSQL_PATH%\psql" -U postgres -c "CREATE DATABASE wallet_pnl WITH OWNER myuser"

:: Run the setup SQL script to create tables and grant privileges
"%PSQL_PATH%\psql" -U postgres -d wallet_pnl -f setup_db.sql

echo Database reset and setup completed successfully.
