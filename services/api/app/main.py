from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Guardrails, Trade, Ledger, Wallet, AuditLog, StrategyProfile
from app.exchange import exchange_adapter
from app.agent import agent_runner
from app.config import settings
from app import notifier

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

async def write_audit(db: AsyncSession, event_type: str, detail: str = "") -> None:
    db.add(AuditLog(event_type=event_type, detail=detail))
    await db.flush()

# --------------------------------------------------------------------------- #
# App lifespan
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    await agent_runner.start()
    yield
    await agent_runner.stop()
    await exchange_adapter.close()

app = FastAPI(
    title="OpenClaw Trading Platform API",
    description="Backend for autonomous AI trading agents",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #

@app.get("/")
async def root():
    return {"message": "OpenClaw Trading API is live"}

@app.get("/health")
async def health():
    return {"status": "healthy", "agent_running": agent_runner.running}

# --------------------------------------------------------------------------- #
# Market data
# --------------------------------------------------------------------------- #

@app.get("/markets")
async def get_markets():
    ticker = await exchange_adapter.fetch_ticker("BTC/USDT")
    if not ticker:
        return {"markets": []}
    return {
        "markets": [
            {"pair": "BTC/USDT", "bid": ticker.get("bid"), "ask": ticker.get("ask"), "last": ticker.get("last")}
        ]
    }

# --------------------------------------------------------------------------- #
# Trades
# --------------------------------------------------------------------------- #

@app.get("/trades")
async def get_trades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).order_by(Trade.timestamp.desc()).limit(20))
    trades = result.scalars().all()
    return {"trades": [
        {
            "id": t.id,
            "pair": t.pair,
            "side": t.side,
            "qty": t.qty,
            "price": t.price,
            "pnl": t.pnl,
            "reasoning": t.reasoning,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        }
        for t in trades
    ]}

# --------------------------------------------------------------------------- #
# PnL
# --------------------------------------------------------------------------- #

@app.get("/pnl")
async def get_pnl(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    def _sum_pnl(trades):
        return sum(t.pnl for t in trades if t.pnl is not None)

    all_result = await db.execute(select(Trade))
    all_trades = all_result.scalars().all()

    day_result = await db.execute(select(Trade).where(Trade.timestamp >= day_ago))
    day_trades = day_result.scalars().all()

    week_result = await db.execute(select(Trade).where(Trade.timestamp >= week_ago))
    week_trades = week_result.scalars().all()

    return {
        "daily_pnl": round(_sum_pnl(day_trades), 4),
        "weekly_pnl": round(_sum_pnl(week_trades), 4),
        "all_time_pnl": round(_sum_pnl(all_trades), 4),
    }

# --------------------------------------------------------------------------- #
# Guardrails
# --------------------------------------------------------------------------- #

class GuardrailUpdate(BaseModel):
    max_position_size: float
    max_leverage: float
    daily_loss_limit: float
    is_active: bool

@app.get("/guardrails")
async def get_guardrails(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guardrails).order_by(Guardrails.id.desc()).limit(1))
    guardrails = result.scalar_one_or_none()
    if not guardrails:
        guardrails = Guardrails()
        db.add(guardrails)
        await db.commit()
        await db.refresh(guardrails)
    return {
        "max_position_size": guardrails.max_position_size,
        "max_leverage": guardrails.max_leverage,
        "daily_loss_limit": guardrails.daily_loss_limit,
        "is_active": guardrails.is_active,
    }

@app.post("/guardrails")
async def update_guardrails(update: GuardrailUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guardrails).order_by(Guardrails.id.desc()).limit(1))
    guardrails = result.scalar_one_or_none()
    if not guardrails:
        guardrails = Guardrails()
        db.add(guardrails)
    guardrails.max_position_size = update.max_position_size
    guardrails.max_leverage = update.max_leverage
    guardrails.daily_loss_limit = update.daily_loss_limit
    guardrails.is_active = update.is_active
    await write_audit(db, "guardrails_updated",
                      f"max_pos={update.max_position_size}, max_lev={update.max_leverage}, loss_limit={update.daily_loss_limit}")
    await db.commit()
    return {"status": "success"}

