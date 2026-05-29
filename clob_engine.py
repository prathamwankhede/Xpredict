import sqlite3
import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@dataclass
class Order:
    id: str
    market_id: str
    user_id: str
    side: str          # 'buy' or 'sell'
    outcome: str       # 'yes' or 'no'
    order_type: str    # 'limit' or 'market'
    price: float       # 0.01 to 0.99
    quantity: int
    filled_quantity: int = 0
    status: str = 'open'  # 'open', 'filled', 'partially_filled', 'cancelled'
    created_at: Optional[str] = None

    @property
    def price_cents(self) -> int:
        # Convert float price to integer cents (1-99) to prevent floating-point rounding errors during matching
        return int(round(self.price * 100))

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.filled_quantity

@dataclass
class Trade:
    id: str
    market_id: str
    buyer_id: str
    seller_id: str
    outcome: str       # 'yes' or 'no'
    price: float       # execution price
    shares: int
    maker_order_id: str
    taker_order_id: str
    trade_type: str = 'direct'  # 'direct' or 'synthetic_mint'

class OrderBook:
    def __init__(self, market_id: str):
        self.market_id = market_id
        # Bids (Buy orders) and Asks (Sell orders) per price point (1 to 99 cents)
        # Each index contains a FIFO list of open Orders
        self.yes_bids: Dict[int, List[Order]] = {p: [] for p in range(1, 100)}
        self.yes_asks: Dict[int, List[Order]] = {p: [] for p in range(1, 100)}
        self.no_bids: Dict[int, List[Order]] = {p: [] for p in range(1, 100)}
        self.no_asks: Dict[int, List[Order]] = {p: [] for p in range(1, 100)}

    def add_order(self, order: Order):
        price = order.price_cents
        if order.outcome == 'yes':
            if order.side == 'buy':
                self.yes_bids[price].append(order)
            else:
                self.yes_asks[price].append(order)
        else:
            if order.side == 'buy':
                self.no_bids[price].append(order)
            else:
                self.no_asks[price].append(order)

    def load_from_db(self, conn: sqlite3.Connection):
        """Loads open orders from SQLite into the in-memory books."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, market_id, user_id, side, outcome, type, price, quantity, filled_quantity, status, created_at
            FROM orders
            WHERE market_id = ? AND status IN ('open', 'partially_filled');
        """, (self.market_id,))
        
        rows = cursor.fetchall()
        for r in rows:
            order = Order(
                id=r[0],
                market_id=r[1],
                user_id=r[2],
                side=r[3],
                outcome=r[4],
                order_type=r[5],
                price=r[6],
                quantity=r[7],
                filled_quantity=r[8],
                status=r[9],
                created_at=r[10]
            )
            self.add_order(order)
        logging.info(f"Loaded {len(rows)} open orders into memory for market {self.market_id}")

