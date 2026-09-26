"""
Public, tamper-evident record of predictions.

- Predictions are locked once, between LOCK_WINDOW_HOURS before kickoff and kickoff,
  and are never updated afterwards.
- Each entry's SHA-256 hash covers its prediction and the previous entry's hash, so
  changing or deleting any past prediction breaks every hash after it (see verify_chain).
- After the match, the result is graded from the official results feed.
"""
import datetime as dt
import hashlib
import json
import sqlite3
from typing import Dict, Iterable, List, Optional

from apps.api.app.models.schemas import BetStatus, Fixture, TrackRecordEntry, TrackRecordStats

LOCK_WINDOW_HOURS = 36
GRADE_AFTER_HOURS = 2  # a match is over roughly two hours after kickoff
VOID_AFTER_DAYS = 7  # no result a week after kickoff: postponed or abandoned
GENESIS_HASH = "0" * 64
NOTIONAL_STAKE_NGN = 1000.0  # flat stake used to show what following every pick would have returned
PICKS = ("1", "X", "2")

_HASHED_FIELDS = [
    "fixture_id", "div", "match_date", "kickoff_utc", "home_team", "away_team", "created_at", "model",
    "p_home", "p_draw", "p_away", "pick", "pick_prob", "odds_h", "odds_d", "odds_a", "prev_hash",
]


