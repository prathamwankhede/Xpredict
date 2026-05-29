import sqlite3
import market_resolution
import uuid
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)

conn = sqlite3.connect("bsname.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bets (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL REFERENCES markets(id),
    user_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    shares INTEGER NOT NULL CHECK (shares > 0),
    price REAL NOT NULL CHECK (price >= 0),
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    weighted_bet DECIMAL NOT NULL,
    time_weight DECIMAL NOT NULL
);
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS markets(
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NOT NULL,
    estimated_resolution_time TIMESTAMP NOT NULL,
    c_yes REAL,
    c_no REAL,
    prob_yes REAL,
    prob_no REAL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'cancelled')),
    resolution_side TEXT CHECK (resolution_side IN ('yes', 'no')),
    resolved_at TIMESTAMP,
    tot_pool REAL NOT NULL DEFAULT 0,
    pool_yes REAL NOT NULL DEFAULT 0,
    pool_no REAL NOT NULL DEFAULT 0,
    weighted_total_pool REAL NOT NULL DEFAULT 0,
    weighted_pool_yes REAL NOT NULL DEFAULT 0,
    weighted_pool_no REAL NOT NULL DEFAULT 0
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    balance REAL NOT NULL DEFAULT 500,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

def create_market(db: sqlite3.connect, market_name, started_at, ended_at, c_yes, c_no):
    market_id = str(uuid.uuid4())
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO markets (id, name, started_at, estimated_resolution_time, c_yes, c_no)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (market_id, market_name, started_at, ended_at, c_yes, c_no))
    db.commit()
    logging.info(f"Created market {market_id} with start time {started_at}, end time {ended_at}, c_yes {c_yes} and c_no {c_no}")
    return market_id

def get_market(db: sqlite3.connect, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    query = """
        SELECT * FROM markets
        WHERE id = ?;
    """
    cursor.execute(query, (market_id,))
    return cursor.fetchone()

def placeBet(db: sqlite3.connect, market_id: str, price: float, time, shares: float, yes: bool, user_id: str):
    side = 'yes' if bool(yes) else 'no'
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    insertion = """
        INSERT INTO bets(id, market_id, user_id, side, shares, price, placed_at, weighted_bet, time_weight)
        VALUES (lower(hex(randomblob(16))), ?, ?, ?, ?, ?, ?, ?, ?);
        """
    time_weight = market_resolution.time_weight(db, user_id, market_id, time)
    time_weighted_bet = shares * price * time_weight
    cursor.execute(insertion, (market_id, user_id, side, shares, price, time, time_weighted_bet, time_weight))
    market_pool = shares * price
    if side == 'yes':
        cursor.execute("""
            UPDATE markets
            SET pool_yes = pool_yes + ?, tot_pool = tot_pool + ?, weighted_total_pool = weighted_total_pool + ?, weighted_pool_yes = weighted_pool_yes + ?
            WHERE id = ?;
        """, (market_pool, market_pool, time_weighted_bet, time_weighted_bet, market_id))
    else:
        cursor.execute("""
            UPDATE markets
            SET pool_no = pool_no + ?, tot_pool = tot_pool + ?, weighted_total_pool = weighted_total_pool + ?, weighted_pool_no = weighted_pool_no + ?
            WHERE id = ?;
        """, (market_pool, market_pool, time_weighted_bet, time_weighted_bet, market_id))
    cursor.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE id = ?;
    """, (market_pool, user_id))
    db.commit()
    logging.info(f"User {user_id} executed trade of {shares} shares at price {price} on side {side} for market {market_id} at time {time} with weight {time_weight}")

def getBets(db: sqlite3.connect, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    query = """
        SELECT * FROM bets
        WHERE market_id = ?;
    """
    cursor.execute(query, (market_id,))
    return cursor.fetchall()

def getBet(db: sqlite3.connect, bet_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    query = """
        SELECT * FROM bets
        WHERE id = ?;
    """
    cursor.execute(query, (bet_id,))
    return cursor.fetchone()

def getBetsByUser(db: sqlite3.connect, user_id: str, market_id: str):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    query = """
        SELECT * FROM bets
        WHERE user_id = ? AND market_id = ?;
    """
    cursor.execute(query, (user_id, market_id))
    return cursor.fetchall()
