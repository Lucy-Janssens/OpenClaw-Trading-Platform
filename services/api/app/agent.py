import asyncio
import logging
import random
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Guardrails, Trade, Ledger, AuditLog
from app.exchange import exchange_adapter
from app.brain import trading_brain
from app import notifier

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self):
        self.running = False
        self.task: asyncio.Task | None = None
        self.symbol = "BTC/USDT"
        self.trade_qty = 0.002
        # Simple cost-basis tracking for PnL (FIFO approximation)
        self._cost_basis: float | None = None

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self.loop())
        logger.info("Agent started")

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Agent stopped")

    async def loop(self):
        await asyncio.sleep(5)
        while self.running:
            try:
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await notifier.notify(f"⚠️ Agent error: {e}")
            await asyncio.sleep(30)

    async def tick(self):
        logger.info("Agent tick…")

        async with AsyncSessionLocal() as session:
            # 1. Guardrail check
            result = await session.execute(select(Guardrails).where(Guardrails.is_active == True))
            guardrails = result.scalar_one_or_none()
            if not guardrails:
                logger.warning("No active guardrails — agent paused.")
                return

            if self.trade_qty > guardrails.max_position_size:
                msg = (
                    f"Trade qty {self.trade_qty} > max_position_size "
                    f"{guardrails.max_position_size}. Skipping."
                )
                logger.warning(msg)
                await notifier.notify(f"🛡️ Guardrail breached — {msg}")
                return

            # 2. Market data
            ticker = await exchange_adapter.fetch_ticker(self.symbol)
            balance = await exchange_adapter.fetch_balance()
            if not ticker:
                logger.warning(f"Could not fetch ticker for {self.symbol}")
                return

            current_price = float(ticker.get("last") or 0)
            logger.info(f"{self.symbol} price: {current_price}")

            # 3. AI decision
            decision = await trading_brain.decide(ticker, balance, self.symbol)
            side = decision.get("side", "hold").lower()
            reasoning = decision.get("reasoning", "No reasoning provided.")

            if side == "hold":
                logger.info(f"HOLD — {reasoning}")
                return

            logger.info(f"{side.upper()} {self.trade_qty} {self.symbol} — {reasoning}")
            order = await exchange_adapter.create_market_order(self.symbol, side, self.trade_qty)

            if order:
                executed_price = float(order.get("average") or order.get("price") or current_price)

                # 4. PnL calculation (FIFO approximation)
                pnl: float | None = None
                if side == "buy":
                    self._cost_basis = executed_price
                elif side == "sell" and self._cost_basis is not None:
                    pnl = (executed_price - self._cost_basis) * self.trade_qty
                    self._cost_basis = None

                # 5. Log trade
                new_trade = Trade(
                    pair=self.symbol,
                    side=side,
                    qty=self.trade_qty,
                    price=executed_price,
                    pnl=pnl,
                    reasoning=reasoning,
                )
                session.add(new_trade)

                # 6. Discord notification for large PnL swings
                if pnl is not None and abs(pnl) > 5:
                    emoji = "🟢" if pnl > 0 else "🔴"
                    await notifier.notify(
                        f"{emoji} Trade closed — {side.upper()} {self.trade_qty} {self.symbol} "
                        f"at ${executed_price:,.2f} | PnL: ${pnl:+.2f}"
                    )

                # 7. Profit sweep
                if random.random() > 0.5:
                    sweep_amount = (self.trade_qty * executed_price) * 0.01
                    ledger_result = await session.execute(
                        select(Ledger).where(Ledger.balance_type == "withdrawal")
                    )
                    ledger = ledger_result.scalar_one_or_none()
                    if not ledger:
                        ledger = Ledger(balance_type="withdrawal", balance=0.0)
                        session.add(ledger)
                    ledger.balance += sweep_amount
                    logger.info(f"Swept ${sweep_amount:.2f} to withdrawal ledger.")

                await session.commit()
            else:
                logger.warning("Order failed — skipping DB record.")

agent_runner = AgentRunner()