def match_taker_order(book: OrderBook, taker: Order) -> Tuple[List[Trade], List[Order]]:
    """Runs the core CLOB double-auction and contract-minting matching loops."""
    trades: List[Trade] = []
    modified_orders: List[Order] = []

    # 1. DIRECT MATCHING LOOP
    # Match Taker Buy with Maker Sell (or Taker Sell with Maker Buy) on the SAME outcome
    if taker.side == 'buy':
        # Buyer wants lowest asks (sells) from $0.01 up to taker's limit price
        asks = book.yes_asks if taker.outcome == 'yes' else book.no_asks
        for price_cents in range(1, taker.price_cents + 1):
            queue = asks[price_cents]
            while queue and taker.remaining_quantity > 0:
                maker = queue[0]
                match_qty = min(taker.remaining_quantity, maker.remaining_quantity)
                
                # Execute match
                taker.filled_quantity += match_qty
                maker.filled_quantity += match_qty
                maker.status = 'filled' if maker.remaining_quantity == 0 else 'partially_filled'
                
                # Record Trade (buyer is taker, seller is maker)
                trade = Trade(
                    id=str(uuid.uuid4()),
                    market_id=book.market_id,
                    buyer_id=taker.user_id,
                    seller_id=maker.user_id,
                    outcome=taker.outcome,
                    price=maker.price,
                    shares=match_qty,
                    maker_order_id=maker.id,
                    taker_order_id=taker.id,
                    trade_type='direct'
                )
                trades.append(trade)
                if maker not in modified_orders:
                    modified_orders.append(maker)
                
                if maker.status == 'filled':
                    queue.pop(0)
    else:
        # Seller wants highest bids (buys) from $0.99 down to taker's limit price
        bids = book.yes_bids if taker.outcome == 'yes' else book.no_bids
        for price_cents in range(99, taker.price_cents - 1, -1):
            queue = bids[price_cents]
            while queue and taker.remaining_quantity > 0:
                maker = queue[0]
                match_qty = min(taker.remaining_quantity, maker.remaining_quantity)
                
                taker.filled_quantity += match_qty
                maker.filled_quantity += match_qty
                maker.status = 'filled' if maker.remaining_quantity == 0 else 'partially_filled'
                
                # Record Trade (buyer is maker, seller is taker)
                trade = Trade(
                    id=str(uuid.uuid4()),
                    market_id=book.market_id,
                    buyer_id=maker.user_id,
                    seller_id=taker.user_id,
                    outcome=taker.outcome,
                    price=maker.price,
                    shares=match_qty,
                    maker_order_id=maker.id,
                    taker_order_id=taker.id,
                    trade_type='direct'
                )
                trades.append(trade)
                if maker not in modified_orders:
                    modified_orders.append(maker)
                
                if maker.status == 'filled':
                    queue.pop(0)

    # Exit early if taker order is fully filled
    if taker.remaining_quantity == 0:
        taker.status = 'filled'
        return trades, modified_orders

    # 2. SYNTHETIC MATCHING LOOP (Contract Minting)
    # Taker YES Buy + Maker NO Buy >= $1.00 (100 cents). We mint new shares!
    # Only triggered if taker order is a BUY order
    if taker.side == 'buy':
        opposite_outcome = 'no' if taker.outcome == 'yes' else 'yes'
        opposite_bids = book.no_bids if taker.outcome == 'yes' else book.yes_bids
        
        # YES bid + NO bid >= 100 cents. Therefore, opposite bid price must be >= 100 - taker.price_cents
        min_opposite_price = 100 - taker.price_cents
        
        # Scan opposite bids from highest ($0.99) down to the threshold
        for price_cents in range(99, min_opposite_price - 1, -1):
            queue = opposite_bids[price_cents]
            while queue and taker.remaining_quantity > 0:
                maker = queue[0]
                match_qty = min(taker.remaining_quantity, maker.remaining_quantity)
                
                # Execute match
                taker.filled_quantity += match_qty
                maker.filled_quantity += match_qty
                maker.status = 'filled' if maker.remaining_quantity == 0 else 'partially_filled'
                
                # Synthetic Mint: both are BUY orders, one buying YES, one buying NO
                # The execution price is taker's bid price (excess from maker bid is refunded in transaction)
                trade = Trade(
                    id=str(uuid.uuid4()),
                    market_id=book.market_id,
                    buyer_id=taker.user_id if taker.outcome == 'yes' else maker.user_id,
                    seller_id=maker.user_id if taker.outcome == 'yes' else taker.user_id, # technically, no seller, but we map buyers to fields
                    outcome='yes', # we record contract mints under outcome 'yes' (1 YES + 1 NO issued)
                    price=taker.price,
                    shares=match_qty,
                    maker_order_id=maker.id,
                    taker_order_id=taker.id,
                    trade_type='synthetic_mint'
                )
                trades.append(trade)
                if maker not in modified_orders:
                    modified_orders.append(maker)
                
                if maker.status == 'filled':
                    queue.pop(0)

    # 3. Finalize Taker Status
    if taker.remaining_quantity == 0:
        taker.status = 'filled'
    elif taker.filled_quantity > 0:
        taker.status = 'partially_filled'
    else:
        taker.status = 'open'

    # If remaining open quantity exists, rest it on the book
    if taker.status in ('open', 'partially_filled'):
        book.add_order(taker)

    return trades, modified_orders

