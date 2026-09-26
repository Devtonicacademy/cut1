"""
Downloads free football data into the local SQLite database.

Usage:
    python -m apps.api.app.data.ingest                  # last 5 seasons + upcoming fixtures
    python -m apps.api.app.data.ingest --seasons 10
    python -m apps.api.app.data.ingest --fixtures-only
"""
import argparse
import datetime as dt
import json
import os
import time
from typing import Dict, List, Optional

import httpx
from dotenv import load_dotenv

from apps.api.app.data import db
from apps.api.app.data import football_data_org as fdorg
from apps.api.app.data import football_data_uk as fduk
from apps.api.app.data.leagues import LEAGUES

RAW_CACHE_DIR = db.REPO_ROOT / "data" / "raw"
REQUEST_PAUSE_SECONDS = 0.4  # be polite to a free, volunteer-run source
FD_ORG_PAUSE_SECONDS = 6.5  # free tier allows 10 requests per minute
FD_ORG_REFRESH_HOURS = 6
USER_AGENT = "LivelyBorg/0.1 (football prediction research)"


def is_offline() -> bool:
    return os.getenv("LIVELYBORG_OFFLINE") == "1"


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _client() -> httpx.Client:
    return httpx.Client(timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True)


def _fetch_season_file(client: httpx.Client, season: str, div: str, use_cache: bool) -> Optional[str]:
    """Returns CSV text, reading completed seasons from the on-disk cache when available."""
    cache_path = RAW_CACHE_DIR / season / f"{div}.csv"
    if use_cache and cache_path.exists():
        return fduk.decode(cache_path.read_bytes())
    response = client.get(fduk.season_url(season, div))
    time.sleep(REQUEST_PAUSE_SECONDS)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response.content)
    return fduk.decode(response.content)


def ingest_history(seasons: int = 5, leagues: Optional[List[str]] = None, verbose: bool = False) -> Dict:
    """Loads the last `seasons` seasons. Completed seasons are cached; the current one is always re-downloaded."""
    divs = leagues or list(LEAGUES)
    current_start = fduk.current_season_start(dt.date.today())
    summary = {"files": 0, "missing": [], "errors": [], "matches": 0}

    with _client() as client, db.connect() as conn:
        for start_year in range(current_start - seasons + 1, current_start + 1):
            season = fduk.season_code(start_year)
            for div in divs:
                try:
                    text = _fetch_season_file(client, season, div, use_cache=start_year != current_start)
                except httpx.HTTPError as e:
                    summary["errors"].append(f"{season}/{div}: {e}")
                    continue
                if text is None:
                    summary["missing"].append(f"{season}/{div}")
                    continue
                count = db.upsert_matches(conn, fduk.parse_results_csv(text, season))
                conn.commit()  # short transactions: never hold the write lock across downloads
                summary["files"] += 1
                summary["matches"] += count
                if verbose:
                    print(f"  {season} {div:<4} {count:>4} matches")
        db.set_meta(conn, "last_history_refresh", _now_utc().isoformat())
    return summary


def ingest_fixtures() -> int:
    with _client() as client:
        response = client.get(fduk.FIXTURES_URL)
        response.raise_for_status()
    rows = fduk.parse_fixtures_csv(fduk.decode(response.content))
    with db.connect() as conn:
        count = db.replace_fixtures(conn, rows)
        db.set_meta(conn, "last_fixtures_refresh", _now_utc().isoformat())
    return count


def _recent_team_names(conn, div: str, seasons_back: int = 3) -> List[str]:
    """Our names for teams of that country seen recently (any division, so promoted teams match)."""
    country = LEAGUES[div].country
    divs = [d for d, lg in LEAGUES.items() if lg.country == country]
    since = (dt.date.today() - dt.timedelta(days=365 * seasons_back)).isoformat()
    marks = ", ".join("?" for _ in divs)
    rows = conn.execute(
        f"SELECT home_team FROM matches WHERE div IN ({marks}) AND match_date >= ? "
        f"UNION SELECT away_team FROM matches WHERE div IN ({marks}) AND match_date >= ?",
        (*divs, since, *divs, since),
    ).fetchall()
    return [r[0] for r in rows]


