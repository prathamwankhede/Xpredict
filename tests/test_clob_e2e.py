import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import uuid
import datetime
import logging
import threading
import random
import time
from typing import List

import clob_engine
import market_resolution

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def run_clob_e2e_tests(db_path="bsname.db"):
    conn = sqlite3.connect(db_path)
    # Enable WAL mode for concurrency handling
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    
    # 1. Setup Temporary Users & Market
    market_id = str(uuid.uuid4())
    users = {
        "User_A": {"id": str(uuid.uuid4()), "initial_balance": 10000.0},
        "User_B": {"id": str(uuid.uuid4()), "initial_balance": 10000.0},
        "User_C": {"id": str(uuid.uuid4()), "initial_balance": 10000.0},
        "User_D": {"id": str(uuid.uuid4()), "initial_balance": 10000.0},
    }
    
    print("\n" + "="*60)
    print("STARTING E2E CLOB INTEGRATION & HIGH-FREQUENCY TESTING")
    print("="*60)
    
    try:
        # Create temp users
        for username, details in users.items():
            cursor.execute(
                "INSERT INTO users (id, username, balance) VALUES (?, ?, ?);",
                (details["id"], username, details["initial_balance"])
            )
        
        # Create a temp CLOB market
        cursor.execute("""
            INSERT INTO markets (id, name, started_at, ended_at, estimated_resolution_time, engine_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (market_id, "E2E CLOB High Frequency Integration Test Market", 
              str(datetime.datetime.now()), str(datetime.datetime.now() + datetime.timedelta(days=1)),
              str(datetime.datetime.now() + datetime.timedelta(days=1)), 'clob', 'open'))
        
        conn.commit()
        
        print(f"Created temporary CLOB market: {market_id}")
        for username, details in users.items():
            print(f"Created {username}: {details['id']} with ${details['initial_balance']:.2f}")
        print("-" * 60)
        
        # 2. High Frequency Bets/Orders Placement (Concurrently)
        print("\n[STEP 1] Placing High-Frequency Orders Concurrently...")
        
        # We will spin up multiple threads representing the traders placing orders
        lock = threading.Lock()
        order_reports = []
        errors = []
        
        def trader_worker(user_name: str, user_id: str, orders_to_place: List[dict]):
            for order_spec in orders_to_place:
                # Add random slight delay to simulate high-frequency spread out in time
                time.sleep(random.uniform(0.001, 0.01))
                
                # Try placing order with retries in case of database locks (SQLite write locks)
                max_retries = 10
                success = False
                report = {}
                for attempt in range(max_retries):
                    try:
                        success, report = clob_engine.process_order(
                            db_path=db_path,
                            market_id=market_id,
                            user_id=user_id,
                            side=order_spec["side"],
                            outcome=order_spec["outcome"],
                            order_type="limit",
                            price=order_spec["price"],
                            quantity=order_spec["quantity"]
                        )
                        if success:
                            break
                    except sqlite3.OperationalError as e:
                        if "locked" in str(e):
                            time.sleep(random.uniform(0.005, 0.02))
                            continue
                        raise e
                
                with lock:
                    if success:
                        order_reports.append(report)
                    else:
                        errors.append((user_name, order_spec, report))

        # Generate a batch of test orders designed to cause direct matches and synthetic mints
        # User A & User B trade YES
        # User C & User D trade NO
        # Also cross-orders that result in synthetic minting (YES Buy + NO Buy >= $1.00)
        orders_a = [
            {"side": "buy", "outcome": "yes", "price": 0.55, "quantity": 10},
            {"side": "buy", "outcome": "yes", "price": 0.58, "quantity": 15},
            {"side": "buy", "outcome": "yes", "price": 0.50, "quantity": 20},
            {"side": "buy", "outcome": "yes", "price": 0.62, "quantity": 10}, # Taker YES Buy
        ]
        
        orders_b = [
            # Pre-seed B with YES position to sell
            {"side": "buy", "outcome": "yes", "price": 0.40, "quantity": 30},
            {"side": "buy", "outcome": "yes", "price": 0.52, "quantity": 10},
        ]
        
        orders_c = [
            {"side": "buy", "outcome": "no", "price": 0.45, "quantity": 15},
            {"side": "buy", "outcome": "no", "price": 0.48, "quantity": 25},
            {"side": "buy", "outcome": "no", "price": 0.38, "quantity": 10},
        ]
        
        orders_d = [
            {"side": "buy", "outcome": "no", "price": 0.42, "quantity": 20},
            {"side": "buy", "outcome": "no", "price": 0.44, "quantity": 10},
        ]
        
        # We start the threads
        threads = []
        threads.append(threading.Thread(target=trader_worker, args=("User_A", users["User_A"]["id"], orders_a)))
        threads.append(threading.Thread(target=trader_worker, args=("User_B", users["User_B"]["id"], orders_b)))
        threads.append(threading.Thread(target=trader_worker, args=("User_C", users["User_C"]["id"], orders_c)))
        threads.append(threading.Thread(target=trader_worker, args=("User_D", users["User_D"]["id"], orders_d)))
        
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()
            
        # Post-seed some sell orders now that they have positions
        # Let's perform a fast sequence of sells to ensure direct match sells are covered
        print("Placing secondary exit/sell orders...")
        exit_orders = [
            (users["User_A"]["id"], "sell", "yes", 0.54, 5),
            (users["User_B"]["id"], "sell", "yes", 0.50, 10),
            (users["User_C"]["id"], "sell", "no", 0.44, 5),
            (users["User_D"]["id"], "sell", "no", 0.40, 5),
        ]
        
        for uid, side, outcome, price, qty in exit_orders:
            success, report = clob_engine.process_order(
                db_path=db_path,
                market_id=market_id,
                user_id=uid,
                side=side,
                outcome=outcome,
                order_type="limit",
                price=price,
                quantity=qty
            )
            if success:
                order_reports.append(report)
            else:
                print(f"Exit order warning: {report}")
                
        print(f"Concurrent execution finished. Placed {len(order_reports)} orders successfully. Errors: {len(errors)}")
        if errors:
            print("Errors encountered during concurrent order placement:")
            for err in errors:
                print(err)
                
        # 3. Retrieve and View Orderbook / Position State before resolution
        print("\n[STEP 2] Orderbook State before resolution:")
        book = clob_engine.get_orderbook(db_path, market_id)
        print(f"YES Bids: {book['yes']['bids']}")
        print(f"YES Asks: {book['yes']['asks']}")
        print(f"NO Bids: {book['no']['bids']}")
        print(f"NO Asks: {book['no']['asks']}")
        
        print("\n[STEP 3] User Positions and Balances before resolution:")
        pre_resolution_balances = {}
        pre_resolution_positions = {}
        for username, details in users.items():
            cursor.execute("SELECT balance FROM users WHERE id = ?;", (details["id"],))
            balance = cursor.fetchone()[0]
            pre_resolution_balances[details["id"]] = balance
            
            cursor.execute("""
                SELECT shares_yes, shares_no, avg_price_yes, avg_price_no 
                FROM user_positions 
                WHERE user_id = ? AND market_id = ?;
            """, (details["id"], market_id))
            pos_row = cursor.fetchone()
            if pos_row:
                pre_resolution_positions[details["id"]] = {
                    "yes": pos_row[0],
                    "no": pos_row[1],
                    "avg_yes": pos_row[2],
                    "avg_no": pos_row[3],
                }
            else:
                pre_resolution_positions[details["id"]] = {"yes": 0, "no": 0, "avg_yes": 0.0, "avg_no": 0.0}
                
            print(f"{username} Balance: ${balance:.2f} | YES shares: {pre_resolution_positions[details['id']]['yes']} | NO shares: {pre_resolution_positions[details['id']]['no']}")
            
        # 4. Resolve the Market (Manually for now)
        print("\n[STEP 4] Resolving Market to 'YES'...")
        market_resolution.resolve_market(conn, market_id, 'yes')
        
        cursor.execute("SELECT status, resolution_side FROM markets WHERE id = ?;", (market_id,))
        m_status, m_res = cursor.fetchone()
        print(f"Market Status in DB: {m_status} | Resolution: {m_res}")
        assert m_status == 'resolved', f"Expected market status to be 'resolved', got {m_status}"
        assert m_res == 'yes', f"Expected market resolution to be 'yes', got {m_res}"
        
        # 5. Distribute Winnings (Payout)
        print("\n[STEP 5] Executing CLOB Payout and Winnings Distribution...")
        market_resolution.distribute_clob_winnings(conn, market_id)
        
        # 6. Verify Post-Resolution State and Mathematical Invariants
        print("\n[STEP 6] Verifying Post-Payout Invariants...")
        
        total_starting_balance = sum(u["initial_balance"] for u in users.values())
        total_final_balance = 0.0
        
        print("\nFinal User states after Payout:")
        for username, details in users.items():
            cursor.execute("SELECT balance FROM users WHERE id = ?;", (details["id"],))
            final_balance = cursor.fetchone()[0]
            total_final_balance += final_balance
            
            cursor.execute("""
                SELECT shares_yes, shares_no 
                FROM user_positions 
                WHERE user_id = ? AND market_id = ?;
            """, (details["id"], market_id))
            pos_row = cursor.fetchone()
            
            # Post-resolution positions must be reset to 0
            final_yes = pos_row[0] if pos_row else 0
            final_no = pos_row[1] if pos_row else 0
            
            print(f"{username} Final Balance: ${final_balance:.2f} (diff: ${final_balance - details['initial_balance']:.2f})")
            assert final_yes == 0, f"Expected final YES shares for {username} to be 0, got {final_yes}"
            assert final_no == 0, f"Expected final NO shares for {username} to be 0, got {final_no}"
            
            # Check individual payout math:
            # User should receive $1.00 for every YES share held pre-resolution
            pre_shares_yes = pre_resolution_positions[details["id"]]["yes"]
            # Any remaining open buy order locked margin should have been refunded.
            # Calculate remaining open order value for this user
            cursor.execute("""
                SELECT SUM(price * (quantity - filled_quantity)) 
                FROM orders 
                WHERE user_id = ? AND market_id = ? AND side = 'buy' AND status = 'cancelled';
            """, (details["id"], market_id))
            refunded_order_sum = cursor.fetchone()[0] or 0.0
            
            # Expected final balance is: balance_before_resolution + (pre_shares_yes * 1.00) + refunded_order_sum (since refund is in payout)
            # Wait, our distribute_clob_winnings function refunds directly to balance and credits payouts.
            expected_balance = pre_resolution_balances[details["id"]] + (pre_shares_yes * 1.00) + refunded_order_sum
            assert abs(final_balance - expected_balance) < 0.01, f"Expected balance for {username} to be {expected_balance:.2f}, got {final_balance:.2f}"
            
        print(f"\nTotal System Initial Cash: ${total_starting_balance:.2f}")
        print(f"Total System Final Cash: ${total_final_balance:.2f}")
        
        # Enforce exact cash conservation invariant
        assert abs(total_final_balance - total_starting_balance) < 0.01, \
            f"CASH CONSERVATION FAILED: Total starting balance is {total_starting_balance}, but final balance is {total_final_balance}"
            
        print(">> SUCCESS: Cash conservation invariant verified! System is mathematically sound.")
        
        # Verify that all open orders on this market are now cancelled
        cursor.execute("SELECT COUNT(*) FROM orders WHERE market_id = ? AND status IN ('open', 'partially_filled');", (market_id,))
        open_orders_count = cursor.fetchone()[0]
        assert open_orders_count == 0, f"Expected 0 open orders remaining, got {open_orders_count}"
        print(">> SUCCESS: All remaining open/partially filled orders successfully cancelled.")
        
        print("\n" + "="*60)
        print("ALL E2E CLOB INTEGRATION & HIGH-FREQUENCY TESTS PASSED!")
        print("="*60)
        
    finally:
        # Cleanup temporary test data to keep the database pristine
        print("\nCleaning up temporary test data from database...")
        cursor.execute("DELETE FROM trades WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM orders WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM user_positions WHERE market_id = ?;", (market_id,))
        cursor.execute("DELETE FROM markets WHERE id = ?;", (market_id,))
        cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?, ?);", 
                       (users["User_A"]["id"], users["User_B"]["id"], users["User_C"]["id"], users["User_D"]["id"]))
        conn.commit()
        conn.close()
        print("Cleanup complete. Test database remains clean.")

if __name__ == "__main__":
    run_clob_e2e_tests()