def process_order(db_path: str, market_id: str, user_id: str, side: str, outcome: str, 
                  order_type: str, price: float, quantity: int) -> Tuple[bool, dict]:
    """
    Executes a limit order atomically inside a SQLite transaction:
    Locks margin balance -> Loads book -> Matches -> Adjusts balances/positions -> Commits.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    order_id = str(uuid.uuid4())
    taker = Order(
        id=order_id,
        market_id=market_id,
        user_id=user_id,
        side=side,
        outcome=outcome,
        order_type=order_type,
        price=price,
        quantity=quantity
    )
    
    try:
        with conn: # Starts an ATOMIC SQLite transaction block
            # 1. Check User Balance & Deduct Margin / Verify Shares for Sell
            cursor.execute("SELECT balance FROM users WHERE id = ?;", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False, {"error": "User does not exist."}
            
            user_balance = user_row[0]
            
            if side == 'buy':
                margin_required = price * quantity
                if user_balance < margin_required:
                    return False, {"error": f"Insufficient balance. Required: ${margin_required:.2f}, Available: ${user_balance:.2f}"}
                
                # Lock the cash margin
                cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?;", (margin_required, user_id))
            else:
                # For SELL orders, verify the user has sufficient shares in user_positions
                cursor.execute("""
                    SELECT shares_yes, shares_no FROM user_positions 
                    WHERE user_id = ? AND market_id = ?;
                """, (user_id, market_id))
                pos_row = cursor.fetchone()
                
                if not pos_row:
                    return False, {"error": f"Insufficient shares. You do not hold any shares in this market."}
                
                shares_held = pos_row[0] if outcome == 'yes' else pos_row[1]
                if shares_held < quantity:
                    return False, {"error": f"Insufficient shares to sell. Required: {quantity}, Held: {shares_held}"}
            
            # 2. Load the In-Memory Book & Match
            book = OrderBook(market_id)
            book.load_from_db(conn)
            
            trades, modified_orders = match_taker_order(book, taker)
            
            # 3. Settle Trades & Adjust Balances/Positions
            for trade in trades:
                buyer_id = trade.buyer_id
                seller_id = trade.seller_id
                shares = trade.shares
                exec_price = trade.price
                
                if trade.trade_type == 'direct':
                    # Taker Buy YES matches Maker Sell YES:
                    # Seller exits position or goes short. In standard matching:
                    # Buyer's margin was already locked. We deduct it permanently.
                    # Seller gets paid the cash directly.
                    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (exec_price * shares, seller_id))
                    
                    # Update Buyer YES position
                    update_position(cursor, buyer_id, market_id, outcome, shares, exec_price)
                    # Update Seller YES position (reduce their YES shares)
                    update_position(cursor, seller_id, market_id, outcome, -shares, exec_price)
                    
                elif trade.trade_type == 'synthetic_mint':
                    # YES Buy + NO Buy matches. We mint brand new contracts!
                    # Taker YES Buy at price P_yes matches Maker NO Buy at price P_no.
                    # P_yes + P_no >= 1.00.
                    # Taker price is exec_price. Maker price is maker.price.
                    # We locate the exact maker order to determine its price and user
                    maker_order = None
                    maker_price = 0.0
                    for mo in modified_orders:
                        if mo.id == trade.maker_order_id:
                            maker_order = mo
                            maker_price = mo.price
                            break
                    
                    # Cash committed by YES buyer: shares * P_yes
                    # Cash committed by NO buyer: shares * P_no
                    excess_price = (exec_price + maker_price) - 1.00
                    if excess_price > 0:
                        # In a CLOB double-auction, the Taker always gets the price improvement (executes at Maker's price)
                        # Therefore, the Taker is refunded the excess cents back to their available balance
                        refund_amount = excess_price * shares
                        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (refund_amount, taker.user_id))
                    
                    # Both buyers get their respective YES/NO shares
                    # Enforce explicit identification of the YES buyer and NO buyer
                    if taker.outcome == 'yes':
                        yes_buyer_id = taker.user_id
                        yes_price = exec_price
                        no_buyer_id = maker_order.user_id
                        no_price = maker_price
                    else:
                        yes_buyer_id = maker_order.user_id
                        yes_price = maker_price
                        no_buyer_id = taker.user_id
                        no_price = exec_price
                    
                    # credit YES shares to the YES buyer
                    update_position(cursor, yes_buyer_id, market_id, 'yes', shares, yes_price)
                    # credit NO shares to the NO buyer
                    update_position(cursor, no_buyer_id, market_id, 'no', shares, no_price)
                
                # Record Trade in DB
                cursor.execute("""
                    INSERT INTO trades (id, market_id, buyer_id, seller_id, outcome, price, shares, maker_order_id, taker_order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (trade.id, market_id, trade.buyer_id, trade.seller_id, outcome if trade.trade_type == 'direct' else 'yes', 
                      exec_price, shares, trade.maker_order_id, trade.taker_order_id))
                
            # 4. Commit Orders back to Database
            # Update all modified maker orders
            for maker in modified_orders:
                cursor.execute("""
                    UPDATE orders 
                    SET filled_quantity = ?, status = ?
                    WHERE id = ?;
                """, (maker.filled_quantity, maker.status, maker.id))
                
                # If a maker order was filled, release its remaining locked margin (which was fully spent)
                if maker.status == 'filled' and maker.side == 'buy':
                    pass # Fully filled, the locked balance is naturally spent
                elif maker.status == 'partially_filled' and maker.side == 'buy':
                    pass # Partially filled, portion is spent, portion remains locked
            
            # Save the Taker Order
            cursor.execute("""
                INSERT INTO orders (id, market_id, user_id, side, outcome, type, price, quantity, filled_quantity, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (taker.id, taker.market_id, taker.user_id, taker.side, taker.outcome, taker.order_type, 
                  taker.price, taker.quantity, taker.filled_quantity, taker.status))
            
            # If the taker order was filled or partially filled, adjust the locked balance appropriately
            if side == 'buy':
                filled_cost = price * taker.filled_quantity
                # The filled portion was spent, so we remove it from the locked margin balance
                # If fully filled, we remove the entire cost. If partially filled, we remove the filled portion.
                # In SQLite, when we placed the order, we subtracted the full cost 'price * quantity' from the user's main balance.
                # Since the filled portion is permanently gone, we leave the remaining open portion (price * remaining_quantity) locked.
                # Therefore, we credit the user's available balance with any refund (if synthetic matching cleared at a cheaper price)
                # but since we executed at taker's exact price for YES/NO mint, there is no taker refund, only maker refunds.
                pass 
                
        logging.info(f"Successfully processed order {order_id} with status {taker.status} generating {len(trades)} trades.")
        return True, {
            "order_id": order_id,
            "status": taker.status,
            "filled_quantity": taker.filled_quantity,
            "trades": [
                {
                    "trade_id": t.id,
                    "price": t.price,
                    "shares": t.shares,
                    "buyer_id": t.buyer_id,
                    "seller_id": t.seller_id,
                    "type": t.trade_type
                } for t in trades
            ]
        }
        
    except Exception as e:
        logging.error(f"Failed to process order: {e}")
        return False, {"error": str(e)}
    finally:
        conn.close()

def update_position(cursor: sqlite3.Cursor, user_id: str, market_id: str, outcome: str, shares: int, price: float):
    """Updates the user share position in user_positions, creating the row if missing."""
    # Check if position row already exists
    cursor.execute("""
        SELECT shares_yes, shares_no, avg_price_yes, avg_price_no 
        FROM user_positions 
        WHERE user_id = ? AND market_id = ?;
    """, (user_id, market_id))
    row = cursor.fetchone()
    
    if not row:
        # Create new position row
        shares_yes = shares if outcome == 'yes' else 0
        shares_no = shares if outcome == 'no' else 0
        avg_price_yes = price if outcome == 'yes' else 0.0
        avg_price_no = price if outcome == 'no' else 0.0
        
        cursor.execute("""
            INSERT INTO user_positions (user_id, market_id, shares_yes, shares_no, avg_price_yes, avg_price_no)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, market_id, shares_yes, shares_no, avg_price_yes, avg_price_no))
    else:
        # Update existing position row
        curr_shares_yes, curr_shares_no, avg_yes, avg_no = row
        
        if outcome == 'yes':
            new_shares_yes = curr_shares_yes + shares
            if new_shares_yes < 0:
                new_shares_yes = 0 # Prevent negative inventory
            
            # Calculate new average entry price (only when buying/adding to position)
            if shares > 0 and (curr_shares_yes + shares) > 0:
                new_avg_yes = ((curr_shares_yes * avg_yes) + (shares * price)) / (curr_shares_yes + shares)
            else:
                new_avg_yes = avg_yes
            
            cursor.execute("""
                UPDATE user_positions 
                SET shares_yes = ?, avg_price_yes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND market_id = ?;
            """, (new_shares_yes, new_avg_yes, user_id, market_id))
        else:
            new_shares_no = curr_shares_no + shares
            if new_shares_no < 0:
                new_shares_no = 0
                
            if shares > 0 and (curr_shares_no + shares) > 0:
                new_avg_no = ((curr_shares_no * avg_no) + (shares * price)) / (curr_shares_no + shares)
            else:
                new_avg_no = avg_no
                
            cursor.execute("""
                UPDATE user_positions 
                SET shares_no = ?, avg_price_no = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND market_id = ?;
            """, (new_shares_no, new_avg_no, user_id, market_id))