def ingest_fd_org_fixtures(days_ahead: int = 14) -> Dict:
    """Scheduled matches for the next `days_ahead` days from football-data.org (needs FOOTBALL_DATA_KEY)."""
    key = os.getenv("FOOTBALL_DATA_KEY")
    if not key:
        return {"skipped": "FOOTBALL_DATA_KEY not set"}
    today = dt.date.today()
    rows, unmatched, errors = [], {}, []
    with _client() as client, db.connect() as conn:
        for i, (code, div) in enumerate(fdorg.COMPETITIONS.items()):
            if i:
                time.sleep(FD_ORG_PAUSE_SECONDS)
            try:
                response = client.get(fdorg.matches_url(code, today, today + dt.timedelta(days=days_ahead)),
                                      headers={"X-Auth-Token": key})
                response.raise_for_status()
            except httpx.HTTPError as e:
                errors.append(f"{code}: {e}")
                continue
            parsed, missing = fdorg.parse_matches(response.json(), div, _recent_team_names(conn, div))
            rows += parsed
            if missing:
                unmatched[code] = missing
        count = db.replace_fixtures(conn, rows, source=fdorg.SOURCE)
        db.set_meta(conn, "last_fdorg_refresh", _now_utc().isoformat())
        db.set_meta(conn, "fdorg_unmatched_teams", json.dumps(unmatched))
    return {"fixtures_added": count, "unmatched_teams": unmatched, "errors": errors}


def _older_than(conn, key: str, delta: dt.timedelta) -> bool:
    last = db.get_meta(conn, key)
    return not last or _now_utc() - dt.datetime.fromisoformat(last) > delta


def refresh(min_interval_minutes: int = 10) -> Dict:
    """
    Pulls the current season's results and the latest fixtures snapshot.
    Skipped when offline or when the last refresh was very recent.
    """
    if is_offline():
        return {"skipped": "offline mode"}
    with db.connect() as conn:
        recent = not _older_than(conn, "last_fixtures_refresh", dt.timedelta(minutes=min_interval_minutes))
        fdorg_due = _older_than(conn, "last_fdorg_refresh", dt.timedelta(hours=FD_ORG_REFRESH_HOURS))
    if recent:
        return {"skipped": f"refreshed less than {min_interval_minutes} minutes ago"}

    result = {"history": ingest_history(seasons=1), "fixtures": ingest_fixtures()}
    if fdorg_due:
        result["football_data_org"] = ingest_fd_org_fixtures()
    return result


def needs_refresh(max_age_hours: float = 6.0) -> bool:
    with db.connect() as conn:
        last = db.get_meta(conn, "last_fixtures_refresh")
    if not last:
        return True
    return _now_utc() - dt.datetime.fromisoformat(last) > dt.timedelta(hours=max_age_hours)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download free football data into the LivelyBorg database.")
    parser.add_argument("--seasons", type=int, default=5, help="How many seasons of history to load (default 5)")
    parser.add_argument("--leagues", nargs="*", help=f"Division codes, default all: {' '.join(LEAGUES)}")
    parser.add_argument("--fixtures-only", action="store_true", help="Only refresh the upcoming fixtures snapshot")
    args = parser.parse_args()
    load_dotenv()

    print(f"Database: {db.get_db_path()}")
    if not args.fixtures_only:
        print(f"Loading {args.seasons} season(s) of history...")
        summary = ingest_history(seasons=args.seasons, leagues=args.leagues, verbose=True)
        print(f"History: {summary['matches']} matches from {summary['files']} files")
        if summary["missing"]:
            print(f"Not published by source: {', '.join(summary['missing'])}")
        for err in summary["errors"]:
            print(f"ERROR {err}")
    print(f"Upcoming fixtures: {ingest_fixtures()}")
    print(f"football-data.org: {ingest_fd_org_fixtures()}")
    with db.connect() as conn:
        print(db.data_status(conn))


if __name__ == "__main__":
    main()
