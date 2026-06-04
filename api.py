# pyrefly: ignore [missing-import]
import sqlite3
import datetime
import logging
import contextlib
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional

import bet_placing
import market_resolution
import clob_engine

app = FastAPI(title="Prediction Market & CLOB API")

DB_PATH = 'bsname.db'

#TODO: add auth tokens for users

@contextlib.contextmanager
def get_db():
    """
    Context manager to safely manage sqlite3 database connection lifecycles,
    ensuring connections are closed even on exceptions.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# --- Pydantic Models for CLOB ---

class OrderRequest(BaseModel):
    user_id: str
    side: str = Field(..., pattern="^(buy|sell)$", description="Must be 'buy' or 'sell'")
    outcome: str = Field(..., pattern="^(yes|no)$", description="Must be 'yes' or 'no'")
    order_type: str = Field("limit", pattern="^(limit|market)$", description="Must be 'limit' or 'market'")
    price: float = Field(..., ge=0.01, le=0.99, description="Price in range 0.01 to 0.99")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

# --- Existing TWPM Pari-Mutuel Endpoints ---

@app.get("api/v1/markets/{market_id}/resolution")
def read_market_resolution(market_id: str):
    with get_db() as db:
        resolution = market_resolution.get_market_resolution(db, market_id)
    if resolution is not None:
        return {"market_id": market_id, "resolution": resolution}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found or not resolved yet."
        )

@app.get("api/v1/markets/{market_id}/bets")
def read_market_bets(market_id: str):
    with get_db() as db:
        bets = bet_placing.getBets(db, market_id)
    return {"market_id": market_id, "bets": [dict(bet) for bet in bets]}

@app.get("api/v1/markets/{market_id}/bets/{bet_id}")
def read_bet(market_id: str, bet_id: str):
    with get_db() as db:
        bet = bet_placing.getBet(db, bet_id)
    if bet is not None and bet['market_id'] == market_id:
        return {"bet_id": bet_id, "market_id": market_id, "bet": dict(bet)}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found for the specified market."
        )

# --- New CLOB Endpoints ---

@app.post("api/v1/markets/{market_id}/orders", status_code=status.HTTP_201_CREATED)
def place_order(market_id: str, order_req: OrderRequest):
    """
    Places a new limit/market order on the CLOB engine for the specified market.
    Adjusts margin balances and matches orders atomically.
    """
    success, result = clob_engine.process_order(
        db_path=DB_PATH,
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

@app.post("api/v1/orders/{order_id}/cancel")
def cancel_order(order_id: str):
    """
    Cancels an open or partially filled order, releasing locked margin balance.
    """
    success, result = clob_engine.cancel_order(DB_PATH, order_id)
    if success:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to cancel order.")
        )

@app.get("api/v1/markets/{market_id}/orderbook")
def read_orderbook(market_id: str):
    """
    Returns the aggregated L2 orderbook bids and asks for YES and NO outcomes.
    """
    return clob_engine.get_orderbook(DB_PATH, market_id)

@app.get("api/v1/users/{user_id}/positions")
def read_user_positions(user_id: str, market_id: Optional[str] = None):
    """
    Retrieves open share positions for a user, optionally filtered by market.
    """
    with get_db() as db:
        cursor = db.cursor()
        if market_id:
            cursor.execute("""
                SELECT market_id, shares_yes, shares_no, avg_price_yes, avg_price_no, updated_at
                FROM user_positions
                WHERE user_id = ? AND market_id = ?;
            """, (user_id, market_id))
        else:
            cursor.execute("""
                SELECT market_id, shares_yes, shares_no, avg_price_yes, avg_price_no, updated_at
                FROM user_positions
                WHERE user_id = ?;
            """, (user_id,))
        rows = cursor.fetchall()
    return {"user_id": user_id, "positions": [dict(row) for row in rows]}

@app.get("api/v1/users/{user_id}/balance")
def read_user_balance(user_id: str):
    """
    Retrieves the available cash balance of a user.
    """
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
    if row:
        return {"user_id": user_id, "balance": row["balance"]}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

@app.get("api/v1/markets/{market_id}/trades")
def read_market_trades(market_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """
    Returns historical trades executed on the CLOB engine for a given market with pagination.
    """
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, buyer_id, seller_id, outcome, price, shares, maker_order_id, taker_order_id, created_at
            FROM trades
            WHERE market_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
        """, (market_id, limit, offset))
        rows = cursor.fetchall()
    return {"market_id": market_id, "trades": [dict(row) for row in rows]}

@app.get("api/v1/users/{user_id}/orders")
def read_user_orders(user_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """
    Retrieves order execution history (open, filled, cancelled) for a user with pagination.
    """
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, market_id, side, outcome, type, price, quantity, filled_quantity, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
        """, (user_id, limit, offset))
        rows = cursor.fetchall()
    return {"user_id": user_id, "orders": [dict(row) for row in rows]}