def cancel_order(db_path: str, order_id: str) -> Tuple[bool, dict]:
    """Cancels an open order and unlocks its cash margin balance back to available balance."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        with conn:
            cursor.execute("""
                SELECT market_id, user_id, side, price, quantity, filled_quantity, status 
                FROM orders 
                WHERE id = ?;
            """, (order_id,))
            row = cursor.fetchone()
            if not row:
                return False, {"error": "Order not found."}
                
            market_id, user_id, side, price, qty, filled_qty, status = row
            if status not in ('open', 'partially_filled'):
                return False, {"error": f"Cannot cancel order with status: {status}."}
                
            # Calculate remaining quantity and unlock its locked margin
            remaining_qty = qty - filled_qty
            refund_amount = price * remaining_qty
            
            # Update order status in DB
            cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?;", (order_id,))
            
            # Release locked margin back to available cash balance for BUY orders
            if side == 'buy':
                cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (refund_amount, user_id))
                
        logging.info(f"Successfully cancelled order {order_id} and refunded ${refund_amount:.2f} to user {user_id}.")
        return True, {"message": "Order successfully cancelled.", "refunded_amount": refund_amount}
        
    except Exception as e:
        logging.error(f"Cancellation failed: {e}")
        return False, {"error": str(e)}
    finally:
        conn.close()

def get_orderbook(db_path: str, market_id: str) -> dict:
    """Retrieves L2 orderbook bid and ask depth sorted by price."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Load open bids and asks for YES and NO outcomes
        cursor.execute("""
            SELECT outcome, side, price, SUM(quantity - filled_quantity) as volume
            FROM orders
            WHERE market_id = ? AND status IN ('open', 'partially_filled')
            GROUP BY outcome, side, price;
        """, (market_id,))
        
        rows = cursor.fetchall()
        book = {
            "yes": {"bids": [], "asks": []},
            "no": {"bids": [], "asks": []}
        }
        
        for r in rows:
            outcome, side, price, volume = r
            entry = [price, volume]
            if side == 'buy':
                book[outcome]["bids"].append(entry)
            else:
                book[outcome]["asks"].append(entry)
                
        # Sort bids descending (highest to lowest) and asks ascending (lowest to highest)
        for outcome in ("yes", "no"):
            book[outcome]["bids"].sort(key=lambda x: x[0], reverse=True)
            book[outcome]["asks"].sort(key=lambda x: x[0])
            
        return book
    except Exception as e:
        logging.error(f"Failed to fetch orderbook: {e}")
        return {"yes": {"bids": [], "asks": []}, "no": {"bids": [], "asks": []}}
    finally:
        conn.close()
