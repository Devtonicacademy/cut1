from typing import List, Optional

from pydantic import BaseModel


class GoogleSignIn(BaseModel):
    credential: str  # the Google ID token (a JWT) returned by Sign in with Google


class AuthConfig(BaseModel):
    google_client_id: Optional[str] = None  # None until GOOGLE_CLIENT_ID is set on the server


class User(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    role: str  # "admin" or "user"


class SessionInfo(BaseModel):
    user: Optional[User] = None


class SaveFixtureRequest(BaseModel):
    fixture_id: str


class SavedFixture(BaseModel):
    fixture_id: str
    saved_at: str
    league: str
    league_crest: Optional[str] = None
    home_team: str
    away_team: str
    home_crest: Optional[str] = None
    away_crest: Optional[str] = None
    kickoff_utc: Optional[str] = None
    p_home: float
    p_draw: float
    p_away: float
    pick: str  # "1", "X" or "2": the model's favourite
    status: str  # "upcoming", "awaiting_result" or "finished"
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    actual: Optional[str] = None  # "1", "X" or "2" once the result is in
    pick_correct: Optional[bool] = None


class ReportSummary(BaseModel):
    locked: int  # predictions recorded in the ledger
    graded: int  # with a final score
    pending: int
    voided: int
    correct: int
    accuracy_pct: float
    avg_confidence_pct: float  # mean probability the model gave its own pick
    brier: float  # mean multi-class Brier score, lower is better
    baseline_brier: float  # same score for always predicting the overall 1/X/2 frequencies
    log_loss: float


class CalibrationBin(BaseModel):
    label: str
    count: int
    avg_predicted_pct: float  # how often the model said these picks would win
    actual_pct: float  # how often they did


class LeagueAccuracy(BaseModel):
    league: str
    graded: int
    correct: int
    accuracy_pct: float


class MatchComparison(BaseModel):
    id: str
    kickoff_utc: str
    league: str
    home_team: str
    away_team: str
    p_home: float
    p_draw: float
    p_away: float
    pick: str
    status: str  # "pending", "void" or "graded"
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    actual: Optional[str] = None
    correct: Optional[bool] = None


class PredictionReport(BaseModel):
    generated_at: str
    summary: ReportSummary
    calibration: List[CalibrationBin]
    leagues: List[LeagueAccuracy]
    matches: List[MatchComparison]
