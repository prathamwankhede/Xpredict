import sqlite3
import uuid
import datetime
import logging
import clob_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def run_clob_tests(db_path="bsname.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Setup Temporary Users & Market
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    market_id = str(uuid.uuid4())
    
    print("\n" + "="*50)
    print("STARTING CENTRAL LIMIT ORDER BOOK (CLOB) INTEGRATION TESTS")
    print("="*50)
    
    try:
        # Create temp users with $1000 balance each
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (?, ?, ?);", (user_a_id, "User_A_YES_Trader", 1000.0))
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (?, ?, ?);", (user_b_id, "User_B_NO_Trader", 1000.0))
        
        # Create a temp CLOB market
        cursor.execute("""
            INSERT INTO markets (id, name, started_at, ended_at, estimated_resolution_time, engine_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (market_id, "Will CLOB Engine Pass Integration Tests?", 
              str(datetime.datetime.now()), str(datetime.datetime.now() + datetime.timedelta(days=1)),
              str(datetime.datetime.now() + datetime.timedelta(days=1)), 'clob', 'open'))
        
        conn.commit()
        print(f"Initialized temporary test market {market_id}")
        print(f"Created User A: {user_a_id} ($1000.00)")
        print(f"Created User B: {user_b_id} ($1000.00)")
        print("-" * 50)
        
        # ---------------------------------------------------------------------
        # TEST 1: Placement and Margin Locking
        # ---------------------------------------------------------------------
        print("\n[TEST 1] Testing Margin Balance Locking...")
        # User A wants to buy 100 YES shares at $0.58. Cost = $58.00.
        success, report = clob_engine.process_order(
            db_path=db_path,
            market_id=market_id,
            user_id=user_a_id,
            side="buy",
            outcome="yes",
            order_type="limit",
            price=0.58,
            quantity=100
        )
        assert success, f"Order placement failed: {report}"
        assert report["status"] == "open", f"Expected 'open', got {report['status']}"
        
        # Verify that User A's available balance is deducted by $58.00
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_a_id,))
        balance_a = cursor.fetchone()[0]
        print(f"User A balance after placing $0.58 YES buy order: ${balance_a:.2f}")
        assert abs(balance_a - 942.00) < 0.01, f"Expected User A balance to be 942.00, got {balance_a}"
        print(">> SUCCESS: Margin balance successfully deducted and locked.")
        
        # ---------------------------------------------------------------------
        # TEST 2: Direct Matching (YES Buy meets YES Sell)
        # ---------------------------------------------------------------------
        print("\n[TEST 2] Testing Direct Order Matching (YES Buy meets YES Sell)...")
        
        # Pre-seed User B holding 50 YES shares (acquired previously) to represent a position exit
        cursor.execute("""
            INSERT INTO user_positions (user_id, market_id, shares_yes, shares_no, avg_price_yes, avg_price_no)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_b_id, market_id, 50, 0, 0.50, 0.0))
        conn.commit()
        
        # User B places a SELL order on YES for 50 shares at $0.55.
        # This should DIRECT match User A's YES BUY resting order at $0.58.
        # Match execution price should be Maker's price ($0.58) per standard CLOB mechanics.
        # Value = 50 * $0.58 = $29.00.
        success, report = clob_engine.process_order(
            db_path=db_path,
            market_id=market_id,
            user_id=user_b_id,
            side="sell",
            outcome="yes",
            order_type="limit",
            price=0.55,
            quantity=50
        )
        assert success, f"Direct sell failed: {report}"
        assert report["status"] == "filled", f"Expected 'filled', got {report['status']}"
        assert len(report["trades"]) == 1, f"Expected 1 trade execution, got {len(report['trades'])}"
        
        trade = report["trades"][0]
        print(f"Trade Executed: {trade['shares']} shares at ${trade['price']:.2f} (Type: {trade['type']})")
        assert trade["price"] == 0.58, f"Expected execution at Maker's price (0.58), got {trade['price']}"
        assert trade["shares"] == 50, f"Expected 50 shares, got {trade['shares']}"
        
        # Verify positions
        # User A bought 50 YES. User B sold 50 YES (representing short -50 or reducing holdings).
        cursor.execute("SELECT shares_yes FROM user_positions WHERE user_id = ? AND market_id = ?;", (user_a_id, market_id))
        pos_a = cursor.fetchone()[0]
        cursor.execute("SELECT shares_yes FROM user_positions WHERE user_id = ? AND market_id = ?;", (user_b_id, market_id))
        pos_b = cursor.fetchone()[0]
        print(f"User A YES shares: {pos_a}")
        print(f"User B YES shares: {pos_b}")
        assert pos_a == 50, f"Expected User A to hold 50 YES, got {pos_a}"
        assert pos_b == 0, f"Expected User B to hold 0 YES (since -50 is set to 0 to prevent negative inventory), got {pos_b}"
        
        # Verify B's balance increased by $29.00
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_b_id,))
        balance_b = cursor.fetchone()[0]
        print(f"User B balance after trade credit: ${balance_b:.2f}")
        assert abs(balance_b - 1029.00) < 0.01, f"Expected User B balance to be 1029.00, got {balance_b}"
        print(">> SUCCESS: Direct matching and position credits verified.")
        
        # ---------------------------------------------------------------------
        # TEST 3: Synthetic Matching & Contract Minting (YES Buy + NO Buy >= $1.00)
        # ---------------------------------------------------------------------
        print("\n[TEST 3] Testing Synthetic Matching (Contract Minting: YES Buy + NO Buy >= $1.00)...")
        # Currently User A has a YES BUY order remaining on the book for 50 shares at $0.58.
        # User B places a NO BUY limit order for 50 shares at $0.43.
        # YES Bid ($0.58) + NO Bid ($0.43) = $1.01 >= $1.00.
        # This must trigger Synthetic match (Contract Minting) of 50 shares!
        # Total cost is exactly $1.00 per paired share.
        # User A pays $0.58/share. User B pays $0.42/share (refunding B $0.01 per share since B bid $0.43).
        # Both buyers get 50 shares of their respective YES/NO assets.
        success, report = clob_engine.process_order(
            db_path=db_path,
            market_id=market_id,
            user_id=user_b_id,
            side="buy",
            outcome="no",
            order_type="limit",
            price=0.43,
            quantity=50
        )
        assert success, f"Synthetic matching order failed: {report}"
        assert report["status"] == "filled", f"Expected 'filled', got {report['status']}"
        assert len(report["trades"]) == 1, f"Expected 1 synthetic trade, got {len(report['trades'])}"
        
        trade = report["trades"][0]
        print(f"Synthetic Trade Executed: {trade['shares']} shares (Type: {trade['type']})")
        assert trade["type"] == "synthetic_mint", f"Expected 'synthetic_mint', got {trade['type']}"
        
        # Verify positions: Both should hold 50 shares
        cursor.execute("SELECT shares_yes FROM user_positions WHERE user_id = ? AND market_id = ?;", (user_a_id, market_id))
        pos_a_yes = cursor.fetchone()[0]
        cursor.execute("SELECT shares_no FROM user_positions WHERE user_id = ? AND market_id = ?;", (user_b_id, market_id))
        pos_b_no = cursor.fetchone()[0]
        print(f"User A YES shares after contract mint: {pos_a_yes}")
        print(f"User B NO shares after contract mint: {pos_b_no}")
        assert pos_a_yes == 100, f"Expected User A YES shares to be 100 (50 direct + 50 minted), got {pos_a_yes}"
        assert pos_b_no == 50, f"Expected User B NO shares to be 50, got {pos_b_no}"
        
        # Verify B's balance:
        # B bid $0.43 * 50 = $21.50 which was initially fully deducted.
        # Synthetic match executed at YES Taker price ($0.58) + Maker NO price ($0.43) = $1.01.
        # B gets refunded $0.01 per share ($0.50 refund total).
        # Balance should be: $1029.00 (before bet) - $21.50 (NO bid cost) + $0.50 (excess refund) = $1008.00.
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_b_id,))
        balance_b = cursor.fetchone()[0]
        print(f"User B final balance (with synthetic excess refund): ${balance_b:.2f}")
        assert abs(balance_b - 1008.00) < 0.01, f"Expected User B balance to be 1008.00, got {balance_b}"
        print(">> SUCCESS: Synthetic contract minting and excess refunds verified.")
        
        # ---------------------------------------------------------------------
        # TEST 4: Order Cancellation & Balance Release
        # ---------------------------------------------------------------------
        print("\n[TEST 4] Testing Order Cancellation and Locked Margin Release...")
        # User A places a new limit BUY order for 100 YES shares at $0.60.
        # Cost = $60.00. Balance should go from $942.00 to $882.00.
        success, report = clob_engine.process_order(
            db_path=db_path,
            market_id=market_id,
            user_id=user_a_id,
            side="buy",
            outcome="yes",
            order_type="limit",
            price=0.60,
            quantity=100
        )
        assert success
        order_id = report["order_id"]
        
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_a_id,))
        balance_a_pre = cursor.fetchone()[0]
        print(f"User A balance with open bid: ${balance_a_pre:.2f}")
        assert abs(balance_a_pre - 882.00) < 0.01, f"Expected 882.00, got {balance_a_pre}"
        
        # Cancel the order
        canc_success, canc_report = clob_engine.cancel_order(db_path=db_path, order_id=order_id)
        assert canc_success, f"Cancellation failed: {canc_report}"
        
        cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_a_id,))
        balance_a_post = cursor.fetchone()[0]
        print(f"User A balance after canceling: ${balance_a_post:.2f}")
        assert abs(balance_a_post - 942.00) < 0.01, f"Expected balance to return to 942.00, got {balance_a_post}"
        print(">> SUCCESS: Order cancellation and full margin release verified.")
        
        # ---------------------------------------------------------------------
        # TEST 5: Orderbook Depth Retrieval
        # ---------------------------------------------------------------------
        print("\n[TEST 5] Testing Orderbook Depth API L2 Feed...")
        # Place a resting YES BUY order (User A, 10 YES at $0.50)
        clob_engine.process_order(db_path, market_id, user_a_id, "buy", "yes", "limit", 0.50, 10)
        
        # Pre-seed User B holding 20 YES shares so they can place a limit sell
        cursor.execute("""
            INSERT OR REPLACE INTO user_positions (user_id, market_id, shares_yes, shares_no, avg_price_yes, avg_price_no)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_b_id, market_id, 20, 0, 0.50, 0.0))
        conn.commit()
        
        # Place a resting YES SELL order (User B, 20 YES at $0.62)
        clob_engine.process_order(db_path, market_id, user_b_id, "sell", "yes", "limit", 0.62, 20)
        
        book = clob_engine.get_orderbook(db_path, market_id)
        print("Orderbook depth JSON output:")
        print(book)
        assert len(book["yes"]["bids"]) > 0, "Bids queue should not be empty."
        assert len(book["yes"]["asks"]) > 0, "Asks queue should not be empty."
        assert book["yes"]["bids"][0] == [0.50, 10], f"Expected best bid [0.50, 10], got {book['yes']['bids'][0]}"
        assert book["yes"]["asks"][0] == [0.62, 20], f"Expected best ask [0.62, 20], got {book['yes']['asks'][0]}"
        print(">> SUCCESS: Orderbook L2 feed correctly aggregated and sorted.")

        print("\n" + "="*50)
        print("ALL CLOB MATCHING ENGINE TESTS PASSED SUCCESSFULLY!")
        print("="*50)
        
    finally:
        # Cleanup temporary rows so your main prototype data remains untouched
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
    run_clob_tests()
