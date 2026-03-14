import logging
import json
import httpx
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class TradingBrain:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    async def decide(self, market_data: Dict[str, Any], balance_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Takes market data and balance data, returns a decision dict:
        {
            "side": "buy" | "sell" | "hold",
            "reasoning": "string explaining why"
        }
        """
        if not self.api_key:
            return self._heuristic_decision(market_data, symbol)

        if self.provider in ["openai", "openrouter"]:
            return await self._openai_compatible_decision(market_data, balance_data, symbol)
        
        # Fallback
        return self._heuristic_decision(market_data, symbol)

    def _heuristic_decision(self, market_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Simple technical-ish decision fallback."""
        price = market_data.get('last', 0)
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            price_val = 0.0

        # Placeholder logic: if price ends in even number, buy. Else sell.
        if int(price_val) % 2 == 0:
            return {
                "side": "buy",
                "reasoning": f"Price {price_val} is even, heuristic trigger for buying {symbol}."
            }
        else:
            return {
                "side": "sell",
                "reasoning": f"Price {price_val} is odd, heuristic trigger for selling {symbol}."
            }

    async def _openai_compatible_decision(self, market_data: Dict[str, Any], balance_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        if self.provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter often appreciates these headers
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/OpenClaw/OpenClaw"
            headers["X-Title"] = "OpenClaw Trading"

        prompt = f"""
        You are an expert crypto trading agent (OpenClaw).
        Current Market Data for {symbol}: {json.dumps(market_data)}
        Current Balance: {json.dumps(balance_data)}
        
        Respond ONLY with a JSON object:
        {{
            "side": "buy" | "sell" | "hold",
            "reasoning": "short explanation of the decision based on the data"
        }}
        """
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": { "type": "json_object" }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=20.0)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return self._heuristic_decision(market_data, symbol)

trading_brain = TradingBrain()
