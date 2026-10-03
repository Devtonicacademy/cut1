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

from apps.api.app.data import api_football
from apps.api.app.data import db
from apps.api.app.data import football_data_org as fdorg
from apps.api.app.data import football_data_uk as fduk
from apps.api.app.data import national
from apps.api.app.data import the_odds_api
from apps.api.app.data.leagues import LEAGUES

RAW_CACHE_DIR = db.REPO_ROOT / "data" / "raw"
REQUEST_PAUSE_SECONDS = 0.4  # be polite to a free, volunteer-run source
FD_ORG_PAUSE_SECONDS = 6.5  # free tier allows 10 requests per minute
FD_ORG_REFRESH_HOURS = 6
API_FOOTBALL_REFRESH_HOURS = 6  # 5 requests per refresh, well inside the free 100 a day
NATIONAL_REFRESH_HOURS = 24
ODDS_API_MIN_CREDITS_LEFT = 20  # the free plan is 500 credits a month; stop before it runs dry
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


def _team_divisions(conn, seasons_back: int = 3) -> Dict[str, str]:
    """Our team names -> the division they most recently played in, across every league we hold."""
    since = (dt.date.today() - dt.timedelta(days=365 * seasons_back)).isoformat()
    rows = conn.execute(
        "SELECT home_team AS team, div, match_date FROM matches WHERE match_date >= ? "
        "UNION ALL SELECT away_team, div, match_date FROM matches WHERE match_date >= ? ORDER BY match_date",
        (since, since),
    ).fetchall()
    return {r["team"]: r["div"] for r in rows}  # later rows overwrite: the most recent division wins


def ingest_fd_org_fixtures(days_ahead: int = 14) -> Dict:
    """Scheduled matches for the next `days_ahead` days from football-data.org (needs FOOTBALL_DATA_KEY)."""
    key = os.getenv("FOOTBALL_DATA_KEY")
    if not key:
        return {"skipped": "FOOTBALL_DATA_KEY not set"}
    today = dt.date.today()
    rows, crests, unmatched, errors = [], [], {}, []
    competitions = [(code, div, False) for code, div in fdorg.COMPETITIONS.items()]
    competitions += [(code, comp, True) for code, comp in fdorg.EUROPEAN_COMPETITIONS.items()]
    with _client() as client, db.connect() as conn:
        team_divs = _team_divisions(conn)
        for i, (code, div, cross_country) in enumerate(competitions):
            if i:
                time.sleep(FD_ORG_PAUSE_SECONDS)
            try:
                response = client.get(fdorg.matches_url(code, today, today + dt.timedelta(days=days_ahead)),
                                      headers={"X-Auth-Token": key})
                response.raise_for_status()
            except httpx.HTTPError as e:
                errors.append(f"{code}: {e}")
                continue
            if cross_country:
                parsed, missing = fdorg.parse_cross_country_matches(response.json(), div, team_divs)
                crests += fdorg.extract_crests(response.json(), div, team_divs, fdorg.CROSS_COUNTRY_THRESHOLD)
            else:
                names = _recent_team_names(conn, div)
                parsed, missing = fdorg.parse_matches(response.json(), div, names)
                crests += fdorg.extract_crests(response.json(), div, names)
            rows += parsed
            if missing:
                unmatched[code] = missing
        count = db.replace_fixtures(conn, rows, source=fdorg.SOURCE)
        db.upsert_crests(conn, crests)
        db.set_meta(conn, "last_fdorg_refresh", _now_utc().isoformat())
        db.set_meta(conn, "fdorg_unmatched_teams", json.dumps(unmatched))
    return {"fixtures_added": count, "unmatched_teams": unmatched, "errors": errors}


def ingest_national_history() -> Dict:
    """Downloads the full international results file (about 3 MB) into the national_matches table."""
    with _client() as client:
        response = client.get(national.RESULTS_URL)
        response.raise_for_status()
    rows = national.parse_results_csv(response.text)
    with db.connect() as conn:
        count = db.upsert_national_matches(conn, rows)
        db.set_meta(conn, "last_national_refresh", _now_utc().isoformat())
    return {"matches": count}


def ingest_api_football_fixtures(days_ahead: int = 14) -> Dict:
    """Upcoming national-team games for the next `days_ahead` days (needs API_FOOTBALL_KEY)."""
    key = os.getenv("API_FOOTBALL_KEY")
    if not key:
        return {"skipped": "API_FOOTBALL_KEY not set"}
    today = dt.date.today()
    rows, crests, unmatched, errors = [], [], {}, []
    with _client() as client, db.connect() as conn:
        names = {r["home_team"] for r in db.load_national_matches(conn)} | \
                {r["away_team"] for r in db.load_national_matches(conn)}
        for league_id, comp in api_football.COMPETITIONS.items():
            try:
                response = client.get(
                    api_football.fixtures_url(league_id, today.year, today, today + dt.timedelta(days=days_ahead)),
                    headers={"x-apisports-key": key})
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as e:
                errors.append(f"{comp}: {e}")
                continue
            if payload.get("errors"):  # the API reports plan limits in the body, with HTTP 200
                errors.append(f"{comp}: {payload['errors']}")
                continue
            parsed, missing = api_football.parse_fixtures(payload, comp, names)
            crests += api_football.extract_crests(payload, comp, names)
            rows += parsed
            if missing:
                unmatched[comp] = missing
        count = db.replace_fixtures(conn, rows, source=api_football.SOURCE)
        db.upsert_crests(conn, crests)
        db.set_meta(conn, "last_api_football_refresh", _now_utc().isoformat())
        db.set_meta(conn, "api_football_unmatched_teams", json.dumps(unmatched))
    return {"fixtures_added": count, "unmatched_teams": unmatched, "errors": errors}


