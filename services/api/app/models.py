from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Guardrails(Base):
    __tablename__ = "guardrails"
    id = Column(Integer, primary_key=True, index=True)
    max_position_size = Column(Float, default=0.01) # e.g. Max 0.01 BTC
    max_leverage = Column(Float, default=1.0)
    daily_loss_limit = Column(Float, default=100.0) # in USD
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String, index=True)
    side = Column(String) # "buy" or "sell"
    qty = Column(Float)
    price = Column(Float)
    pnl = Column(Float, nullable=True)  # realised PnL for this trade in USD
    reasoning = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Ledger(Base):
    __tablename__ = "ledgers"
    id = Column(Integer, primary_key=True, index=True)
    balance_type = Column(String, unique=True) # "trading" or "withdrawal"
    balance = Column(Float, default=0.0)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True)
    whitelisted = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # e.g. "guardrails_updated", "agent_stopped"
    detail = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class StrategyProfile(Base):
    __tablename__ = "strategy_profiles"
    id = Column(Integer, primary_key=True, index=True)
    profile = Column(String, default="balanced")  # conservative | balanced | aggressive
    is_active = Column(Boolean, default=True)
