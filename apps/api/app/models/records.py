from typing import List, Optional

from pydantic import BaseModel


class MatchSide(BaseModel):
    league: str
    league_crest: Optional[str] = None
    home_team: str
    away_team: str
    home_crest: Optional[str] = None
    away_crest: Optional[str] = None
    kickoff_utc: str
    # The prediction exactly as it was locked before kickoff
    p_home: float
    p_draw: float
    p_away: float
    pick: str  # "1", "X" or "2"


class OngoingMatch(MatchSide):
    id: str
    minutes_since_kickoff: int
    # From the live feed; None when it has nothing fresh for this match
    live_status: Optional[str] = None  # "IN_PLAY" or "PAUSED"
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    minute: Optional[int] = None
    score_updated_at: Optional[str] = None


class PastMatch(MatchSide):
    id: str
    status: str  # "graded": official result in; "awaiting": played, official result not in yet
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    actual: Optional[str] = None  # "1", "X" or "2"
    correct: Optional[bool] = None
    provisional: bool = False  # the score is from the live feed and not yet confirmed


class MatchesSummary(BaseModel):
    graded: int
    correct: int
    accuracy_pct: float


class MatchesResponse(BaseModel):
    generated_at: str
    summary: MatchesSummary
    ongoing: List[OngoingMatch]
    past: List[PastMatch]
