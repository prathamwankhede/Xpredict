import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import uuid
import datetime
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_clob_api(db_path="bsname.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Setup Temporary Users & Market
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    market_id = str(uuid.uuid4())
    
    print("\n" + "="*50)
    print("STARTING FASTAPI CLOB API INTEGRATION TESTS")
    print("="*50)
    
    try:
        # Create temp users with $1000 balance each
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (?, ?, ?);", (user_a_id, "User_A_API_YES", 1000.0))
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (?, ?, ?);", (user_b_id, "User_B_API_NO", 1000.0))
        
        # Create a temp CLOB market
        cursor.execute("""
            INSERT INTO markets (id, name, started_at, ended_at, estimated_resolution_time, engine_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (market_id, "Will CLOB API Pass Integration Tests?", 
              str(datetime.datetime.now()), str(datetime.datetime.now() + datetime.timedelta(days=1)),
              str(datetime.datetime.now() + datetime.timedelta(days=1)), 'clob', 'open'))
        
        conn.commit()
        print(f"Initialized temporary test market {market_id}")
        
        # ---------------------------------------------------------------------
        # TEST 1: Place a limit order via POST /markets/{market_id}/orders
        # ---------------------------------------------------------------------
        print("\n[TEST 1] Testing Order Placement API...")
        order_payload = {
            "user_id": user_a_id,
            "side": "buy",
            "outcome": "yes",
            "order_type": "limit",
            "price": 0.62,
            "quantity": 10
        }
        response = client.post(f"/api/v1/markets/{market_id}/orders", json=order_payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "open", f"Expected 'open', got {data['status']}"
        order_id = data["order_id"]
        print(">> SUCCESS: Limit order placed successfully.")
        
        # ---------------------------------------------------------------------
        # TEST 2: Check balance via GET /users/{user_id}/balance
        # ---------------------------------------------------------------------
        print("\n[TEST 2] Testing User Balance API...")
        response = client.get(f"/api/v1/users/{user_a_id}/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        balance_data = response.json()
        print(f"User A balance: ${balance_data['balance']:.2f}")
        assert abs(balance_data["balance"] - 993.80) < 0.01, f"Expected 993.80, got {balance_data['balance']}"
        print(">> SUCCESS: Balance matches locked cash subtraction.")
        
        # ---------------------------------------------------------------------
        # TEST 3: Check orderbook via GET /markets/{market_id}/orderbook
        # ---------------------------------------------------------------------
        print("\n[TEST 3] Testing Orderbook Depth API...")
        response = client.get(f"/api/v1/markets/{market_id}/orderbook")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        book = response.json()
        print("Orderbook structure:", book)
        assert book["yes"]["bids"][0] == [0.62, 10], f"Expected bid [0.62, 10], got {book['yes']['bids'][0]}"
        print(">> SUCCESS: Orderbook correctly fetched.")
        
        # ---------------------------------------------------------------------
        # TEST 4: Direct Matching (NO Buy meets NO Sell)
        # ---------------------------------------------------------------------
        print("\n[TEST 4] Testing Direct Order Matching API (YES Sell meets YES Buy)...")
        # Pre-seed User B holding 5 YES shares
        cursor.execute("""
            INSERT INTO user_positions (user_id, market_id, shares_yes, shares_no, avg_price_yes, avg_price_no)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_b_id, market_id, 5, 0, 0.60, 0.0))
        conn.commit()
        
        # B places a sell order to trigger direct matching
        sell_payload = {
            "user_id": user_b_id,
            "side": "sell",
            "outcome": "yes",
            "order_type": "limit",
            "price": 0.60,
            "quantity": 5
        }
        response = client.post(f"/api/v1/markets/{market_id}/orders", json=sell_payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        match_data = response.json()
        assert match_data["status"] == "filled", f"Expected 'filled', got {match_data['status']}"
        assert len(match_data["trades"]) == 1, f"Expected 1 trade, got {len(match_data['trades'])}"
        trade = match_data["trades"][0]
        print(f"Trade exec: {trade['shares']} shares at ${trade['price']:.2f}")
        assert trade["price"] == 0.62, f"Expected execution at Maker's price 0.62, got {trade['price']}"
        print(">> SUCCESS: Direct match executed successfully.")
        
        # ---------------------------------------------------------------------
        # TEST 5: Check Positions via GET /users/{user_id}/positions
        # ---------------------------------------------------------------------
        print("\n[TEST 5] Testing User Positions API...")
        response = client.get(f"/api/v1/users/{user_a_id}/positions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        pos_data = response.json()
        print(f"User A Positions: {pos_data['positions']}")
        assert pos_data["positions"][0]["shares_yes"] == 5, f"Expected 5 shares_yes, got {pos_data['positions'][0]['shares_yes']}"
        print(">> SUCCESS: Positions successfully matched and updated.")
        
        # ---------------------------------------------------------------------
        # TEST 6: Check Trades via GET /markets/{market_id}/trades
        # ---------------------------------------------------------------------
        print("\n[TEST 6] Testing Market Trades History API...")
        response = client.get(f"/api/v1/markets/{market_id}/trades")
        assert response.status_code == 200, f"Expected 200"
        trades_data = response.json()
        print(f"Market trades: {trades_data['trades']}")
        assert len(trades_data["trades"]) == 1, f"Expected 1 trade, got {len(trades_data['trades'])}"
        print(">> SUCCESS: Trades history API validated.")
        
        # ---------------------------------------------------------------------
        # TEST 7: Order Cancellation via POST /orders/{order_id}/cancel
        # ---------------------------------------------------------------------
        print("\n[TEST 7] Testing Order Cancellation API...")
        # Get remaining order id for User A's open YES buy order (which had 10 quantity, 5 filled, so 5 remaining)
        response = client.get(f"/api/v1/users/{user_a_id}/orders")
        assert response.status_code == 200
        orders_data = response.json()
        print(f"User A Orders: {orders_data['orders']}")
        assert len(orders_data["orders"]) == 1
        rem_order_id = orders_data["orders"][0]["id"]
        assert orders_data["orders"][0]["status"] == "partially_filled"
        
        response = client.post(f"/api/v1/orders/{rem_order_id}/cancel")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        canc_data = response.json()
        print(f"Cancel report: {canc_data}")
        assert canc_data["refunded_amount"] == 3.10, f"Expected refund of 3.10 (5 remaining * $0.62), got {canc_data['refunded_amount']}"
        
        # Re-check balance to confirm release
        response = client.get(f"/api/v1/users/{user_a_id}/balance")
        balance_data = response.json()
        print(f"User A balance after cancel: ${balance_data['balance']:.2f}")
        assert abs(balance_data["balance"] - 996.90) < 0.01, f"Expected 996.90, got {balance_data['balance']}"
        print(">> SUCCESS: Order successfully cancelled and balance released.")
        
        print("\n" + "="*50)
        print("ALL FASTAPI CLOB API INTEGRATION TESTS PASSED SUCCESSFULLY!")
        print("="*50)
        
    finally:
        # Cleanup temporary rows
        print("\nCleaning up temporary test data...")
        cursor.execute("DELETE FROM trades WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM orders WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM user_positions WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM markets WHERE id = ?;", (market_id,))
        cursor.execute("DELETE FROM users WHERE id IN (?, ?);", (user_a_id, user_b_id))
        conn.commit()
        conn.close()
        print("Cleanup complete. Database remains clean.")

if __name__ == "__main__":
    test_clob_api()
