# Xpredict: A Hybrid Venture-Scale Prediction Market Platform

Xpredict is a next-generation, high-performance prediction market platform. It is engineered with a hybrid dual-engine model to address liquidity constraints and insupportable spread dynamics across mainstream and niche markets:

1. **Central Limit Order Book (CLOB)**: A high-throughput double-auction engine utilizing 99-price-bucket static array optimizations for $O(1)$ updates and matching. Features direct order-to-order matching and synthetic contract minting/burning to share liquidity.
2. **Time-Weighted Pari-Mutuel (TWPM)**: A zero-capital cold-start pool engine applying square-root time decay weighting to incentivize early price discovery and offset late-stage information asymmetry.

---

## Project Directory Structure

* **Core Backend Modules**:
  * [api.py](./api.py) - FastAPI service exposing versioned API routes for user balances, open positions, trade histories, TWPM bet placings, and CLOB orderbook matching.
  * [clob_engine.py](./clob_engine.py) - Matches limit/market orders, manages L2 bid/ask depth calculations, processes synthetic mint matches, and operates user position books.
  * [bet_placing.py](./bet_placing.py) - Manages user accounts, SQLite connection initializers, and TWPM pool stakes.
  * [market_resolution.py](./market_resolution.py) - Handles manual oracle resolutions, calculates time weights, and distributes cash winnings/locked margins.
  * [setup_clob_tables.py](./setup_clob_tables.py) - Runs schema migrations for order books, trades, and position tracking in SQLite.
  * [postgres_schema.sql](./postgres_schema.sql) - Production-grade PostgreSQL table designs featuring trade partitioning and composite indices.

* **Client Application**:
  * [frontend/](./frontend) - A Svelte + Vite client implementing a premium dark glassmorphic design system. Features include:
    * Hero spotlight slides showing featured active markets.
    * Bento-grid style market catalog filters (Politics, Tech, Macro, Crypto).
    * Split trading panel view (candlestick chart space, L2 orderbook delta bars, and trading terminal).
    * Focus-trapped search overlays with shortcut (`Cmd/Ctrl + K`) routing.

* **Documentation & Specifications**:
  * [docs/systems_design_spec.md](./docs/systems_design_spec.md) - System specifications for Kafka pipelines, Go WebSocket lifecycles, and responsive Svelte layout grid breakpoints.
  * [docs/implementation_plan.md](./docs/implementation_plan.md) - Product mechanics, mathematical TWPM proofs, database transaction orderings, and project roadmaps.

* **Automated Tests**:
  * [tests/test_clob.py](./tests/test_clob.py) - Unit and integration tests for matching algorithms, order book depths, and synthetic mint cash limits.
  * [tests/test_api.py](./tests/test_api.py) - Routes and query validation checks for the FastAPI gateway.
  * [tests/test_clob_e2e.py](./tests/test_clob_e2e.py) - Concurrency lock stress tests verifying exact cash conservation invariants under parallel trading threads.

---

## Getting Started

### Prerequisites
* Python 3.8+ (Conda environment recommended)
* Node.js 18+ & npm

### Backend Setup
1. Verify database migration structures are created in SQLite:
   ```bash
   python setup_clob_tables.py
   ```
2. Start the FastAPI development backend server:
   ```bash
   uvicorn api:app --reload
   ```
   * The API docs will be available at `http://127.0.0.1:8000/docs`.

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Svelte and client-side dependencies:
   ```bash
   npm install
   ```
3. Boot up the Vite developer client:
   ```bash
   npm run dev
   ```
   * Open the local client in your browser (usually `http://localhost:5173`).

### Running the Test Suite
Ensure tests run cleanly to verify the integrity of the matching engine:
```bash
pytest tests/test_clob.py
pytest tests/test_api.py
pytest tests/test_clob_e2e.py
```
