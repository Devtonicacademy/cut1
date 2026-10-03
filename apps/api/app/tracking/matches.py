"""
Past and ongoing matches for the public track record page.

Everything here comes from the prediction ledger, so each match was predicted and locked before kickoff.
Live scores (data/ingest.py: ingest_live_scores) are shown for matches in play but never change the ledger:
a match is only graded from the official results file.
"""
import datetime as dt
import sqlite3
from typing import Dict, List, Optional

from apps.api.app.data import db
from apps.api.app.models.records import MatchesResponse, MatchesSummary, OngoingMatch, PastMatch
from apps.api.app.tracking.reports import _league_name, outcome_of

ONGOING_HOURS = 3  # in play from kickoff until about this long after
LIVE_FRESH_MINUTES = 10  # an older live row is treated as "no live score"
ACTIVE_STATUSES = ("IN_PLAY", "PAUSED")


def _parse(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts)


def build(conn: sqlite3.Connection, now: dt.datetime, past_limit: int = 60) -> MatchesResponse:
    live = db.load_live_scores(conn)
    crests = db.load_crests(conn)
    team_crest = crests.get("team", {})
    league_crest = crests.get("league", {})

    def side(r: sqlite3.Row) -> Dict:
        return dict(
            league=_league_name(r["div"]), league_crest=league_crest.get(r["div"]),
            home_team=r["home_team"], away_team=r["away_team"],
            home_crest=team_crest.get(r["home_team"]), away_crest=team_crest.get(r["away_team"]),
            kickoff_utc=r["kickoff_utc"], p_home=r["p_home"], p_draw=r["p_draw"], p_away=r["p_away"], pick=r["pick"],
        )

    ongoing: List[OngoingMatch] = []
    past: List[PastMatch] = []
    graded = correct = 0
    for r in conn.execute("SELECT * FROM predictions ORDER BY kickoff_utc DESC, seq DESC"):
        kickoff = _parse(r["kickoff_utc"])
        if r["graded_at"] is not None:
            if r["fthg"] is None:  # voided: postponed or abandoned
                continue
            actual = outcome_of(r["fthg"], r["ftag"])
            graded += 1
            correct += actual == r["pick"]
            past.append(PastMatch(
                id=r["fixture_id"], status="graded", home_goals=r["fthg"], away_goals=r["ftag"], actual=actual,
                correct=actual == r["pick"], **side(r)))
            continue
        if kickoff > now:
            continue  # not started: it belongs in the fixtures list

        row = live.get(r["fixture_id"])
        fresh = bool(row) and now - _parse(row["updated_at"]) <= dt.timedelta(minutes=LIVE_FRESH_MINUTES)
        finished = bool(row) and row["status"] == "FINISHED"
        if finished or now - kickoff >= dt.timedelta(hours=ONGOING_HOURS):
            has_score = finished and row["home_goals"] is not None and row["away_goals"] is not None
            past.append(PastMatch(
                id=r["fixture_id"], status="awaiting",
                home_goals=row["home_goals"] if has_score else None, away_goals=row["away_goals"] if has_score else None,
                provisional=has_score, **side(r)))
            continue
        active = fresh and row["status"] in ACTIVE_STATUSES
        ongoing.append(OngoingMatch(
            id=r["fixture_id"], minutes_since_kickoff=int((now - kickoff).total_seconds() // 60),
            live_status=row["status"] if active else None,
            home_goals=row["home_goals"] if active else None, away_goals=row["away_goals"] if active else None,
            minute=row["minute"] if active else None, score_updated_at=row["updated_at"] if active else None,
            **side(r)))

    ongoing.sort(key=lambda m: m.kickoff_utc)  # earliest kickoff first
    return MatchesResponse(
        generated_at=now.isoformat(),
        summary=MatchesSummary(graded=graded, correct=correct, accuracy_pct=round(correct / graded * 100, 1) if graded else 0.0),
        ongoing=ongoing,
        past=past[:past_limit],
    )
