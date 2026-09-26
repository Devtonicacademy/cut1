import httpx
import pytest
from starlette.testclient import TestClient

from apps.api.app.main import app
from apps.bot.telegram_bot import TelegramBettingBot

client = TestClient(app)


class _ApiThroughTestClient(httpx.AsyncBaseTransport):
    """Routes the bot's HTTP calls to the in-process API."""
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        res = client.request(request.method, str(request.url), content=request.content, headers=dict(request.headers))
        return httpx.Response(res.status_code, content=res.content, headers=res.headers)


@pytest.fixture
def bot(monkeypatch):
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: original(transport=_ApiThroughTestClient()))
    return TelegramBettingBot(api_url="http://testserver/api/v1")


def test_bot_has_api_url():
    assert TelegramBettingBot().api_url


@pytest.mark.asyncio
async def test_daily_slip_message_is_honest(bot):
    message = await bot.get_daily_banker(10000.0)
    assert "DAILY SLIP" in message and "Chance all picks win" in message
    assert "Code" not in message  # no fake booking codes
    assert "18+" in message


@pytest.mark.asyncio
async def test_value_bet_message(bot):
    message = await bot.get_value_bets(10000.0)
    assert "18+" in message
