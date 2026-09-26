"""
Automation: refresh data -> predict -> lock predictions -> grade results, plus a weekly retrain.

Runs inside the API every few hours (see main.py), or once from the command line:
    python -m apps.api.app.jobs            # one cycle
    python -m apps.api.app.jobs --retrain  # one cycle, then retrain the model
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from apps.api.app.data import db, ingest
from apps.api.app.ml import predictor as ml_predictor
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.tracking import ledger

CYCLE_HOURS = float(os.getenv("LIVELYBORG_CYCLE_HOURS", "3"))
RETRAIN_AFTER_DAYS = 7
BOOTSTRAP_SEASONS = 10
BACKUPS_KEPT = 14
_lock = asyncio.Lock()


def bootstrap() -> Dict:
    """First start on an empty server: load history, then train, before any prediction is locked."""
    result: Dict = {}
    if ingest.is_offline():
        return result
    with db.connect() as conn:
        empty = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0
    if empty:
        result["history"] = ingest.ingest_history(seasons=BOOTSTRAP_SEASONS)
    if not ml_predictor.MODEL_PATH.exists():
        retrain()
        result["trained"] = True
    return result


def backup(now: dt.datetime) -> Optional[Path]:
    """Daily copy of the database (safe while in use); keeps the newest BACKUPS_KEPT files."""
    backup_dir = db.get_db_path().parent / "backups"
    target = backup_dir / f"livelyborg-{now:%Y%m%d}.db"
    if target.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    with db.connect() as conn:
        dest = sqlite3.connect(target)
        try:
            conn.backup(dest)
        finally:
            dest.close()
    for old in sorted(backup_dir.glob("livelyborg-*.db"))[:-BACKUPS_KEPT]:
        old.unlink()
    return target


async def run_cycle(fixture_service: FixtureService) -> Dict:
    """One pass of the pipeline. Safe to call repeatedly; each step is idempotent."""
    async with _lock:
        now = dt.datetime.now(dt.timezone.utc)
        try:
            refresh = await asyncio.to_thread(ingest.refresh)
        except Exception as e:  # offline or source down: keep going with the data we have
            refresh = {"error": str(e)}
        fixture_service.refresh_fixtures()
        fixtures = await fixture_service.get_all_fixtures_with_predictions()
        with db.connect() as conn:
            locked = ledger.lock_predictions(conn, fixtures, now)
            graded = ledger.grade(conn, now)
            db.set_meta(conn, "last_cycle", now.isoformat())
        explained = await fixture_service.gemini.explain_missing(fixtures)
        if explained.get("written"):
            fixture_service.refresh_explanations()
        return {"refresh": refresh, "locked": locked, **graded, "explanations": explained}


def model_age_days() -> float:
    if not ml_predictor.REPORT_PATH.exists():
        return float("inf")
    trained_at = json.loads(ml_predictor.REPORT_PATH.read_text()).get("trained_at")
    if not trained_at:
        return float("inf")
    return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(trained_at)).total_seconds() / 86400


def retrain() -> None:
    from apps.api.app.ml import train  # heavy imports only when actually retraining
    train.main()


async def scheduler_loop(fixture_service: FixtureService) -> None:
    try:
        setup = await asyncio.to_thread(bootstrap)
        if setup:
            print(f"[scheduler] first-start setup: {setup}")
            fixture_service.refresh_fixtures()
    except Exception as e:
        print(f"[scheduler] first-start setup failed: {e}")
    while True:
        try:
            print(f"[scheduler] cycle: {await run_cycle(fixture_service)}")
            saved = await asyncio.to_thread(backup, dt.datetime.now(dt.timezone.utc))
            if saved:
                print(f"[scheduler] backup saved: {saved}")
            if not ingest.is_offline() and model_age_days() > RETRAIN_AFTER_DAYS:
                print("[scheduler] model older than a week, retraining...")
                await asyncio.to_thread(retrain)
                fixture_service.refresh_fixtures()  # picks up the new model on the next request
        except Exception as e:
            print(f"[scheduler] cycle failed: {e}")
        await asyncio.sleep(CYCLE_HOURS * 3600)


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(db.REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run one LivelyBorg data/prediction cycle.")
    parser.add_argument("--retrain", action="store_true", help="Also retrain the model after the cycle")
    args = parser.parse_args()
    print(asyncio.run(run_cycle(FixtureService())))
    if args.retrain:
        retrain()
    with db.connect() as conn:
        print(ledger.verify_chain(conn))


if __name__ == "__main__":
    main()
