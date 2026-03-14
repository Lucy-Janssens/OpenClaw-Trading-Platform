import asyncio
import logging
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Guardrails, Trade, Ledger
from app.exchange import exchange_adapter
from app.config import settings
from app.brain import trading_brain

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self):
        self.running = False
        self.task = None
        self.symbol = "BTC/USDT"
        self.trade_qty = 0.002 # Dummy amount to trade

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self.loop())
        logger.info("Agent script started")

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Agent script stopped")

    async def loop(self):
        # Wait a bit before starting the loop
        await asyncio.sleep(5)
        while self.running:
            try:
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
            await asyncio.sleep(30) # Tick every 30 seconds

    async def tick(self):
        logger.info("Agent tick...")
        
        async with AsyncSessionLocal() as session:
            # 1. Check Guardrails
            guardrails = await session.execute(select(Guardrails).where(Guardrails.is_active == True))
            guardrails = guardrails.scalar_one_or_none()
            if not guardrails:
                logger.warning("No active guardrails found. Agent paused.")
                return

            if self.trade_qty > guardrails.max_position_size:
                logger.warning(f"Trade quantity {self.trade_qty} exceeds max_position_size {guardrails.max_position_size}. Skipping.")
                return

            # 2. Fetch Market Price & Balance
            ticker = await exchange_adapter.fetch_ticker(self.symbol)
            balance = await exchange_adapter.fetch_balance()
            
            if not ticker:
                logger.warning(f"Could not fetch ticker for {self.symbol}")
                return
                
            current_price = ticker.get('last')
            logger.info(f"Current {self.symbol} price: {current_price}")

            # 3. AI Brain Strategy
            decision = await trading_brain.decide(ticker, balance, self.symbol)
            side = decision.get("side", "hold").lower()
            reasoning = decision.get("reasoning", "No reasoning provided.")

            if side == "hold":
                logger.info(f"Agent decided to HOLD. Reason: {reasoning}")
                return
            
            # 4. Execute Trade (Real or Testnet via CCXT)
            logger.info(f"Agent decided to {side} {self.trade_qty} {self.symbol}. Reason: {reasoning}")
            order = await exchange_adapter.create_market_order(self.symbol, side, self.trade_qty)
            
            if order:
                # 5. Log Trade to DB
                executed_price = order.get('average') or order.get('price') or current_price
                new_trade = Trade(
                    pair=self.symbol,
                    side=side,
                    qty=self.trade_qty,
                    price=executed_price,
                    reasoning=reasoning
                )
                session.add(new_trade)
                
                # 6. Simulate Profit Sweeping to Withdrawal Ledger
                if random.random() > 0.5:
                    sweep_amount = (self.trade_qty * executed_price) * 0.01 
                    ledger = await session.execute(select(Ledger).where(Ledger.balance_type == "withdrawal"))
                    ledger = ledger.scalar_one_or_none()
                    
                    if not ledger:
                        ledger = Ledger(balance_type="withdrawal", balance=0.0)
                        session.add(ledger)
                    
                    ledger.balance += sweep_amount
                    logger.info(f"Swept {sweep_amount:.2f} to withdrawal ledger. Total: {ledger.balance:.2f}")

                await session.commit()
            else:
                logger.warning("Order failed, skipping DB record.")

agent_runner = AgentRunner()
