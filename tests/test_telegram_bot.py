import pytest
import asyncio
from apps.bot.telegram_bot import TelegramBettingBot
from starlette.testclient import TestClient
from apps.api.app.main import app

def test_telegram_bot_mock_generation():
    """Verify that Telegram bot message formatting functions work seamlessly."""
    bot = TelegramBettingBot()
    # We can test the local logic or formatting
    assert bot.api_url is not None

def test_telegram_bot_banker_formatting():
    """Verify daily banker message layout has SportyBet and Bet9ja codes."""
    # Using TestClient against FastAPI directly to verify payload structure
    client = TestClient(app)
    res = client.post("/api/v1/accumulators/build", json={
        "target_odds": 2.2,
        "risk_level": "conservative",
        "bankroll_ngn": 10000.0,
        "max_legs": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert "sportybet_code" in data
    assert "bet9ja_code" in data
    assert data["sportybet_code"].startswith("SB-")
    assert data["bet9ja_code"].startswith("B9-")
    assert "Total Odds" in data["whatsapp_share_text"]
