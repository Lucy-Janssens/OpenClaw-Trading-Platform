import ccxt.async_support as ccxt
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class BinanceAdapter:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET,
            'enableRateLimit': True,
        })
        if settings.TESTNET:
            self.exchange.set_sandbox_mode(True)
            logger.info("Binance adapter initialized in Testnet mode.")

    async def fetch_markets(self):
        try:
            markets = await self.exchange.load_markets()
            return markets
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return None

    async def fetch_ticker(self, pair: str):
        try:
            ticker = await self.exchange.fetch_ticker(pair)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {pair}: {e}")
            return None

    async def fetch_balance(self):
        try:
            balance = await self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    async def create_market_order(self, pair: str, side: str, amount: float):
        try:
            # Note: Testnet requires minimum amounts. e.g. BTC/USDT minimum is 0.001
            order = await self.exchange.create_market_order(pair, side, amount)
            logger.info(f"Order created: {order}")
            return order
        except Exception as e:
            logger.error(f"Error creating order {side} {amount} {pair}: {e}")
            return None

    async def close(self):
        await self.exchange.close()

# Singleton usage
exchange_adapter = BinanceAdapter()
