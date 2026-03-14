from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Guardrails, Trade, Ledger, Wallet
from app.exchange import exchange_adapter
from app.agent import agent_runner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup on startup
    await agent_runner.start()
    yield
    # Cleanup on shutdown
    await agent_runner.stop()
    await exchange_adapter.close()

app = FastAPI(
    title="OpenClaw Trading Platform API",
    description="Backend for autonomous AI trading agents",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OpenClaw Trading API is live"}

@app.get("/health")
async def health():
    return {"status": "healthy", "agent_running": agent_runner.running}

# --- Market Data ---

@app.get("/markets")
async def get_markets():
    # Only return BTC/USDT to keep MVP simple
    ticker = await exchange_adapter.fetch_ticker("BTC/USDT")
    if not ticker:
        return {"markets": []}
    return {
        "markets": [
            {
                "pair": "BTC/USDT", 
                "bid": ticker.get('bid'), 
                "ask": ticker.get('ask'),
                "last": ticker.get('last')
            }
        ]
    }

# --- Trades ---

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
            "reasoning": t.reasoning,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None
        } for t in trades
    ]}

# --- Guardrails ---

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
        # Create default
        guardrails = Guardrails()
        db.add(guardrails)
        await db.commit()
        await db.refresh(guardrails)
    return {
        "max_position_size": guardrails.max_position_size,
        "max_leverage": guardrails.max_leverage,
        "daily_loss_limit": guardrails.daily_loss_limit,
        "is_active": guardrails.is_active
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
    
    await db.commit()
    return {"status": "success"}

# --- Agent Control ---

@app.post("/agent/stop")
async def stop_agent():
    await agent_runner.stop()
    return {"status": "stopped"}

@app.post("/agent/start")
async def start_agent():
    await agent_runner.start()
    return {"status": "started"}

# --- Ledger & Withdrawals ---

@app.get("/ledger")
async def get_ledger(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ledger).where(Ledger.balance_type == "withdrawal"))
    ledger = result.scalar_one_or_none()
    return {
        "withdrawal_balance": ledger.balance if ledger else 0.0
    }

class WithdrawRequest(BaseModel):
    amount: float
    wallet_address: str

@app.post("/withdraw")
async def execute_withdrawal(req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    wallet_result = await db.execute(select(Wallet).where(Wallet.address == req.wallet_address).where(Wallet.whitelisted == True))
    wallet = wallet_result.scalar_one_or_none()
    
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet address is not whitelisted.")
        
    ledger_result = await db.execute(select(Ledger).where(Ledger.balance_type == "withdrawal"))
    ledger = ledger_result.scalar_one_or_none()
    
    if not ledger or ledger.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient withdrawable balance.")
        
    ledger.balance -= req.amount
    await db.commit()
    
    return {"status": "success", "message": f"Successfully withdrew {req.amount} to {req.wallet_address}"}

class WalletAddRequest(BaseModel):
    address: str

@app.post("/wallets")
async def add_wallet(req: WalletAddRequest, db: AsyncSession = Depends(get_db)):
    wallet_result = await db.execute(select(Wallet).where(Wallet.address == req.address))
    wallet = wallet_result.scalar_one_or_none()
    
    if not wallet:
        wallet = Wallet(address=req.address, whitelisted=True)
        db.add(wallet)
        await db.commit()
        
    return {"status": "success", "address": wallet.address}

@app.get("/wallets")
async def get_wallets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wallet).where(Wallet.whitelisted == True))
    wallets = result.scalars().all()
    return {"wallets": [{"address": w.address} for w in wallets]}
