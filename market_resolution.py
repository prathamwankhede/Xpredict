import sqlite3
import logging
import datetime

conn = sqlite3.connect("bsname.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)

#manual resolution for now
#TODO add automated resolution based on news and social media sentiment analysis, web scraping etc.
def resolve_market(db: sqlite3.connect, market_id: str, resolution_side: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        UPDATE markets
        SET status = 'resolved', resolution_side = ?, resolved_at = ?
        WHERE id = ?;
    """, (resolution_side, datetime.datetime.now(), market_id))
    logging.info(f"Resolved market {market_id} with resolution {resolution_side}")
    db.commit()

def get_market_resolution(db: sqlite3.connect, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    query = """
        SELECT resolution_side FROM markets
        WHERE id = ?;
    """
    cursor.execute(query, (market_id,))
    result = cursor.fetchone()
    if result:
        return result['resolution_side']
    else:
        return None

def time_weight(db: sqlite3.connect, user_id: str, market_id: str, bet_time: datetime = datetime.datetime.now()) -> float:    
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        SELECT started_at, estimated_resolution_time FROM markets
        WHERE id = ?;
    """, (market_id,))
    result = cursor.fetchone()
    start_time, end_time = result['started_at'], result['estimated_resolution_time']
    start_time = datetime.datetime.fromisoformat(start_time)
    end_time = datetime.datetime.fromisoformat(end_time)
    market_duration = (end_time - start_time).total_seconds()
    elapsed_time = (bet_time - start_time).total_seconds()
    r = (market_duration - elapsed_time)/market_duration
    k = 2
    w = 1 + k*((r)**0.5) #square root weight decay function
    return w

def distribute_winnings(db: sqlite3.connect, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    resolution_decision = get_market_resolution(db, market_id)
    if resolution_decision is None:
        raise ValueError(f"Market {market_id} has not been resolved yet.")
    cursor.execute("""
        SELECT user_id, side, shares, price, weighted_bet FROM bets
        WHERE market_id = ? AND side = ?;
    """, (market_id, resolution_decision))
    bets = cursor.fetchall()
    cursor.execute("""
        SELECT weighted_pool_yes, weighted_pool_no, tot_pool FROM markets
        WHERE id = ?;
    """, (market_id,))
    pool_data = cursor.fetchone()
    pool_yes, pool_no, pool = pool_data['weighted_pool_yes'], pool_data['weighted_pool_no'], pool_data['tot_pool']
    for bet in bets:
        weighted_stake = bet['weighted_bet']
        stake = weighted_stake/pool_yes if resolution_decision == 'yes' else weighted_stake/pool_no
        winnings = stake * pool
        cursor.execute("""
            UPDATE users
            SET balance = balance + ?
            WHERE id = ?;
        """, (winnings, bet['user_id']))
        logging.info(f"Distributed {winnings} to user {bet['user_id']} for market {market_id}")
    db.commit()


def distribute_clob_winnings(db: sqlite3.Connection, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    resolution_decision = get_market_resolution(db, market_id)
    if resolution_decision is None:
        raise ValueError(f"Market {market_id} has not been resolved yet.")

    # 1. Cancel all open/partially filled orders and refund locked margin for buy orders
    cursor.execute("""
        SELECT id, user_id, side, price, quantity, filled_quantity 
        FROM orders
        WHERE market_id = ? AND status IN ('open', 'partially_filled');
    """, (market_id,))
    open_orders = cursor.fetchall()
    
    for order in open_orders:
        order_id = order['id']
        user_id = order['user_id']
        side = order['side']
        price = order['price']
        qty = order['quantity']
        filled_qty = order['filled_quantity']
        
        remaining_qty = qty - filled_qty
        
        # Update order status to cancelled
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?;", (order_id,))
        
        # If it was a buy order, refund the locked margin
        if side == 'buy':
            refund_amount = price * remaining_qty
            cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (refund_amount, user_id))
            logging.info(f"Refunded {refund_amount:.2f} to user {user_id} for cancelled order {order_id}")
            
    # 2. Pay out winnings based on positions ($1.00 per winning share)
    cursor.execute("""
        SELECT user_id, shares_yes, shares_no 
        FROM user_positions
        WHERE market_id = ?;
    """, (market_id,))
    positions = cursor.fetchall()
    
    for pos in positions:
        user_id = pos['user_id']
        shares_yes = pos['shares_yes']
        shares_no = pos['shares_no']
        
        payout = 0.0
        if resolution_decision == 'yes':
            if shares_yes > 0:
                payout = shares_yes * 1.00
        elif resolution_decision == 'no':
            if shares_no > 0:
                payout = shares_no * 1.00
                
        if payout > 0:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (payout, user_id))
            logging.info(f"CLOB Payout: Distributed {payout:.2f} to user {user_id} for holding winning shares in market {market_id}")
            
        # Reset positions to zero
        cursor.execute("""
            UPDATE user_positions
            SET shares_yes = 0, shares_no = 0, avg_price_yes = 0.0, avg_price_no = 0.0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND market_id = ?;
        """, (user_id, market_id))
        
    db.commit()


