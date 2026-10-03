"""Per-user data: the fixtures a signed-in user has saved."""
import datetime as dt
import json
from typing import Dict, List, Optional

from apps.api.app.data import db
from apps.api.app.models.accounts import SavedFixture
from apps.api.app.models.schemas import Fixture
from apps.api.app.tracking.reports import outcome_of

MAX_SAVED_PER_USER = 200
PICKS = ("1", "X", "2")


def snapshot_of(f: Fixture) -> Dict:
    """What the dashboard needs to show a fixture later, even after it leaves the upcoming list."""
    p = f.prediction
    probs = [p.prob_home_win, p.prob_draw, p.prob_away_win] if p else [0.0, 0.0, 0.0]
    return {
        "league": f.league, "league_crest": f.league_crest,
        "home_team": f.home_team.name, "away_team": f.away_team.name,
        "home_crest": f.home_team.crest, "away_crest": f.away_team.crest,
        "kickoff_utc": f.kickoff_timestamp,
        "p_home": probs[0], "p_draw": probs[1], "p_away": probs[2],
        "pick": PICKS[max(range(3), key=lambda i: probs[i])],
    }


class SavedLimitReached(Exception):
    pass


def save(user_id: int, fixture: Fixture) -> None:
    with db.connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM saved_fixtures WHERE user_id = ? AND fixture_id = ?", (user_id, fixture.id)).fetchone()
        count = conn.execute("SELECT COUNT(*) FROM saved_fixtures WHERE user_id = ?", (user_id,)).fetchone()[0]
        if not exists and count >= MAX_SAVED_PER_USER:
            raise SavedLimitReached()
        conn.execute(
            """
            INSERT INTO saved_fixtures (user_id, fixture_id, saved_at, snapshot) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, fixture_id) DO UPDATE SET snapshot = excluded.snapshot
            """,  # saving again keeps the original saved_at
            (user_id, fixture.id, dt.datetime.now(dt.timezone.utc).isoformat(), json.dumps(snapshot_of(fixture))),
        )


def unsave(user_id: int, fixture_id: str) -> bool:
    with db.connect() as conn:
        return conn.execute(
            "DELETE FROM saved_fixtures WHERE user_id = ? AND fixture_id = ?", (user_id, fixture_id)).rowcount > 0


def list_saved(user_id: int, live: Dict[str, Fixture], now: Optional[dt.datetime] = None) -> List[SavedFixture]:
    """
    The user's saved fixtures, soonest first. A fixture that is still upcoming shows its current numbers;
    one that has been played shows the final score and whether the model's pick was right.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    with db.connect() as conn:
        saved = conn.execute(
            "SELECT fixture_id, saved_at, snapshot FROM saved_fixtures WHERE user_id = ?", (user_id,)).fetchall()
        results = {
            r["fixture_id"]: r for r in conn.execute(
                "SELECT fixture_id, fthg, ftag, pick, p_home, p_draw, p_away FROM predictions WHERE fthg IS NOT NULL AND fixture_id IN (%s)"
                % ",".join("?" for _ in saved), [s["fixture_id"] for s in saved]).fetchall()
        } if saved else {}
    items: List[SavedFixture] = []
    for row in saved:
        snap = json.loads(row["snapshot"])
        fixture = live.get(row["fixture_id"])
        if fixture and fixture.prediction:
            snap = snapshot_of(fixture)
        result = results.get(row["fixture_id"])
        extra: Dict = {}
        if result:
            actual = outcome_of(result["fthg"], result["ftag"])
            status = "finished"
            # A played match shows the prediction that was locked before kickoff, not today's numbers.
            snap.update(p_home=result["p_home"], p_draw=result["p_draw"], p_away=result["p_away"], pick=result["pick"])
            extra = {"home_goals": result["fthg"], "away_goals": result["ftag"], "actual": actual,
                     "pick_correct": actual == result["pick"]}
        elif fixture:
            status = "upcoming"
        else:
            kickoff = snap.get("kickoff_utc")
            passed = bool(kickoff) and dt.datetime.fromisoformat(kickoff) <= now
            status = "awaiting_result" if passed else "upcoming"
        items.append(SavedFixture(fixture_id=row["fixture_id"], saved_at=row["saved_at"], status=status, **snap, **extra))
    return sorted(items, key=lambda i: (i.kickoff_utc or "9999", i.fixture_id))
