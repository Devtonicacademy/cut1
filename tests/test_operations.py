import datetime as dt
import hashlib
import json

from starlette.testclient import TestClient

from apps.api.app import jobs
from apps.api.app.data import db
from apps.api.app.main import app

client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}  # matches ADMIN_TOKEN set in conftest.py


def test_exported_ledger_can_be_verified_without_our_code():
    client.post("/api/v1/jobs/run", headers=ADMIN_HEADERS)
    export = client.get("/api/v1/track-record/export").json()
    assert export["entries"]
    prev = export["genesis_hash"]
    for entry in export["entries"]:
        payload = json.dumps({k: entry[k] for k in export["hashed_fields"]}, sort_keys=True, separators=(",", ":"))
        assert entry["prev_hash"] == prev
        assert hashlib.sha256(payload.encode()).hexdigest() == entry["hash"]
        prev = entry["hash"]


def test_daily_backup_is_created_once_and_pruned(monkeypatch, tmp_path):
    monkeypatch.setenv("LIVELYBORG_DB_PATH", str(tmp_path / "live.db"))
    with db.connect() as conn:
        db.set_meta(conn, "marker", "kept")
    day = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    for i in range(jobs.BACKUPS_KEPT + 3):
        assert jobs.backup(day + dt.timedelta(days=i)) is not None
    assert jobs.backup(day + dt.timedelta(days=jobs.BACKUPS_KEPT + 2)) is None  # already saved that day

    backups = sorted((tmp_path / "backups").glob("livelyborg-*.db"))
    assert len(backups) == jobs.BACKUPS_KEPT
    assert backups[0].name == "livelyborg-20260904.db"  # the oldest three were pruned
    with db.connect(backups[-1]) as restored:
        assert db.get_meta(restored, "marker") == "kept"


def test_bootstrap_does_nothing_offline():
    assert jobs.bootstrap() == {}
