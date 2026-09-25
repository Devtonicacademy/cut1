import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from apps.api.app.models.schemas import (
    Fixture, BankrollRequest, BankrollAllocation,
    AccumulatorRequest, AccumulatorResponse,
    TrackRecordStats, AdminBroadcastRequest, RiskLevel, BetStatus
)
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.services.kelly_engine import KellyEngine
from apps.api.app.services.accas_optimizer import AccasOptimizer
from apps.api.app.services.tracker_service import TrackerService
from apps.api.app.services.admin_service import AdminService

app = FastAPI(
    title="LivelyBorg AI Sports Intelligence API",
    description="Next-generation football predictive modeling, +EV discovery, and smart bankroll staking for Nigeria",
    version="1.0.0"
)

# Enable CORS for Next.js PWA and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fixture_service = FixtureService()
tracker_service = TrackerService()
admin_service = AdminService()

@app.get("/api/v1/health")
async def healthcheck():
    return {
        "status": "healthy",
        "market": "Lagos, Nigeria",
        "supported_bookmakers": ["SportyBet", "Bet9ja", "BetKing"],
        "models_active": ["Dixon-Coles Bivariate Poisson", "Rolling xG Ensemble", "Google Gemini Contextual"]
    }

@app.get("/api/v1/fixtures", response_model=List[Fixture])
async def get_fixtures(bankroll: float = Query(10000.0, description="User bankroll in Naira")):
    """Retrieves all upcoming fixtures enriched with AI probabilities, fair odds, and +EV plays."""
    return await fixture_service.get_all_fixtures_with_predictions(bankroll)

@app.get("/api/v1/fixtures/{fixture_id}", response_model=Fixture)
async def get_fixture_detail(fixture_id: str, bankroll: float = Query(10000.0)):
    """Retrieves in-depth tactical analysis and predictive breakdown for a single fixture."""
    fixture = await fixture_service.get_fixture_by_id(fixture_id, bankroll)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return fixture

@app.post("/api/v1/bankroll/allocate", response_model=BankrollAllocation)
async def allocate_bankroll(req: BankrollRequest):
    """Calculates optimal fractional Kelly Criterion stakes (₦) for selected value plays."""
    return KellyEngine.allocate_bankroll(
        bankroll_ngn=req.bankroll_ngn,
        risk_level=req.risk_level,
        selected_bets=req.selected_ev_bets
    )

@app.post("/api/v1/accumulators/build", response_model=AccumulatorResponse)
async def build_smart_accumulator(req: AccumulatorRequest):
    """
    Builds an optimized accumulator (Safe 2-Odds, 10-Game Acca, 15-Game, 20-Game, 30-Game Mega Slip)
    and applies the Cut-1/Cut-2 Doctor insurance check.
    """
    fixtures = await fixture_service.get_all_fixtures_with_predictions(req.bankroll_ngn)
    return AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures,
        target_odds=req.target_odds,
        risk_level=req.risk_level,
        bankroll_ngn=req.bankroll_ngn,
        max_legs=req.max_legs,
        target_legs=req.target_legs,
        strategy=req.strategy or "safest_winners",
        selected_leagues=req.selected_leagues
    )

@app.get("/api/v1/track-record", response_model=TrackRecordStats)
async def get_public_track_record():
    """Returns verified public track record with win rates, ROI %, and loss post-mortems."""
    return tracker_service.get_public_stats()

@app.get("/api/v1/challenge/ladder")
async def get_ladder_challenge():
    """Returns the live status of the public ₦1,000 to ₦50,000 compounding ladder challenge."""
    return admin_service.get_ladder_challenge_status()

@app.post("/api/v1/admin/broadcast")
async def broadcast_booking_codes(req: AdminBroadcastRequest):
    """Admin superpower: 1-click multi-channel broadcaster to Web PWA and Telegram."""
    return admin_service.broadcast_codes(req)

@app.post("/api/v1/admin/settle")
async def settle_match(
    match: str,
    prediction: str,
    odds: float,
    stake_ngn: float,
    result: BetStatus,
    post_mortem: Optional[str] = None
):
    """Admin superpower: Settle bet results and update audited track record."""
    entry = tracker_service.record_bet_result(
        match=match,
        prediction=prediction,
        odds=odds,
        stake_ngn=stake_ngn,
        result=result,
        post_mortem=post_mortem
    )
    return {"success": True, "entry": entry}