def entry_hash(entry: Dict) -> str:
    payload = json.dumps({k: entry[k] for k in _HASHED_FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _last_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT hash FROM predictions ORDER BY seq DESC LIMIT 1").fetchone()
    return row["hash"] if row else GENESIS_HASH


def lock_predictions(conn: sqlite3.Connection, fixtures: Iterable[Fixture], now: dt.datetime) -> int:
    """Records a prediction for every fixture inside the lock window that has none yet."""
    prev_hash = _last_hash(conn)
    locked = 0
    upcoming = sorted(
        (f for f in fixtures if f.prediction and f.kickoff_timestamp and f.div),
        key=lambda f: f.kickoff_timestamp,
    )
    for f in upcoming:
        kickoff = dt.datetime.fromisoformat(f.kickoff_timestamp).astimezone(dt.timezone.utc)
        if not now < kickoff <= now + dt.timedelta(hours=LOCK_WINDOW_HOURS):
            continue
        if conn.execute("SELECT 1 FROM predictions WHERE fixture_id = ?", (f.id,)).fetchone():
            continue
        p = f.prediction
        probs = [round(p.prob_home_win, 4), round(p.prob_draw, 4), round(p.prob_away_win, 4)]
        best = max(range(3), key=lambda i: probs[i])
        priced = f.sportybet_odds.bookmaker == "Market Average"
        entry = {
            "fixture_id": f.id,
            "div": f.div,
            "match_date": kickoff.date().isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "home_team": f.home_team.name,
            "away_team": f.away_team.name,
            "created_at": now.isoformat(),
            "model": p.prediction_source or "unknown",
            "p_home": probs[0], "p_draw": probs[1], "p_away": probs[2],
            "pick": PICKS[best],
            "pick_prob": probs[best],
            "odds_h": f.sportybet_odds.home_win if priced else None,
            "odds_d": f.sportybet_odds.draw if priced else None,
            "odds_a": f.sportybet_odds.away_win if priced else None,
            "prev_hash": prev_hash,
        }
        entry["hash"] = entry_hash(entry)
        columns = list(entry)
        conn.execute(
            f"INSERT INTO predictions ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [entry[c] for c in columns],
        )
        prev_hash = entry["hash"]
        locked += 1
    return locked


def grade(conn: sqlite3.Connection, now: dt.datetime) -> Dict[str, int]:
    """Fills in results for finished matches; voids matches with no result after a week."""
    graded = voided = 0
    cutoff = (now - dt.timedelta(hours=GRADE_AFTER_HOURS)).isoformat()
    for r in conn.execute("SELECT * FROM predictions WHERE graded_at IS NULL AND kickoff_utc < ?", (cutoff,)).fetchall():
        day = dt.date.fromisoformat(r["match_date"])
        result = conn.execute(
            """
            SELECT fthg, ftag FROM matches WHERE div = ? AND home_team = ? AND away_team = ?
            AND match_date BETWEEN ? AND ? ORDER BY match_date LIMIT 1
            """,
            (r["div"], r["home_team"], r["away_team"],
             (day - dt.timedelta(days=2)).isoformat(), (day + dt.timedelta(days=2)).isoformat()),
        ).fetchone()
        if result:
            hg, ag = result["fthg"], result["ftag"]
            outcome = "1" if hg > ag else ("X" if hg == ag else "2")
            conn.execute(
                "UPDATE predictions SET fthg = ?, ftag = ?, correct = ?, graded_at = ? WHERE seq = ?",
                (hg, ag, int(outcome == r["pick"]), now.isoformat(), r["seq"]),
            )
            graded += 1
        elif now - dt.datetime.fromisoformat(r["kickoff_utc"]) > dt.timedelta(days=VOID_AFTER_DAYS):
            conn.execute("UPDATE predictions SET graded_at = ? WHERE seq = ?", (now.isoformat(), r["seq"]))
            voided += 1
    return {"graded": graded, "voided": voided}


def verify_chain(conn: sqlite3.Connection) -> Dict:
    """Recomputes every hash; any edited, inserted or deleted past prediction is detected."""
    prev = GENESIS_HASH
    rows = conn.execute("SELECT * FROM predictions ORDER BY seq").fetchall()
    for r in rows:
        entry = dict(r)
        if entry["prev_hash"] != prev or entry_hash(entry) != entry["hash"]:
            return {"valid": False, "entries": len(rows), "first_broken_seq": entry["seq"]}
        prev = entry["hash"]
    return {"valid": True, "entries": len(rows), "first_broken_seq": None, "latest_hash": prev}


def export(conn: sqlite3.Connection) -> Dict:
    """The full ledger plus what anyone needs to re-check every hash independently."""
    return {
        "how_to_verify": (
            "For each entry in order: take the fields listed in hashed_fields, serialise them as JSON with "
            "sorted keys and no spaces (separators ',' and ':'), and SHA-256 the UTF-8 bytes. The result must "
            "equal 'hash', and each entry's 'prev_hash' must equal the previous entry's 'hash' "
            "(the first one uses genesis_hash)."
        ),
        "hashed_fields": _HASHED_FIELDS,
        "genesis_hash": GENESIS_HASH,
        "entries": [dict(r) for r in conn.execute("SELECT * FROM predictions ORDER BY seq")],
    }


def _pick_label(r: sqlite3.Row) -> str:
    return {"1": f"{r['home_team']} to Win", "X": "Draw", "2": f"{r['away_team']} to Win"}[r["pick"]]


def _pick_odds(r: sqlite3.Row) -> Optional[float]:
    return {"1": r["odds_h"], "X": r["odds_d"], "2": r["odds_a"]}[r["pick"]]


def stats(conn: sqlite3.Connection, limit: int = 200) -> TrackRecordStats:
    """
    Accuracy over every graded prediction, plus what a flat notional stake on each
    priced pick would have returned at the market-average odds recorded at lock time.
    """
    rows = conn.execute("SELECT * FROM predictions ORDER BY kickoff_utc, seq").fetchall()
    entries: List[TrackRecordEntry] = []
    wins = losses = voids = 0
    staked = returned = 0.0
    for r in rows:
        odds = _pick_odds(r)
        if r["graded_at"] is None:
            status = BetStatus.PENDING
        elif r["fthg"] is None:
            status = BetStatus.VOID
        else:
            status = BetStatus.WON if r["correct"] else BetStatus.LOST
        wins += status == BetStatus.WON
        losses += status == BetStatus.LOST
        voids += status == BetStatus.VOID

        stake = NOTIONAL_STAKE_NGN if odds and status in (BetStatus.WON, BetStatus.LOST) else 0.0
        ret = stake * odds if stake and status == BetStatus.WON else 0.0
        staked += stake
        returned += ret

        if status == BetStatus.PENDING:
            note = f"Locked {r['created_at'][:16].replace('T', ' ')} UTC, before kickoff."
        elif status == BetStatus.VOID:
            note = "No result reported within a week (postponed or abandoned)."
        else:
            note = f"Final score {r['fthg']}-{r['ftag']}."
        if not odds:
            note += " No market price at lock time: counts for accuracy only."
        entries.append(TrackRecordEntry(
            id=f"pred-{r['seq']:05d}",
            date=r["match_date"],
            match=f"{r['home_team']} vs {r['away_team']}",
            prediction=f"{_pick_label(r)} ({r['pick_prob']:.0%})",
            odds=odds or round(1 / r["pick_prob"], 2),
            stake_ngn=stake,
            result=status,
            return_ngn=round(ret, 2),
            profit_ngn=round(ret - stake, 2),
            pnl_running_roi=round((returned - staked) / staked * 100, 1) if staked else 0.0,
            ai_post_mortem=f"{note} Hash {r['hash'][:12]}",
        ))

    streak = 0
    for e in reversed(entries):
        if e.result == BetStatus.PENDING:
            continue
        if e.result != BetStatus.WON:
            break
        streak += 1

    return TrackRecordStats(
        total_bets=len(entries),
        wins=wins,
        losses=losses,
        voids=voids,
        win_rate_pct=round(wins / (wins + losses) * 100, 1) if wins + losses else 0.0,
        total_staked_ngn=round(staked, 2),
        total_returned_ngn=round(returned, 2),
        net_profit_ngn=round(returned - staked, 2),
        roi_pct=round((returned - staked) / staked * 100, 1) if staked else 0.0,
        current_winning_streak=streak,
        entries=list(reversed(entries))[:limit],
    )
