import os
from pathlib import Path
from dotenv import load_dotenv
# Always the project-root .env (a bare load_dotenv() searches upward from this file and could pick up another one)
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import asyncio
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from apps.api.app.data import db, ingest
from apps.api.app.models.schemas import (
    Fixture, BankrollRequest, BankrollAllocation,
    AccumulatorRequest, AccumulatorResponse,
    TrackRecordStats
)
from apps.api.app import jobs
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.services.kelly_engine import KellyEngine
from apps.api.app.services.accas_optimizer import AccasOptimizer
from apps.api.app.services.tracker_service import TrackerService

async def _refresh_data() -> dict:
    """Pulls the latest results and fixtures without blocking the event loop."""
    result = await asyncio.to_thread(ingest.refresh)
    fixture_service.refresh_fixtures()
    return result


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Refresh -> predict -> lock -> grade every few hours, retraining weekly (apps/api/app/jobs.py)
    task = None
    if os.getenv("LIVELYBORG_AUTO_REFRESH", "1") == "1":
        task = asyncio.create_task(jobs.scheduler_loop(fixture_service))
    yield
    if task:
        task.cancel()


app = FastAPI(
    title="LivelyBorg AI Sports Intelligence API",
    description="Football match predictions trained on real results, with a public, tamper-evident track record",
    version="1.0.0",
    lifespan=lifespan,
)

# Only the web app's own origins may call the API from a browser (comma-separated in ALLOWED_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

fixture_service = FixtureService()
tracker_service = TrackerService()


def require_admin(x_admin_token: str = Header(default="")) -> None:
    """Admin endpoints need the X-Admin-Token header to match ADMIN_TOKEN; they are off when it is unset."""
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=403, detail="Admin endpoints are disabled: set ADMIN_TOKEN on the server")
    if not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token")


@app.get("/api/v1/health")
async def healthcheck():
    predictor = fixture_service.predictor
    return {
        "status": "healthy",
        "model_loaded": predictor.available,
        "model_trained_at": predictor.report.get("trained_at"),
    }

@app.get("/api/v1/fixtures", response_model=List[Fixture])
async def get_fixtures(
    bankroll: float = Query(10000.0, description="User bankroll in Naira"),
    upcoming_only: bool = Query(True, description="Strictly filter for upcoming matches")
):
    """Retrieves all upcoming fixtures enriched with AI probabilities, fair odds, and +EV plays."""
    fixtures = await fixture_service.get_all_fixtures_with_predictions(bankroll)
    if upcoming_only:
        fixtures = [f for f in fixtures if getattr(f, "is_upcoming", True)]
    return fixtures

@app.post("/api/v1/fixtures/refresh", response_model=List[Fixture], dependencies=[Depends(require_admin)])
async def refresh_fixtures(bankroll: float = Query(10000.0)):
    """Pulls the latest results and fixtures from the data source, then rebuilds predictions."""
    try:
        await _refresh_data()
    except Exception as e:
        print(f"Data refresh failed, serving cached data: {e}")
    fixtures = await fixture_service.get_all_fixtures_with_predictions(bankroll)
    return [f for f in fixtures if f.is_upcoming]

@app.get("/api/v1/data/status")
async def get_data_status():
    """Shows how much real data is loaded and when it was last refreshed."""
    with db.connect() as conn:
        status = db.data_status(conn)
    status["sources"] = ["football-data.co.uk", "football-data.org"]
    return status

@app.get("/api/v1/model/report")
async def get_model_report():
    """Backtest of the prediction model against bookmakers on seasons it never trained on."""
    predictor = fixture_service.predictor
    predictor.reload_if_changed()
    if not predictor.available:
        raise HTTPException(status_code=404, detail="No trained model. Run: python -m apps.api.app.ml.train")
    return predictor.report

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
        strategy=req.strategy or "safest",
        selected_leagues=req.selected_leagues
    )

@app.get("/api/v1/track-record", response_model=TrackRecordStats)
async def get_public_track_record():
    """Every prediction locked before kickoff, graded automatically from official results."""
    return tracker_service.get_public_stats()

@app.get("/api/v1/track-record/verify")
async def verify_track_record():
    """Recomputes the hash chain: proves no past prediction was edited, inserted or deleted."""
    return tracker_service.verify()

@app.get("/api/v1/track-record/export")
async def export_track_record():
    """The complete prediction ledger, so anyone can re-check every hash themselves."""
    return tracker_service.export()

@app.post("/api/v1/jobs/run", dependencies=[Depends(require_admin)])
async def run_pipeline_now():
    """Runs one refresh -> predict -> lock -> grade cycle immediately."""
    return await jobs.run_cycle(fixture_service)
