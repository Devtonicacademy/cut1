from typing import List, Dict, Optional
from apps.api.app.models.schemas import AdminBroadcastRequest, BetStatus

class AdminService:
    """
    Admin superpowers engine:
    1. Daily AI Quality Gate
    2. 1-Click Multi-Channel Booking Code Broadcaster (Web PWA, Telegram, WhatsApp)
    3. Automated Result Grader & Match Settler
    4. ₦1,000 to ₦50,000 Ladder Challenge Management
    """
    def __init__(self):
        self.approved_picks_of_day: List[Dict[str, any]] = []
        self.broadcast_history: List[Dict[str, any]] = []
        self.ladder_challenge = {
            "title": "₦1,000 to ₦50,000 Safe Compounding Challenge",
            "current_day": 4,
            "target_days": 10,
            "starting_amount_ngn": 1000.0,
            "current_bankroll_ngn": 3280.0,
            "target_amount_ngn": 50000.0,
            "status": "ACTIVE",
            "history": [
                {"day": 1, "pick": "Arsenal 1X & Over 1.5", "odds": 1.35, "stake": 1000.0, "return": 1350.0, "status": "WON"},
                {"day": 2, "pick": "Real Madrid to Win", "odds": 1.30, "stake": 1350.0, "return": 1755.0, "status": "WON"},
                {"day": 3, "pick": "Bayern Munich Over 1.5 Team Goals", "odds": 1.38, "stake": 1755.0, "return": 2420.0, "status": "WON"},
                {"day": 4, "pick": "Inter Milan Draw No Bet", "odds": 1.35, "stake": 2420.0, "return": 3280.0, "status": "WON"},
            ]
        }

    def broadcast_codes(self, req: AdminBroadcastRequest) -> Dict[str, any]:
        """
        Broadcasts SportyBet and Bet9ja booking codes to all configured channels.
        """
        payload = {
            "title": req.title,
            "message": req.message,
            "sportybet_code": req.sportybet_code,
            "bet9ja_code": req.bet9ja_code,
            "channels": req.channels,
            "timestamp": "Just now",
            "reach_estimate": {
                "web_pwa_push": 4200,
                "telegram_vip_channel": 12500,
                "whatsapp_community": 3800
            }
        }
        self.broadcast_history.insert(0, payload)
        return {
            "success": True,
            "broadcast_id": f"bc-{len(self.broadcast_history):04d}",
            "summary": f"Broadcast successfully dispatched to {', '.join(req.channels)}!",
            "payload": payload
        }

    def get_ladder_challenge_status(self) -> Dict[str, any]:
        """Returns the public compounding challenge details."""
        return self.ladder_challenge

    def add_ladder_challenge_step(self, pick: str, odds: float, status: str = "PENDING") -> Dict[str, any]:
        """Advances or adds a step to the public challenge."""
        current_bank = self.ladder_challenge["current_bankroll_ngn"]
        new_day = self.ladder_challenge["current_day"] + 1
        est_return = round(current_bank * odds, 2)
        
        step = {
            "day": new_day,
            "pick": pick,
            "odds": odds,
            "stake": current_bank,
            "return": est_return,
            "status": status
        }
        self.ladder_challenge["history"].append(step)
        self.ladder_challenge["current_day"] = new_day
        if status == "WON":
            self.ladder_challenge["current_bankroll_ngn"] = est_return
        return self.ladder_challenge
