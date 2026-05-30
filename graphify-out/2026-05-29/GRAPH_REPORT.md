# Graph Report - .  (2026-05-29)

## Corpus Check
- Corpus is ~13,998 words - fits in a single context window. You may not need a graph.

## Summary
- 108 nodes · 120 edges · 29 communities (9 shown, 20 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CLOB Matching Engine Core|CLOB Matching Engine Core]]
- [[_COMMUNITY_Prediction Platform Architecture|Prediction Platform Architecture]]
- [[_COMMUNITY_Pari-Mutuel Bet Placing & Markets|Pari-Mutuel Bet Placing & Markets]]
- [[_COMMUNITY_Market Resolution & TWPM Math|Market Resolution & TWPM Math]]
- [[_COMMUNITY_Web API Routing & Logic|Web API Routing & Logic]]
- [[_COMMUNITY_Antigravity CLI Resource Metadata|Antigravity CLI Resource Metadata]]
- [[_COMMUNITY_Market Resolution Endpoint Mappings|Market Resolution Endpoint Mappings]]
- [[_COMMUNITY_Bet Details Fetching API Endpoint|Bet Details Fetching API Endpoint]]
- [[_COMMUNITY_Market Bets Querying API Endpoint|Market Bets Querying API Endpoint]]
- [[_COMMUNITY_SQLite Trades Database Table|SQLite Trades Database Table]]
- [[_COMMUNITY_Graphify Rules & Internal Docs|Graphify Rules & Internal Docs]]
- [[_COMMUNITY_Project Planning & Requirements|Project Planning & Requirements]]
- [[_COMMUNITY_Resolution Logic Entry point|Resolution Logic Entry point]]
- [[_COMMUNITY_SQLite Users Schema|SQLite Users Schema]]
- [[_COMMUNITY_SQLite User Balances Schema|SQLite User Balances Schema]]
- [[_COMMUNITY_SQLite Ledger Transactions Schema|SQLite Ledger Transactions Schema]]
- [[_COMMUNITY_SQLite Markets Schema|SQLite Markets Schema]]
- [[_COMMUNITY_SQLite Pari-Mutuel Bets Schema|SQLite Pari-Mutuel Bets Schema]]
- [[_COMMUNITY_Web API Server Instance|Web API Server Instance]]
- [[_COMMUNITY_Betting Engine Market Creation Entrypoint|Betting Engine Market Creation Entrypoint]]
- [[_COMMUNITY_Pari-Mutuel Market Fetching|Pari-Mutuel Market Fetching]]
- [[_COMMUNITY_Pari-Mutuel User Bets Retrieval|Pari-Mutuel User Bets Retrieval]]
- [[_COMMUNITY_Svelte Root Mounting Interface|Svelte Root Mounting Interface]]
- [[_COMMUNITY_Limit Price Optimization Design|Limit Price Optimization Design]]
- [[_COMMUNITY_Event-Driven Execution Architecture|Event-Driven Execution Architecture]]
- [[_COMMUNITY_Siloed Channel Matching Model|Siloed Channel Matching Model]]
- [[_COMMUNITY_Hybrid TWPM-CLOB Liquidity Integration|Hybrid TWPM-CLOB Liquidity Integration]]

## God Nodes (most connected - your core abstractions)
1. `process_order()` - 11 edges
2. `Order` - 7 edges
3. `match_taker_order()` - 7 edges
4. `update_position()` - 7 edges
5. `OrderBook` - 6 edges
6. `connect` - 6 edges
7. `process_order Function` - 6 edges
8. `str` - 5 edges
9. `time_weight()` - 5 edges
10. `str` - 5 edges

## Surprising Connections (you probably didn't know these)
- `placeBet Function` --semantically_similar_to--> `process_order Function`  [INFERRED] [semantically similar]
  bet_placing.py → clob_engine.py
- `process_order Function` --implements--> `Central Limit Order Book Engine Concept`  [INFERRED]
  clob_engine.py → implementation_plan.md
- `match_taker_order Function` --implements--> `Synthetic Order Matching Mechanism`  [INFERRED]
  clob_engine.py → clob_implementation_plan.md
- `time_weight Function` --implements--> `Time-Weighted Pari-Mutuel Formulation`  [INFERRED]
  market_resolution.py → implementation_plan.md
- `user_positions Table` --semantically_similar_to--> `setup_clob_database Function`  [INFERRED] [semantically similar]
  postgres_schema.sql → setup_clob_tables.py

## Hyperedges (group relationships)
- **CLOB Engine Order Processing and Execution Flow** — clob_engine_process_order, clob_engine_match_taker_order, clob_engine_update_position, clob_engine_cancel_order [EXTRACTED 1.00]
- **TWPM Pari-Mutuel Pool Betting Flow** — bet_placing_placebet, market_resolution_time_weight, market_resolution_distribute_winnings [EXTRACTED 1.00]
- **Matching Engine Architecture & Optimizations** — clob_implementation_plan_99_price_bucket_optimization, clob_implementation_plan_synthetic_matching, clob_implementation_plan_event_driven_architecture, clob_implementation_plan_siloed_channel_architecture [EXTRACTED 1.00]

## Communities (29 total, 20 thin omitted)

### Community 0 - "CLOB Matching Engine Core"
Cohesion: 0.14
Nodes (20): bool, float, str, Connection, Cursor, int, cancel_order(), get_orderbook() (+12 more)

### Community 1 - "Prediction Platform Architecture"
Cohesion: 0.12
Nodes (17): placeBet Function, cancel_order Function, get_orderbook Function, match_taker_order Function, Order Dataclass, OrderBook Class, process_order Function, update_position Function (+9 more)

### Community 2 - "Pari-Mutuel Bet Placing & Markets"
Cohesion: 0.35
Nodes (10): bool, connect, float, str, create_market(), get_market(), getBet(), getBets() (+2 more)

### Community 3 - "Market Resolution & TWPM Math"
Cohesion: 0.33
Nodes (8): datetime, connect, float, str, distribute_winnings(), get_market_resolution(), resolve_market(), time_weight()

### Community 4 - "Web API Routing & Logic"
Cohesion: 0.38
Nodes (6): str, # TODO: add auth tokens for users, # TODO: add deadlock handling for db transactions, read_bet(), read_market_bets(), read_market_resolution()

### Community 5 - "Antigravity CLI Resource Metadata"
Cohesion: 0.40
Nodes (4): id, name, projectResources, resources

### Community 6 - "Market Resolution Endpoint Mappings"
Cohesion: 0.67
Nodes (3): read_market_resolution Endpoint, distribute_winnings Function, get_market_resolution Function

## Knowledge Gaps
- **39 isolated node(s):** `Connection`, `Cursor`, `float`, `float`, `bool` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Market Resolution & TWPM Math` to `Web API Routing & Logic`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `Connection`, `Cursor`, `Loads open orders from SQLite into the in-memory books.` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLOB Matching Engine Core` be split into smaller, more focused modules?**
  _Cohesion score 0.14153846153846153 - nodes in this community are weakly interconnected._
- **Should `Prediction Platform Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._