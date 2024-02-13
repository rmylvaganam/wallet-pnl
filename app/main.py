from fastapi import FastAPI
from app.pnl.pnl import calculate_pnl as calculate_hourly_pnl

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello world!"}

@app.post("/calculate_pnl")
async def calculate_pnl(wallet_address: str):
    pnl_data = calculate_hourly_pnl(wallet_address)
    return {"wallet_address": wallet_address, "pnl": pnl_data}