def ingest_odds_api(window_days: Optional[int] = None) -> Dict:
    """
    Market odds for upcoming fixtures that have none (needs ODDS_API_KEY). Only divisions with an unpriced
    fixture kicking off within `window_days` are requested, each costing one credit per region.
    """
    key = os.getenv("ODDS_API_KEY")
    if not key:
        return {"skipped": "ODDS_API_KEY not set"}
    window_days = window_days or int(os.getenv("ODDS_API_WINDOW_DAYS", "3"))
    regions = os.getenv("ODDS_API_REGIONS", "eu")
    now = _now_utc()
    horizon = (now + dt.timedelta(days=window_days)).isoformat()
    rows, unmatched, errors, queried = [], {}, [], []
    remaining = None
    with _client() as client, db.connect() as conn:
        unpriced: Dict[str, List[Dict]] = {}
        for f in db.load_fixtures_after(conn, now.isoformat()):
            if f["avg_h"] is None and f["kickoff_utc"] <= horizon and f["div"] in the_odds_api.SPORT_KEYS:
                unpriced.setdefault(f["div"], []).append(f)
        for div, fixtures in unpriced.items():
            try:
                response = client.get(the_odds_api.odds_url(the_odds_api.SPORT_KEYS[div], regions),
                                      params={"apiKey": key})
                response.raise_for_status()
                events = response.json()
            except (httpx.HTTPError, ValueError) as e:
                errors.append(f"{div}: {type(e).__name__}")  # never echo the URL: it carries the key
                continue
            queried.append(div)
            parsed, missing = the_odds_api.parse_events(events, div, fixtures)
            rows += parsed
            if missing:
                unmatched[div] = missing
            left = response.headers.get("x-requests-remaining")
            if left is not None:
                remaining = float(left)
                if remaining < ODDS_API_MIN_CREDITS_LEFT:
                    errors.append(f"stopped early: {remaining:g} credits left")
                    break
        count = db.replace_odds_overlay(conn, rows, queried, now.isoformat())
        db.set_meta(conn, "last_odds_api_refresh", now.isoformat())
        db.set_meta(conn, "odds_api_unmatched_teams", json.dumps(unmatched))
        if remaining is not None:
            db.set_meta(conn, "odds_api_requests_remaining", str(remaining))
    return {"priced_fixtures": count, "divisions_queried": queried, "unmatched_teams": unmatched,
            "credits_left": remaining, "errors": errors}


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
        national_due = _older_than(conn, "last_national_refresh", dt.timedelta(hours=NATIONAL_REFRESH_HOURS))
        apif_due = _older_than(conn, "last_api_football_refresh", dt.timedelta(hours=API_FOOTBALL_REFRESH_HOURS))
        odds_due = _older_than(conn, "last_odds_api_refresh",
                               dt.timedelta(hours=float(os.getenv("ODDS_API_REFRESH_HOURS", "8"))))
        # Crests are collected by those two feeds. A database that predates them (or whose feeds were skipped)
        # has none, so pull the feeds now instead of waiting out their refresh interval.
        no_crests = db.crest_count(conn) == 0
        fdorg_due, apif_due = fdorg_due or no_crests, apif_due or no_crests
    if recent:
        return {"skipped": f"refreshed less than {min_interval_minutes} minutes ago"}

    result = {"history": ingest_history(seasons=1), "fixtures": ingest_fixtures()}
    if fdorg_due:
        result["football_data_org"] = ingest_fd_org_fixtures()
    for name, due, fn in (("national_history", national_due, ingest_national_history),
                          ("api_football", apif_due, ingest_api_football_fixtures),
                          ("odds_api", odds_due, ingest_odds_api)):  # last: it prices what the others listed
        if due:
            try:
                result[name] = fn()
            except (httpx.HTTPError, ValueError) as e:  # a failing optional source must not stop the cycle
                result[name] = {"error": str(e)}
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
    load_dotenv(db.REPO_ROOT / ".env")

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
    print(f"National-team history: {ingest_national_history()}")
    print(f"API-Football: {ingest_api_football_fixtures()}")
    print(f"The Odds API: {ingest_odds_api()}")
    with db.connect() as conn:
        print(db.data_status(conn))


if __name__ == "__main__":
    main()
