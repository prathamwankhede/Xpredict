import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def setup_clob_database(db_path="bsname.db"):
    if not os.path.exists(db_path):
        logging.error(f"Database file not found at {db_path}. Please run from the directory containing bsname.db.")
        return False
    
    logging.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enforce foreign key constraints in SQLite
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Update existing markets table with engine_type column (if not already present)
        logging.info("Checking for 'engine_type' in markets table...")
        cursor.execute("PRAGMA table_info(markets);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "engine_type" not in columns:
            logging.info("Adding 'engine_type' column to markets table...")
            cursor.execute("""
                ALTER TABLE markets 
                ADD COLUMN engine_type TEXT DEFAULT 'twpm' 
                CHECK (engine_type IN ('clob', 'amm', 'twpm'));
            """)
            logging.info("Successfully added 'engine_type' column to markets.")
        else:
            logging.info("'engine_type' column already exists in markets table.")
            
        # 2. Create the CLOB orders table
        logging.info("Creating 'orders' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                market_id TEXT NOT NULL REFERENCES markets(id) ON DELETE RESTRICT,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                outcome TEXT NOT NULL CHECK (outcome IN ('yes', 'no')),
                type TEXT NOT NULL CHECK (type IN ('limit', 'market')),
                price REAL NOT NULL CHECK (price >= 0.01 AND price <= 0.99), -- represented as decimal cents
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                filled_quantity INTEGER NOT NULL DEFAULT 0 CHECK (filled_quantity <= quantity),
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'filled', 'partially_filled', 'cancelled', 'expired')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.info("'orders' table checked/created successfully.")
        
        # 3. Create high-efficiency index for orders (Price-Time Priority)
        logging.info("Creating index for fast matching queries...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_matching 
            ON orders(market_id, outcome, side, price, created_at) 
            WHERE status IN ('open', 'partially_filled');
        """)
        
        # 4. Create the CLOB trades execution table
        logging.info("Creating 'trades' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                market_id TEXT NOT NULL REFERENCES markets(id) ON DELETE RESTRICT,
                buyer_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                seller_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                outcome TEXT NOT NULL CHECK (outcome IN ('yes', 'no')),
                price REAL NOT NULL,
                shares INTEGER NOT NULL CHECK (shares > 0),
                maker_order_id TEXT NOT NULL,
                taker_order_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.info("'trades' table checked/created successfully.")
        
        # 5. Create index for trade history lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id, created_at);")
        
        # 6. Create the user_positions table (Tracks share holdings for YES/NO outcomes)
        logging.info("Creating 'user_positions' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_positions (
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                market_id TEXT NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
                shares_yes INTEGER NOT NULL DEFAULT 0 CHECK (shares_yes >= 0),
                shares_no INTEGER NOT NULL DEFAULT 0 CHECK (shares_no >= 0),
                avg_price_yes REAL DEFAULT 0.0,
                avg_price_no REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, market_id)
            );
        """)
        logging.info("'user_positions' table checked/created successfully.")
        
        conn.commit()
        logging.info("Database migration and CLOB table setup completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    setup_clob_database()
