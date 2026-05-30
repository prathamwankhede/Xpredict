# Graph Report - predict  (2026-05-29)

## Corpus Check
- 18 files · ~14,012 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 198 nodes · 208 edges · 40 communities (16 shown, 24 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d1e965a7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_Prediction Market Strategic Specification|Prediction Market Strategic Specification]]
- [[_COMMUNITY_High-Performance CLOB Engine Design|High-Performance CLOB Engine Design]]
- [[_COMMUNITY_Project Lifecycle & Planning Roadmap|Project Lifecycle & Planning Roadmap]]
- [[_COMMUNITY_Codebase Audits & Prototype Debt|Codebase Audits & Prototype Debt]]
- [[_COMMUNITY_Premium UI/UX & Visual Design Specs|Premium UI/UX & Visual Design Specs]]
- [[_COMMUNITY_Developer Session Logs & Progress|Developer Session Logs & Progress]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]

## God Nodes (most connected - your core abstractions)
1. `process_order()` - 11 edges
2. `str` - 10 edges
3. `Platform Architecture & Product Specification: A Hybrid Venture-Scale Prediction Market` - 10 edges
4. `Central Limit Order Book (CLOB) Implementation Plan` - 9 edges
5. `Order` - 7 edges
6. `match_taker_order()` - 7 edges
7. `update_position()` - 7 edges
8. `OrderBook` - 6 edges
9. `connect` - 6 edges
10. `Phases` - 6 edges

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

## Communities (40 total, 24 thin omitted)

### Community 0 - "CLOB Matching Engine Core"
Cohesion: 0.14
Nodes (20): bool, float, str, Connection, Cursor, int, cancel_order(), get_orderbook() (+12 more)

### Community 1 - "Prediction Platform Architecture"
Cohesion: 0.14
Nodes (14): placeBet Function, match_taker_order Function, Order Dataclass, OrderBook Class, process_order Function, update_position Function, Synthetic Order Matching Mechanism, Architectural Findings and Existing Prototype Analysis (+6 more)

### Community 2 - "Pari-Mutuel Bet Placing & Markets"
Cohesion: 0.35
Nodes (10): bool, connect, float, str, create_market(), get_market(), getBet(), getBets() (+2 more)

### Community 3 - "Market Resolution & TWPM Math"
Cohesion: 0.26
Nodes (8): datetime, connect, float, str, distribute_winnings(), get_market_resolution(), resolve_market(), time_weight()

### Community 4 - "Web API Routing & Logic"
Cohesion: 0.13
Nodes (22): str, BaseModel, cancel_order(), OrderRequest, place_order(), Returns the aggregated L2 orderbook bids and asks for YES and NO outcomes., Retrieves all open share positions (YES/NO shares, average prices) for a user., # TODO: add auth tokens for users (+14 more)

### Community 5 - "Antigravity CLI Resource Metadata"
Cohesion: 0.40
Nodes (4): id, name, projectResources, resources

### Community 6 - "Market Resolution Endpoint Mappings"
Cohesion: 0.67
Nodes (3): read_market_resolution Endpoint, distribute_winnings Function, get_market_resolution Function

### Community 29 - "Prediction Market Strategic Specification"
Cohesion: 0.08
Nodes (23): 1. Executive Summary & Strategic Vision, 2.1 The Time-Weighted Pari-Mutuel (TWPM) Formulation, 2.2 CLOB vs. AMM vs. TWPM: Technical & Economic Tradeoffs, 2. Product Architecture & Market Mechanics, 3. Database Modeling (PostgreSQL Schemas), 4.1 Recommended Technology Stack, 4.2 Database Transaction & Deadlock Strategy, 4. Systems Architecture & Scalability Strategy (+15 more)

### Community 30 - "High-Performance CLOB Engine Design"
Cohesion: 0.12
Nodes (16): 1. System Requirements & Goals, 2. Structural & Language Tradeoffs (Go vs. Rust vs. Python), 3.1 The 99-Price-Bucket Optimization, 3.2 Struct Definitions (Go), 3. High-Performance In-Memory Data Structures, 4.1 Match Types Explained, 4.2 Core Matching Algorithm Logic (Pseudocode), 4. The Matching & Contract-Minting Algorithm (+8 more)

### Community 31 - "Project Lifecycle & Planning Roadmap"
Cohesion: 0.18
Nodes (10): Decisions, Errors Encountered, Goal, Phase 1: Research & Codebase Analysis (In Progress), Phase 2: System Architecture Design, Phase 3: Database & API Modeling, Phase 4: Risk, Security, & Compliance, Phase 5: MVP Scope & Long-Term Roadmap (+2 more)

### Community 32 - "Codebase Audits & Prototype Debt"
Cohesion: 0.29
Nodes (6): Architectural Findings: Existing Prototype Analysis, Core Mechanics, Financial Matching & Settlement, Scaling Goals for Venture-Scale Architecture, Technical Debt & Prototype Limitations, Time Weight Decay Function

### Community 33 - "Premium UI/UX & Visual Design Specs"
Cohesion: 0.40
Nodes (5): 6.1 Design Tokens & Aesthetics, 6.2 Component Hierarchy (Main Dashboards), 6.3 Accessibility (a11y) & UX Polish, 6. Premium UI/UX & Visual Engineering, Detail Page UI Layout (Desktop Split View):

### Community 34 - "Developer Session Logs & Progress"
Cohesion: 0.50
Nodes (3): 2026-05-28 Session, 2026-05-29 Session, Session Log & Progress

## Knowledge Gaps
- **83 isolated node(s):** `Connection`, `Cursor`, `float`, `float`, `bool` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Platform Architecture & Product Specification: A Hybrid Venture-Scale Prediction Market` connect `Community 29` to `Community 33`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `datetime` connect `Market Resolution & TWPM Math` to `Web API Routing & Logic`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `Connection`, `Cursor`, `Loads open orders from SQLite into the in-memory books.` to the rest of the system?**
  _102 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLOB Matching Engine Core` be split into smaller, more focused modules?**
  _Cohesion score 0.14153846153846153 - nodes in this community are weakly interconnected._
- **Should `Prediction Platform Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Web API Routing & Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.12648221343873517 - nodes in this community are weakly interconnected._
- **Should `Community 29` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._