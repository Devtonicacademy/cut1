from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"

class MarketType(str, Enum):
    HOME_WIN = "1"
    DRAW = "X"
    AWAY_WIN = "2"
    DOUBLE_CHANCE_1X = "1X"
    DOUBLE_CHANCE_X2 = "X2"
    DOUBLE_CHANCE_12 = "12"
    OVER_1_5 = "Over 1.5"
    OVER_2_5 = "Over 2.5"
    UNDER_2_5 = "Under 2.5"
    BTTS_YES = "GG (BTTS)"
    BTTS_NO = "NG (No BTTS)"

class Team(BaseModel):
    id: str
    name: str
    short_code: str
    league: str
    home_attack_strength: float = 1.2
    home_defense_weakness: float = 0.9
    away_attack_strength: float = 1.0
    away_defense_weakness: float = 1.1
    rolling_xg_created: float = 1.65
    rolling_xg_conceded: float = 1.10
    form: str = "WWDWL"
    key_injuries: List[str] = []

class BookmakerOdds(BaseModel):
    bookmaker: str # "SportyBet", "Bet9ja", "BetKing"
    home_win: float
    draw: float
    away_win: float
    over_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None
    double_chance_1x: Optional[float] = None
    double_chance_x2: Optional[float] = None
    double_chance_12: Optional[float] = None

class ValueBetItem(BaseModel):
    market: MarketType
    market_name: str
    selection: str
    bookmaker: str
    market_odds: float
    fair_odds: float
    model_probability: float
    implied_probability: float
    expected_value_pct: float
    recommended_stake_pct: float
    recommended_stake_ngn: float
    confidence_tier: str # "High Value (Gold)", "Moderate Value (Silver)", "Speculative"
    reasoning: str

class PredictionDetail(BaseModel):
    home_team: str
    away_team: str
    league: str
    kickoff_time: str
    expected_goals_home: float
    expected_goals_away: float
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    prob_over_1_5: float
    prob_over_2_5: float
    prob_under_2_5: float
    prob_btts: float
    fair_odds_home: float
    fair_odds_draw: float
    fair_odds_away: float
    top_exact_scores: Dict[str, float]
    gemini_tactical_summary: str
    gemini_lineup_risk: str
    value_bets: List[ValueBetItem]
    likely_winner_team: str = ""
    likely_winner_prob: float = 0.0
    likely_winner_confidence: str = "" # "Banker (70%+)", "Strong Favorite", "Moderate Edge", "Evenly Contested"
    statistical_verdict: str = ""
    recommended_safe_pick: str = ""
    recommended_safe_odds: float = 1.20

class Fixture(BaseModel):
    id: str
    home_team: Team
    away_team: Team
    league: str
    kickoff: str
    venue: str
    sportybet_odds: BookmakerOdds
    bet9ja_odds: BookmakerOdds
    status: str = "UPCOMING"
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    prediction: Optional[PredictionDetail] = None

class BankrollRequest(BaseModel):
    bankroll_ngn: float = Field(..., gt=0, description="Total user betting capital in Naira")
    risk_level: RiskLevel = RiskLevel.CONSERVATIVE
    selected_ev_bets: List[ValueBetItem]

class BankrollAllocation(BaseModel):
    bankroll_ngn: float
    risk_level: RiskLevel
    total_staked_ngn: float
    remaining_bankroll_ngn: float
    expected_profit_ngn: float
    allocations: List[ValueBetItem]

class AccumulatorRequest(BaseModel):
    target_odds: float = 5.0 # Target total odds, e.g. 2.0 (banker), 5.0, 10.0
    risk_level: RiskLevel = RiskLevel.BALANCED
    bankroll_ngn: float = 10000.0
    max_legs: int = 5
    target_legs: Optional[int] = None # When user specifies number of games e.g. 5, 10, 15, 20, 25, 30
    strategy: Optional[str] = "safest_winners" # "safest_winners", "balanced_value", "straight_win"
    selected_leagues: Optional[List[str]] = None # Filter by specific leagues

class AccumulatorLeg(BaseModel):
    fixture_id: str
    match_name: str
    market: str
    odds: float
    model_probability: float
    ev_pct: float
    risk_assessment: str # "Safe Anchor", "Moderate Leg", "High Yield"
    safer_alternative: Optional[str] = None # For Cut-1 Doctor
    league: Optional[str] = None
    likely_winner: Optional[str] = None

class AccumulatorResponse(BaseModel):
    ticket_type: str # "2-Odds Daily Banker", "Weekend 5-Odds Ticket", "Top 10 High Confidence Acca", "20-Game Mega Slip"
    total_odds: float
    win_probability: float
    recommended_stake_ngn: float
    potential_payout_ngn: float
    legs: List[AccumulatorLeg]
    cut_1_insured: bool
    cut_1_warning: Optional[str] = None
    sportybet_code: str
    bet9ja_code: str
    whatsapp_share_text: str
    recommended_game_count_note: Optional[str] = None
    leagues_covered: Optional[List[str]] = None

class TrackRecordEntry(BaseModel):
    id: str
    date: str
    match: str
    prediction: str
    odds: float
    stake_ngn: float
    result: BetStatus
    return_ngn: float
    profit_ngn: float
    pnl_running_roi: float
    ai_post_mortem: Optional[str] = None

class TrackRecordStats(BaseModel):
    total_bets: int
    wins: int
    losses: int
    voids: int
    win_rate_pct: float
    total_staked_ngn: float
    total_returned_ngn: float
    net_profit_ngn: float
    roi_pct: float
    current_winning_streak: int
    entries: List[TrackRecordEntry]

class AdminBroadcastRequest(BaseModel):
    title: str
    message: str
    sportybet_code: str
    bet9ja_code: str
    channels: List[str] = ["web", "telegram"] # "web", "telegram", "whatsapp"
