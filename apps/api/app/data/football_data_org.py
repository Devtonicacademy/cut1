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


def match_teams(fd_teams: Iterable[Mapping], candidates: Iterable[str]) -> Tuple[Dict[int, str], List[str]]:
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
        if score < MATCH_THRESHOLD:
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


def matches_url(code: str, date_from: dt.date, date_to: dt.date) -> str:
    return f"{API_URL}/competitions/{code}/matches?dateFrom={date_from.isoformat()}&dateTo={date_to.isoformat()}"
