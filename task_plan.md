# Task Plan: Venture-Scale Prediction Market Architecture

## Goal
Fully design, plan, and architect a modern, production-grade, venture-scale prediction market platform (inspired by Polymarket and Kalshi, but incorporating and expanding upon the Time-Weighted Pari-Mutuel mechanics present in the existing codebase).

## Phases

### Phase 1: Research & Codebase Analysis (In Progress)
- [x] Inspect existing database schemas in `bet_placing.py` and `market_resolution.py`
- [x] Analyze current time-weighted pari-mutuel calculation formulas
- [x] Document limitations of the current SQLite + FastAPI setup

### Phase 2: System Architecture Design
- [x] Design the high-throughput Central Limit Order Book (CLOB) and AMM trading engines
- [x] Implement core CLOB double-auction matching engine with synthetic contract minting/burning
- [ ] Detail the real-time event streaming and push notification systems (WebSockets, Redis, Kafka)
- [ ] Plan backend infrastructure (Go/Rust for execution, Node.js/Fastify for API, PostgreSQL for state)
- [ ] Design the frontend design system, component hierarchy, and responsive UI/UX

### Phase 3: Database & API Modeling
- [x] Model PostgreSQL database schemas (with indexes, partitions, and constraints)
- [ ] Document RESTful and WebSocket API endpoints and payloads
- [ ] Draft folder structures and coding conventions

### Phase 4: Risk, Security, & Compliance
- [ ] Model security practices (oracle design, multi-sig resolution, wash trading prevention)
- [ ] Define compliance and KYC/AML flow architecture
- [ ] Draft monetization strategies and risk matrices

### Phase 5: MVP Scope & Long-Term Roadmap
- [x] Define precise boundaries between MVP and Long-term production state
- [x] Compile everything into a startup-grade master architectural document (`implementation_plan.md`) at the workspace root

## Decisions
| 2026-05-28 | Hybrid Engine (CLOB + TWPM) | Keep existing Time-Weighted Pari-Mutuel (TWPM) for specific long-tail markets while implementing CLOB/AMM for high-frequency trading. |
| 2026-05-29 | Go & Price-Bucket Array for CLOB | Select Go for matching engine implementation. Use static arrays of size 100 for bids/asks to achieve O(1) execution speed, completely bypassing tree traversal bottlenecks. |
| 2026-05-29 | Pivot to SQLite (bsname.db) | Pivot target database to SQLite (bsname.db) for the MVP. Integrate the CLOB matching engine directly with existing Python/FastAPI files to preserve your running prototype data. |

## Errors Encountered
*None yet.*
