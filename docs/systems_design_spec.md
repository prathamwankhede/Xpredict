# Systems Design Specification: Event Streaming, Backend Infrastructure, and UI/UX

This document details the architectural specification for the real-time event streaming pipelines, backend infrastructure, and frontend design system of the Venture-Scale Prediction Market platform, completing Phase 2 of the system architecture design.

---

## 1. Real-Time Event Streaming & Push Notification Systems

To achieve sub-millisecond execution and decouple high-frequency matching from persistence and user notification layers, we utilize a message-broker architecture built on **Apache Kafka**, **Redis**, and a **Go-based WebSocket Gateway**.

```
  [User Client] <=================== (WebSockets / TLS) ===================> [Go WebSocket Gateway]
                                                                                   ^
                                                                                   | (Redis Pub/Sub)
                                                                            [Redis Pub/Sub Channels]
                                                                                   ^
                                                                                   | (Publishes L2 Feeds)
  [User Order]                                                              [Matching Engine (Go)]
       |                                                                           |
       v (HTTPS POST)                                                              v (Publishes Trades)
  [API Gateway] ---- (Produces JSON) ----> [Kafka: pending-orders] -------------> [Kafka: matched-trades]
                                                                                           |
                                                                                           v (Consumes)
                                                                                  [Settlement Worker]
                                                                                           |
                                                                                           v (Batch Write)
                                                                                   [(PostgreSQL DB)]
```

### 1.1 Kafka Event Pipeline & Message Schemas

We use Apache Kafka for durable, in-order request routing. Each message is keyed by the `market_id` to guarantee that all orders and matches for a single market are processed in strict FIFO order on the same partition.

#### Topic: `pending-orders`
* **Partition Key**: `market_id`
* **JSON Schema**:
  ```json
  {
    "order_id": "uuid-v4-string",
    "market_id": "uuid-v4-string",
    "user_id": "uuid-v4-string",
    "side": "buy | sell",
    "outcome": "yes | no",
    "order_type": "limit | market",
    "price": 62,
    "quantity": 100,
    "created_at": "2026-06-15T02:50:00.000Z"
  }
  ```

#### Topic: `matched-trades`
* **Partition Key**: `market_id`
* **JSON Schema**:
  ```json
  {
    "trade_id": "uuid-v4-string",
    "market_id": "uuid-v4-string",
    "buyer_id": "uuid-v4-string",
    "seller_id": "uuid-v4-string",
    "outcome": "yes | no",
    "price": 62,
    "shares": 50,
    "maker_order_id": "uuid-v4-string",
    "taker_order_id": "uuid-v4-string",
    "match_type": "direct | synthetic_mint | synthetic_burn",
    "created_at": "2026-06-15T02:50:00.120Z"
  }
  ```

### 1.2 Redis Pub/Sub Topology & L2 Orderbook Cache

* **L2 Cache Storage**: The current aggregated L2 order book depth for each market is stored in Redis under the hash key `orderbook:{market_id}`.
  * Structure:
    * `yes_bids` -> `{"0.62": 2400, "0.61": 3200}`
    * `yes_asks` -> `{"0.63": 1900, "0.64": 2700}`
* **Pub/Sub Channels**:
  * `market:{market_id}:depth`: Emits delta updates or full L2 snapshots when the order book changes.
  * `market:{market_id}:trades`: Emits real-time trade execution reports.

### 1.3 Go WebSocket Gateway Architecture

The WebSocket Gateway maintains long-lived TCP connections with clients, handles client subscriptions, and broadcasts Redis Pub/Sub updates to connected clients.

* **Concurrency Model**: Go's Goroutines are spawned per connection (one reader, one writer).
* **Connection Lifecycle**:
  1. **Handshake**: Handled via standard HTTPS upgrade (`wss://api.platform.com/v1/stream`).
  2. **Authentication**: Clients must supply a JWT via the `token` query parameter. Connection is terminated immediately on invalid or expired token.
  3. **Heartbeat (Ping-Pong)**: 
     * The server sends a `Ping` control frame every 54 seconds.
     * The client must respond with a `Pong` frame within a 60-second read deadline. This prevents load balancers (e.g. AWS ALB, Nginx) from dropping idle connections (default timeout is usually 60s).
  4. **Scaling & Load Balancing**: Horizontal scale is achieved by deploying multiple WebSocket instances behind an ALB with sticky sessions disabled (connections are stateless and sync via Redis Pub/Sub).

---

## 2. Backend Infrastructure & Scalability Strategy

The backend platform is built as a set of focused microservices using a shared PostgreSQL instance for persistent source-of-truth state.

