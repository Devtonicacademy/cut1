"""
football-data.org client (free tier: 10 requests/minute, key in FOOTBALL_DATA_KEY).
Used to see fixtures further ahead than the football-data.co.uk snapshot. Its team
names ("Manchester City FC") are mapped onto the football-data.co.uk names used in
our history ("Man City") so ratings, form and H2H line up.
"""
import datetime as dt
import difflib
import re
import unicodedata
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from apps.api.app.data.football_data_uk import UK_TZ

API_URL = "https://api.football-data.org/v4"
SOURCE = "football-data.org"
# football-data.org competition code -> football-data.co.uk division (free-tier competitions only)
COMPETITIONS = {"PL": "E0", "ELC": "E1", "PD": "SP1", "SA": "I1", "BL1": "D1", "FL1": "F1", "DED": "N1", "PPL": "P1"}
# Cross-country competitions: football-data.org code -> our competition code. Clubs are matched against
# every league we hold history for, so the bar is higher than within one country.
EUROPEAN_COMPETITIONS = {"CL": "CL"}
CROSS_COUNTRY_THRESHOLD = 0.85
MATCH_THRESHOLD = 0.72

# Names too different for fuzzy matching: football-data.org full name -> football-data.co.uk name
NAME_OVERRIDES = {
    "Nottingham Forest FC": "Nott'm Forest",
    "Wolverhampton Wanderers FC": "Wolves",
    "Sheffield Wednesday FC": "Sheffield Weds",
    "Queens Park Rangers FC": "QPR",
    "West Bromwich Albion FC": "West Brom",
    "Athletic Club": "Ath Bilbao",
    "Club Atlético de Madrid": "Ath Madrid",
    "RCD Espanyol de Barcelona": "Espanol",
    "Rayo Vallecano de Madrid": "Vallecano",
    "Real Betis Balompié": "Betis",
    "RC Celta de Vigo": "Celta",
    "FC Bayern München": "Bayern Munich",
    "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "1. FC Köln": "FC Koln",
    "1. FSV Mainz 05": "Mainz",
    "Hamburger SV": "Hamburg",
    "Paris Saint-Germain FC": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon",
    "AS Saint-Étienne": "St Etienne",
    "Stade Rennais FC 1901": "Rennes",
    "PSV": "PSV Eindhoven",
    "NEC": "Nijmegen",
    "Sporting Clube de Portugal": "Sp Lisbon",
    "Sporting Clube de Braga": "Sp Braga",
    "Vitória SC": "Guimaraes",
    "FC Internazionale Milano": "Inter",
}

_GENERIC_TOKENS = {
    "fc", "afc", "cf", "ac", "as", "ss", "ssc", "us", "bc", "cfc", "acf", "calcio", "club", "sc", "sv",
    "rc", "cd", "ud", "sd", "rcd", "ca", "fk", "sk", "vfl", "vfb", "tsg", "fsv", "bv", "de", "and", "hove",
}