# --------------------------------------------------------------------------- #
# Agent control
# --------------------------------------------------------------------------- #

@app.post("/agent/stop")
async def stop_agent(db: AsyncSession = Depends(get_db)):
    await agent_runner.stop()
    await write_audit(db, "agent_stopped")
    await db.commit()
    await notifier.notify("🛑 Agent stopped manually.")
    return {"status": "stopped"}

@app.post("/agent/start")
async def start_agent(db: AsyncSession = Depends(get_db)):
    await agent_runner.start()
    await write_audit(db, "agent_started")
    await db.commit()
    await notifier.notify("▶️ Agent started manually.")
    return {"status": "started"}

# --------------------------------------------------------------------------- #
# Ledger & Withdrawals
# --------------------------------------------------------------------------- #

@app.get("/ledger")
async def get_ledger(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ledger).where(Ledger.balance_type == "withdrawal"))
    ledger = result.scalar_one_or_none()
    return {"withdrawal_balance": ledger.balance if ledger else 0.0}

class WithdrawRequest(BaseModel):
    amount: float
    wallet_address: str

@app.post("/withdraw")
async def execute_withdrawal(req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.address == req.wallet_address).where(Wallet.whitelisted == True)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet address is not whitelisted.")

    ledger_result = await db.execute(select(Ledger).where(Ledger.balance_type == "withdrawal"))
    ledger = ledger_result.scalar_one_or_none()
    if not ledger or ledger.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient withdrawable balance.")

    ledger.balance -= req.amount
    await write_audit(db, "withdrawal", f"${req.amount} → {req.wallet_address}")
    await db.commit()
    await notifier.notify(f"💸 Withdrawal of ${req.amount:.2f} to `{req.wallet_address}`")
    return {"status": "success", "message": f"Withdrew {req.amount} to {req.wallet_address}"}

class WalletAddRequest(BaseModel):
    address: str

@app.post("/wallets")
async def add_wallet(req: WalletAddRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wallet).where(Wallet.address == req.address))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(address=req.address, whitelisted=True)
        db.add(wallet)
        await write_audit(db, "wallet_added", req.address)
        await db.commit()
    return {"status": "success", "address": wallet.address}

@app.get("/wallets")
async def get_wallets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wallet).where(Wallet.whitelisted == True))
    wallets = result.scalars().all()
    return {"wallets": [{"address": w.address} for w in wallets]}

# --------------------------------------------------------------------------- #
# Audit Log
# --------------------------------------------------------------------------- #

@app.get("/audit-log")
async def get_audit_log(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50))
    entries = result.scalars().all()
    return {"entries": [
        {
            "id": e.id,
            "event_type": e.event_type,
            "detail": e.detail,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in entries
    ]}

# --------------------------------------------------------------------------- #
# Strategy Profile
# --------------------------------------------------------------------------- #

VALID_PROFILES = {"conservative", "balanced", "aggressive"}

class StrategyUpdate(BaseModel):
    profile: str

@app.get("/strategy")
async def get_strategy(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StrategyProfile).where(StrategyProfile.is_active == True).limit(1))
    sp = result.scalar_one_or_none()
    current = sp.profile if sp else settings.STRATEGY_PROFILE
    return {"profile": current, "options": sorted(VALID_PROFILES)}

@app.post("/strategy")
async def update_strategy(update: StrategyUpdate, db: AsyncSession = Depends(get_db)):
    if update.profile not in VALID_PROFILES:
        raise HTTPException(status_code=400, detail=f"Invalid profile. Choose from: {VALID_PROFILES}")

    result = await db.execute(select(StrategyProfile).where(StrategyProfile.is_active == True).limit(1))
    sp = result.scalar_one_or_none()
    if not sp:
        sp = StrategyProfile()
        db.add(sp)
    old = sp.profile
    sp.profile = update.profile
    # Reflect in live settings so brain picks it up on the next tick
    settings.STRATEGY_PROFILE = update.profile
    await write_audit(db, "strategy_changed", f"{old} → {update.profile}")
    await db.commit()
    await notifier.notify(f"⚙️ Strategy profile changed: **{old}** → **{update.profile}**")
    return {"status": "success", "profile": update.profile}
