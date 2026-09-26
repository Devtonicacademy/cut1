import datetime as dt

import pytest
from starlette.testclient import TestClient

from apps.api.app.data import db
from apps.api.app.main import app
from apps.api.app.models.schemas import BetStatus, Fixture
from apps.api.app.tracking import ledger

ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}  # matches ADMIN_TOKEN set in conftest.py

client = TestClient(app)


@pytest.fixture
def fixtures():
    return [Fixture.model_validate(f) for f in client.get("/api/v1/fixtures").json()]


@pytest.fixture
def ledger_db(tmp_path):
    return tmp_path / "ledger.db"


def _kickoff(f: Fixture) -> dt.datetime:
    return dt.datetime.fromisoformat(f.kickoff_timestamp).astimezone(dt.timezone.utc)


def test_locks_only_inside_window_and_only_once(fixtures, ledger_db):
    now = dt.datetime.now(dt.timezone.utc)
    in_window = [f for f in fixtures if _kickoff(f) <= now + dt.timedelta(hours=ledger.LOCK_WINDOW_HOURS)]
    assert 0 < len(in_window) < len(fixtures)
    with db.connect(ledger_db) as conn:
        assert ledger.lock_predictions(conn, fixtures, now) == len(in_window)
        assert ledger.lock_predictions(conn, fixtures, now) == 0  # never re-locked or overwritten
        row = conn.execute("SELECT * FROM predictions ORDER BY seq LIMIT 1").fetchone()
        assert row["pick"] in ("1", "X", "2") and row["odds_h"] is not None
        assert row["pick_prob"] == max(row["p_home"], row["p_draw"], row["p_away"])
        assert ledger.verify_chain(conn)["valid"] is True


def test_editing_or_deleting_a_prediction_breaks_the_chain(fixtures, ledger_db):
    now = dt.datetime.now(dt.timezone.utc)
    with db.connect(ledger_db) as conn:
        ledger.lock_predictions(conn, fixtures, now)
        conn.execute("UPDATE predictions SET p_home = 0.99 WHERE seq = 2")
        assert ledger.verify_chain(conn) == {"valid": False, "entries": ledger.verify_chain(conn)["entries"],
                                             "first_broken_seq": 2}
    with db.connect(ledger_db) as conn:
        conn.execute("DELETE FROM predictions")
        ledger.lock_predictions(conn, fixtures, now)
        first = conn.execute("SELECT MIN(seq) FROM predictions").fetchone()[0]
        conn.execute("DELETE FROM predictions WHERE seq = ?", (first + 1,))
        assert ledger.verify_chain(conn)["valid"] is False


def test_grading_results_and_voids(fixtures, ledger_db):
    now = dt.datetime.now(dt.timezone.utc)
    with db.connect(ledger_db) as conn:
        ledger.lock_predictions(conn, fixtures, now)
        locked = conn.execute("SELECT * FROM predictions ORDER BY seq").fetchall()
        won, lost = locked[0], locked[1]
        score = {"1": (2, 0), "X": (1, 1), "2": (0, 2)}
        wrong = {"1": (0, 1), "X": (2, 0), "2": (1, 0)}
        for r, (hg, ag) in ((won, score[won["pick"]]), (lost, wrong[lost["pick"]])):
            db.upsert_matches(conn, [{"div": r["div"], "season": "2627", "match_date": r["match_date"],
                                      "home_team": r["home_team"], "away_team": r["away_team"],
                                      "fthg": hg, "ftag": ag}])

        kickoff = dt.datetime.fromisoformat(won["kickoff_utc"])
        assert ledger.grade(conn, kickoff + dt.timedelta(hours=3)) == {"graded": 2, "voided": 0}
        result = ledger.grade(conn, kickoff + dt.timedelta(days=9))
        assert result == {"graded": 0, "voided": len(locked) - 2}

        stats = ledger.stats(conn)
        assert (stats.wins, stats.losses, stats.voids) == (1, 1, len(locked) - 2)
        assert stats.win_rate_pct == 50.0
        won_odds = {"1": won["odds_h"], "X": won["odds_d"], "2": won["odds_a"]}[won["pick"]]
        assert stats.total_staked_ngn == 2000.0
        assert stats.total_returned_ngn == pytest.approx(1000.0 * won_odds, abs=0.01)
        assert {e.result for e in stats.entries} == {BetStatus.WON, BetStatus.LOST, BetStatus.VOID}
        assert ledger.verify_chain(conn)["valid"] is True  # grading never touches hashed fields


def test_pipeline_cycle_locks_predictions_and_track_record_is_verifiable():
    cycle = client.post("/api/v1/jobs/run", headers=ADMIN_HEADERS).json()
    assert cycle["refresh"] == {"skipped": "offline mode"}
    assert cycle["locked"] > 0
    record = client.get("/api/v1/track-record").json()
    assert record["total_bets"] >= cycle["locked"]
    assert all(e["result"] == "pending" for e in record["entries"])
    assert client.get("/api/v1/track-record/verify").json()["valid"] is True
    assert client.post("/api/v1/jobs/run", headers=ADMIN_HEADERS).json()["locked"] == 0
