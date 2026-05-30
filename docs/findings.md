# Architectural Findings: Existing Prototype Analysis

## Core Mechanics
The existing codebase implements a **Time-Weighted Pari-Mutuel (TWPM)** prediction market mechanism. Instead of a continuous order matching engine, it uses a pool-based model where payouts are calculated at resolution.

### Time Weight Decay Function
The weight of a bet decays using a square root function of the remaining time:
$$w = 1 + k \cdot \sqrt{\frac{T_{duration} - T_{elapsed}}{T_{duration}}}$$
- **$k = 2$**: The maximum time multiplier is $3.0$ (when placed at the exact start of the market), decaying to $1.0$ at the estimated resolution time.
- **Goal**: Reward early risk-takers who trade under high uncertainty, and penalize late trades placed when the outcome is nearly certain.

### Financial Matching & Settlement
- **Bet Cost**: A user pays `shares * price` from their balance.
- **Weighted Bet**: $\text{Weighted Bet} = \text{shares} \cdot \text{price} \cdot w$.
- **Pool State**: Keeps cumulative sum of standard pools (`pool_yes`, `pool_no`, `tot_pool`) and weighted pools (`weighted_pool_yes`, `weighted_pool_no`, `weighted_total_pool`).
- **Settlement Formula**: If outcome is YES, a winning YES bet gets:
$$\text{Payout}_i = \left( \frac{\text{Weighted Bet}_i}{\text{Weighted Pool YES}} \right) \cdot \text{Total Pool}$$

---

## Technical Debt & Prototype Limitations

1. **Database Bottlenecks (SQLite & Concurrent Writes):**
   - SQLite uses database-level locking for writes. High-frequency concurrent trades will trigger `database is locked` errors.
   - Connections are opened/closed in every API call (`sqlite3.connect('bsname.db')`), creating substantial TCP/overhead latency.

2. **Matching Engine Limitations:**
   - There is no matching engine. Trades are executed as instant buys into the pool at a static `price` passed in the request. This represents a fixed-rate betting slip rather than dynamic order books.
   - No bid/ask spreads or liquidity provision (like an AMM).

3. **Concurrency & Real-time Feeds:**
   - Written in synchronous Python/FastAPI without async DB execution.
   - No real-time updates (no WebSockets, SSE, or polling framework).

4. **Security & Validation Gaps:**
   - No authentication/authorization: any user can place bets on behalf of any `user_id`.
   - No transaction/deadlock handling. If an update to `markets` fails after deducting user balance, funds are lost (no DB transaction rollbacks).
   - No validation on whether the user has sufficient balance or if the market is closed before placing a bet.

---

## Scaling Goals for Venture-Scale Architecture
To scale to **millions of users** and **thousands of simultaneous markets**, the new system must:
- **Adopt a Hybrid Model:** Provide a Central Limit Order Book (CLOB) and Constant Product Market Maker (AMM) for high-frequency markets, while retaining the Time-Weighted Pari-Mutuel (TWPM) mechanism for long-tail speculative markets.
- **Decouple Ingestion & Settlement:** Run a high-frequency matching engine in memory (Go or Rust) and stream state via Kafka/Redis.
- **Leverage PostgreSQL & Redis:** Distribute reads using replica pools and Redis caching, and guarantee high-concurrency writes with robust queue-backed worker engines.
