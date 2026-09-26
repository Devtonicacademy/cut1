"""
Client for football-data.co.uk: free historical results (with shots, cards and
bookmaker odds) and a rolling snapshot of upcoming fixtures. No API key required.
Kickoff times in these files are UK local time.
"""
import csv
import datetime as dt
import io
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from apps.api.app.data.leagues import LEAGUES

BASE_URL = "https://www.football-data.co.uk"
FIXTURES_URL = f"{BASE_URL}/fixtures.csv"
UK_TZ = ZoneInfo("Europe/London")
UTC = dt.timezone.utc

_RESULT_COLUMNS = {"FTHG": "fthg", "FTAG": "ftag"}
_STAT_COLUMNS = {
    "HTHG": "hthg", "HTAG": "htag", "HS": "hs", "AS": "as_", "HST": "hst", "AST": "ast",
    "HC": "hc", "AC": "ac", "HY": "hy", "AY": "ay", "HR": "hr", "AR": "ar",
}
# Our column -> candidate CSV headers (newer name first, pre-2019 "Bb" name second).
_ODDS_COLUMNS = {
    "avg_h": ["AvgH", "BbAvH"], "avg_d": ["AvgD", "BbAvD"], "avg_a": ["AvgA", "BbAvA"],
    "max_h": ["MaxH", "BbMxH"], "max_d": ["MaxD", "BbMxD"], "max_a": ["MaxA", "BbMxA"],
    "avg_o25": ["Avg>2.5", "BbAv>2.5"], "avg_u25": ["Avg<2.5", "BbAv<2.5"],
    "max_o25": ["Max>2.5", "BbMx>2.5"], "max_u25": ["Max<2.5", "BbMx<2.5"],
}
_CLOSING_ODDS_COLUMNS = {
    "avg_ch": ["AvgCH"], "avg_cd": ["AvgCD"], "avg_ca": ["AvgCA"],
    "psc_h": ["PSCH"], "psc_d": ["PSCD"], "psc_a": ["PSCA"],
}


def season_code(start_year: int) -> str:
    """2026 -> '2627' (the 2026/27 season)."""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def current_season_start(today: dt.date) -> int:
    return today.year if today.month >= 7 else today.year - 1


def season_url(season: str, div: str) -> str:
    return f"{BASE_URL}/mmz4281/{season}/{div}.csv"


def decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def parse_date(value: str) -> Optional[dt.date]:
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def uk_kickoff_to_utc(match_date: dt.date, time_str: Optional[str]) -> Optional[dt.datetime]:
    time_str = (time_str or "").strip()
    if not time_str:
        return None
    try:
        hour, minute = (int(p) for p in time_str.split(":")[:2])
    except ValueError:
        return None
    local = dt.datetime.combine(match_date, dt.time(hour, minute), tzinfo=UK_TZ)
    return local.astimezone(UTC)


def _to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(float(value)) if value not in (None, "") else None
    except ValueError:
        return None


def _to_float(value: Optional[str]) -> Optional[float]:
    try:
        f = float(value) if value not in (None, "") else None
    except ValueError:
        return None
    return f if f and f > 1.0 else None


def _first_float(row: Dict[str, str], headers: List[str]) -> Optional[float]:
    for h in headers:
        v = _to_float(row.get(h))
        if v is not None:
            return v
    return None


def _base_row(row: Dict[str, str]) -> Optional[Dict]:
    div = (row.get("Div") or "").strip()
    home = (row.get("HomeTeam") or "").strip()
    away = (row.get("AwayTeam") or "").strip()
    match_date = parse_date(row.get("Date", ""))
    if div not in LEAGUES or not home or not away or match_date is None:
        return None
    kickoff = uk_kickoff_to_utc(match_date, row.get("Time"))
    parsed = {
        "div": div,
        "match_date": match_date.isoformat(),
        "kickoff_utc": kickoff.isoformat() if kickoff else None,
        "home_team": home,
        "away_team": away,
    }
    for col, headers in _ODDS_COLUMNS.items():
        parsed[col] = _first_float(row, headers)
    return parsed


def parse_results_csv(text: str, season: str) -> List[Dict]:
    """Parses a season results file. Rows without a full-time score are skipped."""
    rows = []
    for row in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
        parsed = _base_row(row)
        if parsed is None:
            continue
        fthg, ftag = _to_int(row.get("FTHG")), _to_int(row.get("FTAG"))
        if fthg is None or ftag is None:
            continue
        parsed.update({"season": season, "fthg": fthg, "ftag": ftag})
        for header, col in _STAT_COLUMNS.items():
            parsed[col] = _to_int(row.get(header))
        for col, headers in _CLOSING_ODDS_COLUMNS.items():
            parsed[col] = _first_float(row, headers)
        rows.append(parsed)
    return rows


def parse_fixtures_csv(text: str) -> List[Dict]:
    """Parses the upcoming-fixtures snapshot. Rows without a kickoff time are skipped."""
    return [
        parsed
        for parsed in (_base_row(row) for row in csv.DictReader(io.StringIO(text.lstrip("﻿"))))
        if parsed is not None and parsed["kickoff_utc"] is not None
    ]
