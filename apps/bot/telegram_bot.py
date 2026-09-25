"""
Telegram VIP Alert Bot for LivelyBorg AI Sports Intelligence
Provides instant delivery of +EV value drops, daily 2-odds bankers,
and SportyBet/Bet9ja booking codes to Nigerian bettors in Lagos.
"""

import os
import asyncio
import httpx
from typing import Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TOKEN_FOR_DEV")

class TelegramBettingBot:
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url

    async def get_daily_banker(self, bankroll_ngn: float = 10000.0) -> str:
        """Fetches the daily 2-odds banker and formats it for Telegram."""
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.api_url}/accumulators/build",
                    json={
                        "target_odds": 2.2,
                        "risk_level": "conservative",
                        "bankroll_ngn": bankroll_ngn,
                        "max_legs": 3
                    },
                    timeout=10.0
                )
                if res.status_code == 200:
                    data = res.json()
                    message = (
                        f"🟢 *LIVELYBORG AI: DAILY 2-ODDS BANKER* 🟢\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Total Odds: *{data['total_odds']:.2f}*\n"
                        f"🎯 Win Probability: *{data['win_probability']*100:.1f}%*\n"
                        f"💰 Rec. Kelly Stake: *₦{data['recommended_stake_ngn']:,.0f}* (Bankroll: ₦{bankroll_ngn:,.0f})\n"
                        f"💵 Potential Payout: *₦{data['potential_payout_ngn']:,.0f}*\n\n"
                        f"*MATCH SELECTIONS:*\n"
                    )
                    for i, leg in enumerate(data["legs"], 1):
                        message += f"{i}. ⚽ *{leg['match_name']}*\n"
                        message += f"   👉 Pick: *{leg['market']}* ({leg['odds']:.2f}) [EV: +{leg['ev_pct']:.1f}%]\n"

                    if data.get("cut_1_warning"):
                        message += f"\n🛡️ *{data['cut_1_warning']}*\n"

                    message += (
                        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📲 *SportyBet Code:* `{data['sportybet_code']}`\n"
                        f"📲 *Bet9ja Code:* `{data['bet9ja_code']}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚡ _Copy code directly into your app before lines move!_"
                    )
                    return message
                else:
                    return "⚠️ Unable to generate banker slip right now. Please try again in 5 minutes."
            except Exception as e:
                return f"⚠️ Service temporarily unreachable: {e}"

    async def calculate_custom_stake(self, user_bankroll: float) -> str:
        """Calculates personalized Kelly stake for the user's specific bankroll."""
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(f"{self.api_url}/fixtures?bankroll={user_bankroll}", timeout=10.0)
                if res.status_code == 200:
                    fixtures = res.json()
                    message = (
                        f"💼 *PERSONALIZED STAKE ALLOCATION*\n"
                        f"🏦 Your Bankroll: *₦{user_bankroll:,.0f}*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    )
                    count = 0
                    for f in fixtures[:3]:
                        if f.get("prediction") and f["prediction"].get("value_bets"):
                            top_bet = f["prediction"]["value_bets"][0]
                            count += 1
                            message += (
                                f"{count}. ⚽ *{f['home_team']['name']} vs {f['away_team']['name']}*\n"
                                f"   • Market: *{top_bet['market_name']}* ({top_bet['market_odds']:.2f})\n"
                                f"   • Bookmaker: *{top_bet['bookmaker']}*\n"
                                f"   • AI Edge: *+{top_bet['expected_value_pct']:.1f}%* EV\n"
                                f"   • Recommended Stake: *₦{top_bet['recommended_stake_ngn']:,.0f}* ({top_bet['recommended_stake_pct']:.1f}%)\n\n"
                            )
                    message += "🛡️ _Rule: Never exceed recommended stakes to preserve your bankroll._"
                    return message
                else:
                    return "⚠️ Could not retrieve live fixtures."
            except Exception as e:
                return f"⚠️ Error: {e}"

    async def get_challenge_status(self) -> str:
        """Returns the ₦1,000 to ₦50,000 ladder challenge update."""
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(f"{self.api_url}/challenge/ladder", timeout=10.0)
                if res.status_code == 200:
                    data = res.json()
                    msg = (
                        f"🚀 *{data['title']}*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📅 Progress: Day *{data['current_day']}* of *{data['target_days']}*\n"
                        f"💰 Current Bankroll: *₦{data['current_bankroll_ngn']:,.0f}* (Started: ₦{data['starting_amount_ngn']:,.0f})\n"
                        f"🎯 Ultimate Target: *₦{data['target_amount_ngn']:,.0f}*\n\n"
                        f"*RECENT WINS:*\n"
                    )
                    for h in data["history"][-3:]:
                        msg += f"• Day {h['day']}: {h['pick']} ({h['odds']:.2f}) -> *WON* (₦{h['return']:,.0f})\n"
                    msg += "\n🔥 _Next pick drops at 12:00 PM tomorrow!_"
                    return msg
                return "⚠️ Ladder challenge data unavailable."
            except Exception as e:
                return f"⚠️ Error: {e}"

if __name__ == "__main__":
    bot = TelegramBettingBot()
    print("Testing Telegram Bot Banker generation locally...")
    loop = asyncio.get_event_loop()
    msg = loop.run_until_complete(bot.get_daily_banker(15000.0))
    print(msg)