```
/platform
  ├── /api-gateway            # Fastify API (TypeScript)
  ├── /matching-engine        # Go in-memory CLOB execution engine
  ├── /settlement-worker      # Go event consumer & Postgres persistence
  ├── /postgres-schema        # Database migration files
  └── /shared-proto           # Protobuf contracts for internal RPCs
```

### 2.1 Microservices Architecture

1. **API Gateway (Node.js/Fastify)**:
   - High-throughput entry point for REST API requests (e.g., auth, market listings, user profiles).
   - Validates user balances against Redis cache before producing to the Kafka `pending-orders` queue.
   - Database connection pool using `pg-pool` with:
     * `max: 50` connections
     * `idleTimeoutMillis: 30000`
2. **Matching Engine (Go)**:
   - In-memory order matching, utilizing the 99-price-bucket static array optimization for $O(1)$ updates.
   - Subscribes to Kafka `pending-orders` and emits to Redis Pub/Sub and Kafka `matched-trades`.
3. **Settlement Worker (Go)**:
   - Consumes Kafka `matched-trades`.
   - Batches DB operations (up to 100 rows or 50ms intervals) to optimize PostgreSQL transaction writing.
   - Utilizes `pgxpool` with:
     * `MaxConns: 20`
     * `MinConns: 5`

### 2.2 PostgreSQL Schema Optimization & Indexes

PostgreSQL stores persistent state. We use specific indexes and partitioning to maintain query performance:

* **Trades Partitioning**: The `trades` table is partitioned by range on the `created_at` timestamp (monthly partitions) to keep active indexes small.
* **Indexes**:
  * `idx_orders_market_user`: Composite index on `orders(market_id, user_id)` for quick lookup of active user orders per market.
  * `idx_trades_market_created`: Index on `trades(market_id, created_at DESC)` for trade history pagination.
  * `idx_user_positions_composite`: Unique composite index on `user_positions(user_id, market_id)`.

---

## 3. Frontend Design System & Component Hierarchy

The frontend is implemented in Svelte/Vite using a customized Tailwind CSS styling system.

### 3.1 Design System Tokens & Aesthetics

* **Theme**: Deep space dark mode.
* **Color Palette**:
  - `bg-base`: `hsl(222, 47%, 6%)` (Deep dark slate)
  - `bg-surface`: `hsla(222, 47%, 11%, 0.7)` (Lighter slate with transparency)
  - `border-glass`: `hsla(217, 32%, 18%, 0.5)` (Subtle borders)
  - `color-primary`: `hsl(180, 100%, 50%)` (Bright neon cyan for branding and UI focus)
  - `color-success` (YES): `hsl(142, 76%, 45%)` (Vibrant green)
  - `color-danger` (NO): `hsl(350, 89%, 60%)` (Vibrant rose red)
* **Glassmorphism Spec**:
  - CSS rule: `backdrop-filter: blur(12px) saturate(180%);`
  - Reusable class: `.card-glass { background: var(--bg-surface); border: 1px solid var(--border-glass); backdrop-filter: blur(12px); }`
* **Typography Stack**:
  - Heading & Display: **Space Grotesk** (Tech-focused, geometric, clean)
  - UI & Body: **Sora** (Highly legible, modern sans-serif)

### 3.2 Component Hierarchy

```
App (Main layout wrapper with NewsTicker overlay)
 ├── Navigation (Full-width header with "Start Trading" CTA)
 ├── SearchOverlay (Traps focus, handles Cmd/Ctrl+K quick search)
 ├── Dashboard View
 │    ├── HeroSpotlight (Highlights high-volume active market)
 │    ├── MarketFilters (Filter grids by category or engine type)
 │    └── MarketsGrid
 │         └── MarketCard (Bento card layout with YES/NO CTA quick bet)
 └── MarketDetail View (Desktop split column layout)
      ├── MarketHeader (Title, engine type, volume statistics, resolution time)
      ├── ChartArea (High-frequency price chart showing probability trends)
      ├── OrderBook (Aggregated bids/asks tables with depth volume bars)
      ├── RecentTrades (Scrolling list of latest filled trades)
      └── TradingTerminal (Buy/Sell toggle, Order Type tab, Slippage/Premium estimations)
```

### 3.3 Responsive Breakpoints & Mobile Optimization

- **Mobile First Layout**: Multi-column grids default to single-column on mobile.
- **Breakpoints**:
  - `md` (`768px`): Splits Dashboard into two columns, adjusts search overlay text size.
  - `lg` (`1024px`): Splits MarketDetail page into 3-column view: left/center for charts/orderbook, right for trading terminal.
- **A11y (Accessibility)**:
  - Focus-visible outline rings on all interactive elements.
  - ARIA attributes (`aria-expanded`, `aria-hidden`, etc.) wired for search overlay.
  - Reduced-motion media query checks to disable custom ticker animations.
