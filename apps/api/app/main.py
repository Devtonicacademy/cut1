import os
from pathlib import Path
from dotenv import load_dotenv
# Always the project-root .env (a bare load_dotenv() searches upward from this file and could pick up another one)
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import asyncio
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from apps.api.app.data import db, ingest
from apps.api.app.data.leagues import LEAGUES
from apps.api.app.models.schemas import (
    Fixture, BankrollRequest, BankrollAllocation,
    AccumulatorRequest, AccumulatorResponse,
    TrackRecordStats
)
from apps.api.app import accounts, auth, jobs
from apps.api.app.models.accounts import (
    AuthConfig, GoogleSignIn, PredictionReport, SaveFixtureRequest, SavedFixture, SessionInfo,
)
from apps.api.app.tracking import reports
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
    allow_credentials=True,  # origins are an explicit list, never "*"
    allow_methods=["GET", "POST", "DELETE"],
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
    fixtures = [f for f in fixtures if f.div in LEAGUES]  # cross-league predictions are not backtested
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


# ---- Accounts: Sign in with Google, saved fixtures, admin reports ----

@app.get("/api/v1/auth/config", response_model=AuthConfig)
def auth_config():
    """Lets the site fetch the (public) Google client id at runtime instead of baking it into the build."""
    return AuthConfig(google_client_id=auth.google_client_id())


@app.post("/api/v1/auth/google", response_model=SessionInfo)
def sign_in_with_google(body: GoogleSignIn, request: Request, response: Response):
    try:
        claims = auth.verify_google_credential(body.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:  # bad signature, expired, wrong audience, certificates unreachable...
        raise HTTPException(status_code=401, detail="Could not verify the Google sign-in")
    token = auth.create_session(claims)
    response.set_cookie(
        auth.COOKIE_NAME, token, max_age=auth.SESSION_DAYS * 86400, httponly=True,
        samesite="lax", secure=auth.cookie_secure(request), path="/",
    )
    return SessionInfo(user=auth.to_user(auth.user_for_token(token)))


@app.get("/api/v1/auth/me", response_model=SessionInfo)
def whoami(user=Depends(auth.optional_user)):
    return SessionInfo(user=auth.to_user(user) if user else None)


@app.post("/api/v1/auth/logout", response_model=SessionInfo)
def sign_out(request: Request, response: Response):
    token = request.cookies.get(auth.COOKIE_NAME)
    if token:
        auth.delete_session(token)
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return SessionInfo(user=None)


@app.get("/api/v1/me/saved", response_model=List[SavedFixture])
async def my_saved_fixtures(user=Depends(auth.require_user)):
    live = {f.id: f for f in await fixture_service.get_all_fixtures_with_predictions()}
    return accounts.list_saved(user["id"], live)


@app.post("/api/v1/me/saved", response_model=List[SavedFixture])
async def save_fixture(body: SaveFixtureRequest, user=Depends(auth.require_user)):
    fixture = await fixture_service.get_fixture_by_id(body.fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="That fixture is no longer available")
    try:
        accounts.save(user["id"], fixture)
    except accounts.SavedLimitReached:
        raise HTTPException(status_code=409, detail=f"You can save up to {accounts.MAX_SAVED_PER_USER} fixtures")
    live = {f.id: f for f in await fixture_service.get_all_fixtures_with_predictions()}
    return accounts.list_saved(user["id"], live)


@app.delete("/api/v1/me/saved/{fixture_id}", response_model=List[SavedFixture])
async def unsave_fixture(fixture_id: str, user=Depends(auth.require_user)):
    accounts.unsave(user["id"], fixture_id)
    live = {f.id: f for f in await fixture_service.get_all_fixtures_with_predictions()}
    return accounts.list_saved(user["id"], live)


@app.get("/api/v1/admin/reports/predictions", response_model=PredictionReport)
def prediction_report(limit: int = Query(300, ge=1, le=2000), _admin=Depends(auth.require_admin_role)):
    """Locked predictions against the actual results. Admin role only (see auth.ADMIN_EMAILS)."""
    with db.connect() as conn:
        return reports.build_report(conn, limit)
