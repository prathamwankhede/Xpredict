# pyrefly: ignore [missing-import]
import sqlite3
import datetime
import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional

import bet_placing
import market_resolution
import clob_engine

app = FastAPI(title="Prediction Market & CLOB API")

# --- Pydantic Models for CLOB ---

class OrderRequest(BaseModel):
    user_id: str
    side: str = Field(..., pattern="^(buy|sell)$", description="Must be 'buy' or 'sell'")
    outcome: str = Field(..., pattern="^(yes|no)$", description="Must be 'yes' or 'no'")
    order_type: str = Field("limit", pattern="^(limit|market)$", description="Must be 'limit' or 'market'")
    price: float = Field(..., ge=0.01, le=0.99, description="Price in range 0.01 to 0.99")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

# --- Existing TWPM Pari-Mutuel Endpoints ---

@app.get("/markets/{market_id}/resolution")
def read_market_resolution(market_id: str):
    db = sqlite3.connect('bsname.db')
    resolution = market_resolution.get_market_resolution(db, market_id)
    db.close()
    if resolution is not None:
        return {"market_id": market_id, "resolution": resolution}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found or not resolved yet."
        )

@app.get("/markets/{market_id}/bets")
def read_market_bets(market_id: str):
    db = sqlite3.connect('bsname.db')
    bets = bet_placing.getBets(db, market_id)
    db.close()
    return {"market_id": market_id, "bets": [dict(bet) for bet in bets]}

@app.get("/markets/{market_id}/bets/{bet_id}")
def read_bet(market_id: str, bet_id: str):
    db = sqlite3.connect('bsname.db')
    bet = bet_placing.getBet(db, bet_id)
    db.close()
    if bet is not None and bet['market_id'] == market_id:
        return {"bet_id": bet_id, "market_id": market_id, "bet": dict(bet)}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found for the specified market."
        )

# --- New CLOB Endpoints ---

@app.post("/markets/{market_id}/orders", status_code=status.HTTP_201_CREATED)
def place_order(market_id: str, order_req: OrderRequest):
    """
    Places a new limit/market order on the CLOB engine for the specified market.
    Adjusts margin balances and matches orders atomically.
    """
    success, result = clob_engine.process_order(
        db_path='bsname.db',
        market_id=market_id,
        user_id=order_req.user_id,
        side=order_req.side,
        outcome=order_req.outcome,
        order_type=order_req.order_type,
        price=order_req.price,
        quantity=order_req.quantity
    )
    if success:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to process order.")
        )

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str):
    """
    Cancels an open or partially filled order, releasing locked margin balance.
    """
    success, result = clob_engine.cancel_order('bsname.db', order_id)
    if success:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to cancel order.")
        )

@app.get("/markets/{market_id}/orderbook")
def read_orderbook(market_id: str):
    """
    Returns the aggregated L2 orderbook bids and asks for YES and NO outcomes.
    """
    return clob_engine.get_orderbook('bsname.db', market_id)

@app.get("/users/{user_id}/positions")
def read_user_positions(user_id: str):
    """
    Retrieves all open share positions (YES/NO shares, average prices) for a user.
    """
    db = sqlite3.connect('bsname.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        SELECT market_id, shares_yes, shares_no, avg_price_yes, avg_price_no, updated_at
        FROM user_positions
        WHERE user_id = ?;
    """, (user_id,))
    rows = cursor.fetchall()
    db.close()
    return {"user_id": user_id, "positions": [dict(row) for row in rows]}

@app.get("/users/{user_id}/balance")
def read_user_balance(user_id: str):
    """
    Retrieves the available cash balance of a user.
    """
    db = sqlite3.connect('bsname.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_id,))
    row = cursor.fetchone()
    db.close()
    if row:
        return {"user_id": user_id, "balance": row["balance"]}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

@app.get("/markets/{market_id}/trades")
def read_market_trades(market_id: str):
    """
    Returns historical trades executed on the CLOB engine for a given market.
    """
    db = sqlite3.connect('bsname.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, buyer_id, seller_id, outcome, price, shares, maker_order_id, taker_order_id, created_at
        FROM trades
        WHERE market_id = ?
        ORDER BY created_at DESC;
    """, (market_id,))
    rows = cursor.fetchall()
    db.close()
    return {"market_id": market_id, "trades": [dict(row) for row in rows]}

@app.get("/users/{user_id}/orders")
def read_user_orders(user_id: str):
    """
    Retrieves order execution history (open, filled, cancelled) for a user.
    """
    db = sqlite3.connect('bsname.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, market_id, side, outcome, type, price, quantity, filled_quantity, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC;
    """, (user_id,))
    rows = cursor.fetchall()
    db.close()
    return {"user_id": user_id, "orders": [dict(row) for row in rows]}


