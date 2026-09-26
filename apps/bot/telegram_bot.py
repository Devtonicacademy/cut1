"""
Telegram alert bot for LivelyBorg AI: formats the daily short slip and any
validated value bets from the API for posting to a Telegram channel.
"""

import os
import asyncio
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TOKEN_FOR_DEV")
DISCLAIMER = "_Predictions are probabilities, not guarantees. 18+ only. Bet responsibly._"


class TelegramBettingBot:
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url

    async def get_daily_banker(self, bankroll_ngn: float = 10000.0) -> str:
        """Fetches the most likely short slip (about 2.0 total odds) and formats it for Telegram."""
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.api_url}/accumulators/build",
                    json={"target_odds": 2.0, "bankroll_ngn": bankroll_ngn, "max_legs": 3},
                    timeout=10.0,
                )
            except Exception as e:
                return f"⚠️ Service temporarily unreachable: {e}"
        if res.status_code != 200:
            return "⚠️ Unable to build today's slip right now. Please try again in 5 minutes."
        data = res.json()
        if not data["legs"]:
            return "No upcoming matches with market prices and a clear favourite right now."
        message = (
            f"🟢 *LIVELYBORG AI: DAILY SLIP* 🟢\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Total Odds: *{data['total_odds']:.2f}*\n"
            f"🎯 Chance all picks win (model): *{data['win_probability'] * 100:.1f}%*\n\n"
            f"*PICKS:*\n"
        )
        for i, leg in enumerate(data["legs"], 1):
            message += f"{i}. ⚽ *{leg['match_name']}*\n"
            message += f"   👉 *{leg['market']}* ({leg['odds']:.2f}, {leg['model_probability'] * 100:.0f}%)\n"
        return message + f"\n{DISCLAIMER}"

    async def get_value_bets(self, user_bankroll: float) -> str:
        """Lists value bets, which the API only returns when they passed the backtest."""
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(f"{self.api_url}/fixtures?bankroll={user_bankroll}", timeout=10.0)
            except Exception as e:
                return f"⚠️ Error: {e}"
        if res.status_code != 200:
            return "⚠️ Could not retrieve fixtures."
        lines = []
        for f in res.json():
            for vb in (f.get("prediction") or {}).get("value_bets", [])[:1]:
                lines.append(
                    f"⚽ *{f['home_team']['name']} vs {f['away_team']['name']}*\n"
                    f"   • *{vb['market_name']}* @ {vb['market_odds']:.2f} ({vb['bookmaker']})\n"
                    f"   • Model edge: *+{vb['expected_value_pct']:.1f}%* | Stake: *₦{vb['recommended_stake_ngn']:,.0f}*\n"
                )
        if not lines:
            return "No value bets today: none of our model's edges have passed the backtest.\n\n" + DISCLAIMER
        return f"💼 *VALUE BETS* (Bankroll ₦{user_bankroll:,.0f})\n\n" + "\n".join(lines[:5]) + f"\n{DISCLAIMER}"


if __name__ == "__main__":
    bot = TelegramBettingBot()
    print(asyncio.run(bot.get_daily_banker(15000.0)))
