"""
Admin report: what the model predicted for each match against what actually happened.
Reads the tamper-evident ledger (predictions table), so it can only describe predictions that
were locked before kickoff.
"""
import datetime as dt
import math
import sqlite3
from typing import Dict, List

from apps.api.app.data.leagues import EUROPEAN_COMPETITIONS, LEAGUES, NATIONAL_COMPETITIONS
from apps.api.app.models.accounts import (
    CalibrationBin, LeagueAccuracy, MatchComparison, PredictionReport, ReportSummary,
)

# (lower bound inclusive, upper bound exclusive) of the probability the model gave its pick
CALIBRATION_BINS = [(0.0, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70), (0.70, 1.01)]
OUTCOMES = ("1", "X", "2")


def _league_name(div: str) -> str:
    if div in LEAGUES:
        return LEAGUES[div].name
    if div in EUROPEAN_COMPETITIONS:
        return EUROPEAN_COMPETITIONS[div].name
    if div in NATIONAL_COMPETITIONS:
        return NATIONAL_COMPETITIONS[div].name
    return div


def outcome_of(home_goals: int, away_goals: int) -> str:
    return "1" if home_goals > away_goals else ("X" if home_goals == away_goals else "2")


def build_report(conn: sqlite3.Connection, limit: int = 300) -> PredictionReport:
    rows = [dict(r) for r in conn.execute("SELECT * FROM predictions ORDER BY kickoff_utc DESC, seq DESC")]
    graded = [r for r in rows if r["graded_at"] is not None and r["fthg"] is not None]
    pending = [r for r in rows if r["graded_at"] is None]
    voided = [r for r in rows if r["graded_at"] is not None and r["fthg"] is None]
    for r in graded:
        r["actual"] = outcome_of(r["fthg"], r["ftag"])
    correct = sum(1 for r in graded if r["actual"] == r["pick"])

    brier = baseline = log_loss = 0.0
    if graded:
        freq = {o: sum(1 for r in graded if r["actual"] == o) / len(graded) for o in OUTCOMES}
        for r in graded:
            probs = {"1": r["p_home"], "X": r["p_draw"], "2": r["p_away"]}
            brier += sum((probs[o] - (o == r["actual"])) ** 2 for o in OUTCOMES)
            baseline += sum((freq[o] - (o == r["actual"])) ** 2 for o in OUTCOMES)
            log_loss -= math.log(max(probs[r["actual"]], 1e-9))
        brier, baseline, log_loss = brier / len(graded), baseline / len(graded), log_loss / len(graded)

    summary = ReportSummary(
        locked=len(rows), graded=len(graded), pending=len(pending), voided=len(voided), correct=correct,
        accuracy_pct=round(correct / len(graded) * 100, 1) if graded else 0.0,
        avg_confidence_pct=round(sum(r["pick_prob"] for r in graded) / len(graded) * 100, 1) if graded else 0.0,
        brier=round(brier, 4), baseline_brier=round(baseline, 4), log_loss=round(log_loss, 4),
    )

    calibration: List[CalibrationBin] = []
    for lo, hi in CALIBRATION_BINS:
        bucket = [r for r in graded if lo <= r["pick_prob"] < hi]
        label = f"{round(lo * 100)}-{round(min(hi, 1.0) * 100)}%" if hi <= 1.0 else f"{round(lo * 100)}%+"
        calibration.append(CalibrationBin(
            label=label, count=len(bucket),
            avg_predicted_pct=round(sum(r["pick_prob"] for r in bucket) / len(bucket) * 100, 1) if bucket else 0.0,
            actual_pct=round(sum(1 for r in bucket if r["actual"] == r["pick"]) / len(bucket) * 100, 1) if bucket else 0.0,
        ))

    by_league: Dict[str, List[dict]] = {}
    for r in graded:
        by_league.setdefault(_league_name(r["div"]), []).append(r)
    leagues = sorted(
        (LeagueAccuracy(league=name, graded=len(rs), correct=sum(1 for r in rs if r["actual"] == r["pick"]),
                        accuracy_pct=round(sum(1 for r in rs if r["actual"] == r["pick"]) / len(rs) * 100, 1))
         for name, rs in by_league.items()),
        key=lambda l: (-l.graded, l.league),
    )

    matches: List[MatchComparison] = []
    for r in rows[:limit]:
        is_graded = r["graded_at"] is not None and r["fthg"] is not None
        status = "graded" if is_graded else ("pending" if r["graded_at"] is None else "void")
        actual = outcome_of(r["fthg"], r["ftag"]) if is_graded else None
        matches.append(MatchComparison(
            id=r["fixture_id"], kickoff_utc=r["kickoff_utc"], league=_league_name(r["div"]),
            home_team=r["home_team"], away_team=r["away_team"],
            p_home=r["p_home"], p_draw=r["p_draw"], p_away=r["p_away"], pick=r["pick"], status=status,
            home_goals=r["fthg"] if is_graded else None, away_goals=r["ftag"] if is_graded else None,
            actual=actual, correct=(actual == r["pick"]) if is_graded else None,
        ))

    return PredictionReport(
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        summary=summary, calibration=calibration, leagues=leagues, matches=matches,
    )
