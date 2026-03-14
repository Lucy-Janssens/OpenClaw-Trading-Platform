# OpenClaw Trading Platform — Architecture (v2)

Overview
- AI-native, multi-venue trading workbench for OpenClaw agents
- Deploy in Docker, Python + TS UI, REST/WebSocket adapters
- Exchange and chain agnostic via unified adapters
- Human-in-the-loop for withdrawals and guardrails

Core Entities
- Agent: autonomous decision-maker (executes via tools exposed by platform)
- Market: external venues (spot, futures, DeFi)
- Wallet: user-owned custody for withdrawals
- Guardrails: risk parameters configured by user
- Withdrawable ledger: profits designated for withdrawal

Platform Layers
1) UI Layer (TS/React) – status dashboards, controls, withdrawal requests
2) API/Orchestration Layer (Python) – agent coordination, policy evaluation, risk checks
3) Venue Adapters – unified REST/WebSocket interfaces for CEXs and on-chain protocols
4) Data & Audit – market data, price streams, trade history, audit logs
5) Auth & Secrets – OAuth-like auth, API keys vaulting, key scoping to whitelisted addresses
6) SRE & Safety – hard kill, pause/resume, alerting

Data Model Essentials
- Accounts, Balances, Positions, Trades, Withdrawals
- Guardrails: maxPositionSize, maxLeverage, dailyLossLimit, exposure caps
- StrategySet: collection of Strategy instances running concurrently

MVP Scope
- Real-time price data (WS or polling)
- Read/Write access to venues via adapters
- Multi-strategy support per agent
- Withdrawable balance mechanics and manual withdrawal confirmation
- Human login via UI and role-based access

Non-Functional Requirements
- Observability: logging, metrics, tracing
- Security: key vaulting, whitelisting, minimal-privilege
- Reliability: idempotent operations, robust retries
- Scalability: Dockerized micro-services, horizontal scale

Deployment
- Docker Compose / Kubernetes for orchestration
- Tech: Python services, TS UI, Postgres for state

Notes
- This spec is MVP-oriented; we can expand to multi-tenant in future