def normalise(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(t for t in text.split() if t not in _GENERIC_TOKENS and not t.isdigit())


def similarity(a: str, b: str) -> float:
    na, nb = normalise(a), normalise(b)
    if not na or not nb:
        return 0.0
    ta, tb = set(na.split()), set(nb.split())
    if ta <= tb or tb <= ta:
        return 0.95 if na != nb else 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def match_teams(
    fd_teams: Iterable[Mapping], candidates: Iterable[str], threshold: float = MATCH_THRESHOLD
) -> Tuple[Dict[int, str], List[str]]:
    """
    Maps football-data.org teams to our team names. Overrides first, then the best
    fuzzy pairs, each of our names used at most once. Returns (mapping, unmatched names).
    """
    candidates = sorted(set(candidates))
    teams = {t["id"]: t for t in fd_teams}
    mapping: Dict[int, str] = {}
    for team_id, t in teams.items():
        override = NAME_OVERRIDES.get(t.get("name", ""))
        if override in candidates:
            mapping[team_id] = override

    pairs = []
    for team_id, t in teams.items():
        if team_id in mapping:
            continue
        labels = [x for x in (t.get("shortName"), t.get("name")) if x]
        for cand in candidates:
            pairs.append((max(similarity(label, cand) for label in labels), team_id, cand))
    used = set(mapping.values())
    for score, team_id, cand in sorted(pairs, reverse=True):
        if score < threshold:
            break
        if team_id not in mapping and cand not in used:
            mapping[team_id] = cand
            used.add(cand)
    unmatched = sorted(teams[i].get("name", str(i)) for i in teams if i not in mapping)
    return mapping, unmatched


def parse_matches(payload: Mapping, div: str, candidates: Iterable[str]) -> Tuple[List[Dict], List[str]]:
    """Scheduled matches -> fixture rows (no odds). Matches with an unmapped team are dropped."""
    matches = [m for m in payload.get("matches", []) if m.get("status") in ("SCHEDULED", "TIMED")]
    fd_teams = {t["id"]: t for m in matches for t in (m["homeTeam"], m["awayTeam"]) if t.get("id")}
    mapping, unmatched = match_teams(fd_teams.values(), candidates)
    rows = []
    for m in matches:
        home, away = mapping.get(m["homeTeam"].get("id")), mapping.get(m["awayTeam"].get("id"))
        if not home or not away:
            continue
        kickoff = dt.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        rows.append({
            "div": div,
            "match_date": kickoff.astimezone(UK_TZ).date().isoformat(),  # same date convention as football-data.co.uk
            "kickoff_utc": kickoff.isoformat(),
            "home_team": home,
            "away_team": away,
            "source": SOURCE,
        })
    return rows, unmatched


def parse_cross_country_matches(
    payload: Mapping, comp: str, team_divs: Mapping[str, str]
) -> Tuple[List[Dict], List[str]]:
    """
    Scheduled matches of a cross-country competition -> fixture rows tagged with each club's domestic
    division. `team_divs` maps our team names to a division. Matches where either club has no history
    in our leagues are dropped, because there is nothing to rate them with; those clubs are returned.
    """
    matches = [m for m in payload.get("matches", []) if m.get("status") in ("SCHEDULED", "TIMED")]
    fd_teams = {t["id"]: t for m in matches for t in (m["homeTeam"], m["awayTeam"]) if t.get("id")}
    mapping, unmatched = match_teams(fd_teams.values(), team_divs, CROSS_COUNTRY_THRESHOLD)
    rows = []
    for m in matches:
        home, away = mapping.get(m["homeTeam"].get("id")), mapping.get(m["awayTeam"].get("id"))
        if not home or not away:
            continue
        kickoff = dt.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        rows.append({
            "div": comp,
            "match_date": kickoff.astimezone(UK_TZ).date().isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "home_team": home,
            "away_team": away,
            "home_div": team_divs[home],
            "away_div": team_divs[away],
            "source": SOURCE,
        })
    return rows, unmatched


LIVE_STATUSES = ("IN_PLAY", "PAUSED", "FINISHED")


def _goals(score: Mapping, key: str):
    part = (score or {}).get(key) or {}
    home, away = part.get("home"), part.get("away")
    return (home, away) if home is not None and away is not None else None


def parse_live_scores(payload: Mapping, candidates: Iterable[str]) -> List[Dict]:
    """
    Matches that are under way or just finished -> {home_team, away_team, kickoff_utc, status, home_goals,
    away_goals, minute}. Names are mapped to ours; matches with an unmapped team are dropped. The running
    score is the full-time figure, or the half-time one when that is all the feed has yet.
    """
    matches = [m for m in payload.get("matches", []) if m.get("status") in LIVE_STATUSES]
    fd_teams = {t["id"]: t for m in matches for t in (m["homeTeam"], m["awayTeam"]) if t.get("id")}
    mapping, _ = match_teams(fd_teams.values(), candidates)
    rows = []
    for m in matches:
        home, away = mapping.get(m["homeTeam"].get("id")), mapping.get(m["awayTeam"].get("id"))
        if not home or not away:
            continue
        score = m.get("score") or {}
        goals = _goals(score, "fullTime") or _goals(score, "halfTime")
        minute = m.get("minute")
        rows.append({
            "home_team": home, "away_team": away,
            "kickoff_utc": dt.datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).isoformat(),
            "status": m["status"],
            "home_goals": goals[0] if goals else None, "away_goals": goals[1] if goals else None,
            "minute": int(minute) if isinstance(minute, (int, float)) or (isinstance(minute, str) and minute.isdigit()) else None,
        })
    return rows


def extract_crests(
    payload: Mapping, key: str, candidates: Iterable[str], threshold: float = MATCH_THRESHOLD
) -> List[Dict]:
    """
    Crest URLs from a competition's matches payload: one per club we can place (keyed by our team
    name) plus the competition emblem (keyed by `key`, our competition code). Clubs and the emblem
    without a URL are skipped.
    """
    matches = [m for m in payload.get("matches", []) if m.get("status") in ("SCHEDULED", "TIMED")]
    fd_teams = {t["id"]: t for m in matches for t in (m["homeTeam"], m["awayTeam"]) if t.get("id")}
    mapping, _ = match_teams(fd_teams.values(), candidates, threshold)
    rows = [{"kind": "team", "key": mapping[i], "url": t["crest"]} for i, t in fd_teams.items() if i in mapping and t.get("crest")]
    emblem = (payload.get("competition") or {}).get("emblem")
    if emblem:
        rows.append({"kind": "league", "key": key, "url": emblem})
    return rows


def matches_url(code: str, date_from: dt.date, date_to: dt.date) -> str:
    return f"{API_URL}/competitions/{code}/matches?dateFrom={date_from.isoformat()}&dateTo={date_to.isoformat()}"
