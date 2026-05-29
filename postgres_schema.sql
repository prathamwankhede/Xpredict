-- ============================================================================
-- VENTURE-SCALE PREDICTION MARKET PLATFORM: PRODUCTION POSTGRESQL SCHEMA
-- Upgrades prototype SQLite tables & integrates CLOB matching engine structures
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Core Users Table (Profile metadata only to avoid write locks on balance adjustments)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    reputation_score INT NOT NULL DEFAULT 100,
    kyc_status VARCHAR(20) NOT NULL DEFAULT 'unverified' CHECK (kyc_status IN ('unverified', 'pending', 'verified', 'flagged')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. User Balances Table (Separated for isolation and row locking performance)
CREATE TABLE IF NOT EXISTS user_balances (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE RESTRICT,
    available_balance NUMERIC(20, 6) NOT NULL DEFAULT 500.000000 CHECK (available_balance >= 0),
    locked_balance NUMERIC(20, 6) NOT NULL DEFAULT 0.000000 CHECK (locked_balance >= 0), -- Margin locks for open limit orders
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Double-Entry Financial Ledger (Ensures absolute mathematical auditability)
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    amount NUMERIC(20, 6) NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('deposit', 'withdrawal', 'trade_debit', 'trade_credit', 'payout', 'fee')),
    reference_id UUID, -- References order_id, trade_id, or payout_id
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger_transactions(user_id, created_at DESC);

-- 4. Unified Markets Table (Supports CLOB, AMM, and existing TWPM mechanisms)
CREATE TABLE IF NOT EXISTS markets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    engine_type VARCHAR(10) NOT NULL DEFAULT 'twpm' CHECK (engine_type IN ('clob', 'amm', 'twpm')),
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('draft', 'open', 'paused', 'resolved', 'cancelled')),
    
    -- Schedule
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estimated_resolution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Oracle Resolution
    resolution_source VARCHAR(255) NOT NULL,
    resolution_side VARCHAR(10) CHECK (resolution_side IN ('yes', 'no') OR resolution_side IS NULL),
    
    -- TWPM Engine Pools (Upgraded to NUMERIC to prevent rounding anomalies)
    pool_yes NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    pool_no NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    tot_pool NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    weighted_pool_yes NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    weighted_pool_no NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    weighted_total_pool NUMERIC(20, 6) NOT NULL DEFAULT 0.000000,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_markets_status_engine ON markets(status, engine_type);
CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);

-- 5. Central Limit Order Book: Orders Table (CLOB Engine only)
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    side VARCHAR(5) NOT NULL CHECK (side IN ('buy', 'sell')),
    outcome VARCHAR(5) NOT NULL CHECK (outcome IN ('yes', 'no')),
    type VARCHAR(10) NOT NULL CHECK (type IN ('limit', 'market')),
    price NUMERIC(4, 2) NOT NULL CHECK (price >= 0.01 AND price <= 0.99), -- Represented in cents: $0.01 to $0.99
    quantity NUMERIC(16, 4) NOT NULL CHECK (quantity > 0),
    filled_quantity NUMERIC(16, 4) NOT NULL DEFAULT 0.0000 CHECK (filled_quantity <= quantity),
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'filled', 'partially_filled', 'cancelled', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Composite index for rapid matching book order retrieval (Price-Time Priority)
CREATE INDEX IF NOT EXISTS idx_orders_matching ON orders(market_id, outcome, side, price DESC, created_at ASC) 
WHERE status = 'open' OR status = 'partially_filled';
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);

-- 6. Trades / Executions Table (Closes loop on matched buyer & seller)
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id UUID NOT NULL REFERENCES markets(id),
    buyer_id UUID NOT NULL REFERENCES users(id),
    seller_id UUID NOT NULL REFERENCES users(id),
    outcome VARCHAR(5) NOT NULL CHECK (outcome IN ('yes', 'no')),
    price NUMERIC(4, 2) NOT NULL,
    shares NUMERIC(16, 4) NOT NULL,
    maker_order_id UUID NOT NULL,
    taker_order_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id, created_at DESC);

-- 7. Time-Weighted Bets Table (For TWPM Engine markets)
CREATE TABLE IF NOT EXISTS twpm_bets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    side VARCHAR(5) NOT NULL CHECK (side IN ('yes', 'no')),
    shares NUMERIC(16, 4) NOT NULL CHECK (shares > 0),
    price NUMERIC(4, 2) NOT NULL CHECK (price >= 0.01 AND price <= 0.99),
    time_weight NUMERIC(8, 4) NOT NULL,
    weighted_bet NUMERIC(20, 6) NOT NULL,
    placed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_twpm_bets_market_side ON twpm_bets(market_id, side);
CREATE INDEX IF NOT EXISTS idx_twpm_bets_user ON twpm_bets(user_id);

-- 8. User Positions Table (Materialized holding view aggregated per market)
CREATE TABLE IF NOT EXISTS user_positions (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    shares_yes NUMERIC(16, 4) NOT NULL DEFAULT 0.0000 CHECK (shares_yes >= 0),
    shares_no NUMERIC(16, 4) NOT NULL DEFAULT 0.0000 CHECK (shares_no >= 0),
    avg_price_yes NUMERIC(4, 2) DEFAULT 0.00,
    avg_price_no NUMERIC(4, 2) DEFAULT 0.00,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, market_id)
);

-- 9. Watchlists Table
CREATE TABLE IF NOT EXISTS user_watchlists (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, market_id)
);
