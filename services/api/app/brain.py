import logging
import json
import httpx
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

STRATEGY_PREAMBLES = {
    "conservative": (
        "You are a CONSERVATIVE crypto trading agent. "
        "Prioritise capital preservation above all else. "
        "Prefer HOLD over any trade unless the signal is extremely strong. "
        "Never risk more than 0.5% of balance on a single trade."
    ),
    "balanced": (
        "You are a BALANCED crypto trading agent. "
        "Seek moderate growth while managing risk sensibly. "
        "Act on clear technical signals and avoid overtrading."
    ),
    "aggressive": (
        "You are an AGGRESSIVE crypto trading agent. "
        "Maximise returns by acting on momentum signals quickly. "
        "Higher risk is acceptable when the opportunity is clear."
    ),
}

class TradingBrain:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    def _profile_preamble(self) -> str:
        profile = getattr(settings, "STRATEGY_PROFILE", "balanced").lower()
        return STRATEGY_PREAMBLES.get(profile, STRATEGY_PREAMBLES["balanced"])

    async def decide(self, market_data: Dict[str, Any], balance_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Returns a decision dict:
        {"side": "buy" | "sell" | "hold", "reasoning": "..."}
        """
        if not self.api_key:
            return self._heuristic_decision(market_data, symbol)

        if self.provider in ["openai", "openrouter"]:
            return await self._openai_compatible_decision(market_data, balance_data, symbol)

        return self._heuristic_decision(market_data, symbol)

    def _heuristic_decision(self, market_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        price = market_data.get("last", 0)
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            price_val = 0.0

        if int(price_val) % 2 == 0:
            return {"side": "buy", "reasoning": f"Price {price_val} — heuristic buy signal for {symbol}."}
        return {"side": "sell", "reasoning": f"Price {price_val} — heuristic sell signal for {symbol}."}

    async def _openai_compatible_decision(self, market_data: Dict[str, Any], balance_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        url = (
            "https://openrouter.ai/api/v1/chat/completions"
            if self.provider == "openrouter"
            else "https://api.openai.com/v1/chat/completions"
        )
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/OpenClaw/OpenClaw"
            headers["X-Title"] = "OpenClaw Trading"

        preamble = self._profile_preamble()
        prompt = f"""
{preamble}

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
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=20.0)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return self._heuristic_decision(market_data, symbol)

trading_brain = TradingBrain()
