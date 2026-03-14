import pytest
from app.agent import AgentRunner
from app.models import Guardrails
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_agent_respects_guardrails():
    agent = AgentRunner()
    agent.trade_qty = 10.0 # Huge amount
    
    # Mock guardrail that should block this trade
    mock_guardrail = Guardrails(
        max_position_size=1.0,
        max_leverage=1.0,
        daily_loss_limit=100.0,
        is_active=True
    )
    
    # We don't ACTUALLY want to hit DB or Binance in this unit test. 
    # Just checking internal logic: if we mock DB return, does it abort?
    
    with patch('app.agent.AsyncSessionLocal') as mock_session_maker:
        mock_session = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        # Async mock for session.execute
        mock_execute = MagicMock()
        mock_execute.scalar_one_or_none.return_value = mock_guardrail
        mock_session.execute.return_value = mock_execute
        
        with patch('app.agent.logger.warning') as mock_warning:
            await agent.tick()
            
            # Since trade_qty (10.0) > max_position_size (1.0), we expect a warning and return Early!
            mock_warning.assert_called_with(
                f"Trade quantity {agent.trade_qty} exceeds max_position_size {mock_guardrail.max_position_size}. Skipping."
            )
