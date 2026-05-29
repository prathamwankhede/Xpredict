# pyrefly: ignore [missing-import]
from fastapi import FastAPI
app = FastAPI()
import bet_placing
import market_resolution
import sqlite3
import datetime
import logging
from functools import lru_cache

# TODO: add auth tokens for users
# TODO: add deadlock handling for db transactions

@app.get("/markets/{market_id}/resolution")
def read_market_resolution(market_id: str):
    db = sqlite3.connect('bsname.db')
    resolution = market_resolution.get_market_resolution(db, market_id)
    db.close()
    if resolution is not None:
        return {"market_id": market_id, "resolution": resolution}
    else:
        return {"error": "Market not found or not resolved yet."}
    
@app.get("/markets/{market_id}/bets")
def read_market_bets(market_id: str):
    db =sqlite3.connect('bsname.db')
    bets = bet_placing.getBets(db, market_id)
    db.close()
    return {"market_id": market_id, "bets": [dict(bet) for bet in bets]}

@app.get("/markets/{market_id}/bets/{bet_id}")
def read_bet(market_id: str, bet_id: str):
    db =sqlite3.connect('bsname.db')
    bet = bet_placing.getBet(db, bet_id)
    db.close()
    if bet is not None and bet['market_id'] == market_id:
        return {"bet_id": bet_id, "market_id": market_id, "bet": dict(bet)}
    else:
        return {"error": "Bet not found for the specified market."}

