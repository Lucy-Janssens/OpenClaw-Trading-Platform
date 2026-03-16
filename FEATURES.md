# OpenClaw Features

> Priority-ordered feature list. Items implemented first are the most critical to capital safety and agent value.

## 🛡️ Level 1 — Core Safety & Infrastructure

| # | Feature | Status |
|---|---------|--------|
| 1 | **Hard Guardrails** — Max position size, leverage, daily loss that AI cannot override | ✅ Done |
| 2 | **Global Kill Switch** — Instant freeze of all agent activity | ✅ Done |
| 3 | **Exchange Connectivity** — Async Binance connection with error recovery | ✅ Done |
| 4 | **Transaction Persistence** — Postgres log of every trade and balance change | ✅ Done |

## 🧠 Level 2 — Autonomous Intelligence

| # | Feature | Status |
|---|---------|--------|
| 5 | **LLM Strategy Engine** — GPT-4o via OpenRouter to analyse markets and decide trades | ✅ Done |
| 6 | **Transparent Reasoning** — Every trade logs the AI's reasoning in the DB | ✅ Done |
| 7 | **Balance-Aware Trading** — Positions sized against real-time account equity | ✅ Done |
| 8 | **Self-Healing Loop** — Background execution loop with auto-recovery | ✅ Done |

## 💰 Level 3 — Funds & Risk Management

| # | Feature | Status |
|---|---------|--------|
| 9 | **Automated Profit Sweeping** — Moves % of realised gains to a safe withdrawal ledger | ✅ Done |
| 10 | **Whitelisted Withdrawals** — Fund movements restricted to pre-approved wallets | ✅ Done |
| 11 | **PnL Tracking** — Real-time daily/weekly performance calculations | 🏗️ Planned |
| 12 | **Audit Log** — History of all manual interventions and config changes | 🏗️ Planned |

## 📊 Level 4 — Visibility & UX

| # | Feature | Status |
|---|---------|--------|
| 13 | **Dashboard** — Live dark-mode UI for trade monitoring and agent control | ✅ Done |
| 14 | **Responsive Design** — Full control from any device | ✅ Done |
| 15 | **Push Notifications** — Discord/Telegram alerts on major events | 🏗️ Planned |
| 16 | **Strategy Profiles** — Switchable AI risk levels (Safe / Neutral / Aggressive) | 🏗️ Planned |

## 🚀 Level 5 — Accessory & Expansion

| # | Feature | Status |
|---|---------|--------|
| 17 | **Multi-Exchange Support** — Same strategy running on Kraken, Coinbase, OKX | 🏗️ Planned |
| 18 | **Backtesting Sandbox** — LLM "trades" historical data to estimate performance | 🏗️ Planned |
| 19 | **Signal Hub** — External signals (TradingView) fed as high-confidence inputs to AI | 🏗️ Planned |
| 20 | **Portfolio Analytics** — Sharpe ratio, max drawdown, win-rate charts | 🏗️ Planned |
