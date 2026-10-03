"""
API-Football client (api-sports.io, key in API_FOOTBALL_KEY) for national-team fixtures that
football-data.org's free tier does not cover. Team names ("Korea Republic") are mapped onto the
names in the international results history ("South Korea") so ratings line up.
"""
import datetime as dt
from typing import Dict, Iterable, List, Mapping, Tuple

from apps.api.app.data.football_data_org import match_teams

API_URL = "https://v3.football.api-sports.io"
SOURCE = "api-football"
# API-Football league id -> our competition code (see NATIONAL_COMPETITIONS in leagues.py)
COMPETITIONS = {5: "UNL", 6: "AFCON", 36: "AFCONQ", 7: "ASIAN", 10: "FRI"}
SCHEDULED = ("TBD", "NS")
MATCH_THRESHOLD = 0.85

# API-Football name -> name used in the results history
NAME_OVERRIDES = {
    "USA": "United States",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "Cote d'Ivoire": "Ivory Coast",
    "Czechia": "Czech Republic",
    "Turkiye": "Turkey",
    "Türkiye": "Turkey",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
}


def fixtures_url(league_id: int, season: int, date_from: dt.date, date_to: dt.date) -> str:
    return (f"{API_URL}/fixtures?league={league_id}&season={season}"
            f"&from={date_from.isoformat()}&to={date_to.isoformat()}")


def _map_teams(matches, names: List[str]):
    api_teams = {t["id"]: {"id": t["id"], "name": t["name"]}
                 for m in matches for t in (m["teams"]["home"], m["teams"]["away"]) if t.get("id")}
    mapping: Dict[int, str] = {}
    for team_id, t in api_teams.items():
        override = NAME_OVERRIDES.get(t["name"], t["name"])
        if override in names:
            mapping[team_id] = override
    rest = {i: t for i, t in api_teams.items() if i not in mapping}
    fuzzy, _ = match_teams(rest.values(), [n for n in names if n not in mapping.values()], MATCH_THRESHOLD)
    mapping.update(fuzzy)
    return api_teams, mapping


def extract_crests(payload: Mapping, comp: str, team_names: Iterable[str]) -> List[Dict]:
    """Team logos (keyed by our team name) and the competition logo (keyed by `comp`) from a fixtures payload."""
    names = sorted(set(team_names))
    matches = [m for m in payload.get("response", []) if m["fixture"]["status"]["short"] in SCHEDULED]
    _, mapping = _map_teams(matches, names)
    rows, seen = [], set()
    for m in matches:
        for side in ("home", "away"):
            t = m["teams"][side]
            if t.get("id") in mapping and t.get("logo") and t["id"] not in seen:
                seen.add(t["id"])
                rows.append({"kind": "team", "key": mapping[t["id"]], "url": t["logo"]})
    logo = next((m.get("league", {}).get("logo") for m in matches if m.get("league", {}).get("logo")), None)
    if logo:
        rows.append({"kind": "league", "key": comp, "url": logo})
    return rows


def parse_fixtures(payload: Mapping, comp: str, team_names: Iterable[str]) -> Tuple[List[Dict], List[str]]:
    """Not-yet-played matches -> fixture rows (no odds). Matches with a team we cannot place are dropped."""
    names = sorted(set(team_names))
    matches = [m for m in payload.get("response", []) if m["fixture"]["status"]["short"] in SCHEDULED]
    api_teams, mapping = _map_teams(matches, names)
    unmatched = sorted(t["name"] for i, t in api_teams.items() if i not in mapping)

    rows = []
    for m in matches:
        home, away = mapping.get(m["teams"]["home"].get("id")), mapping.get(m["teams"]["away"].get("id"))
        if not home or not away:
            continue
        kickoff = dt.datetime.fromisoformat(m["fixture"]["date"]).astimezone(dt.timezone.utc)
        rows.append({
            "div": comp,
            "match_date": kickoff.date().isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "home_team": home,
            "away_team": away,
            "source": SOURCE,
        })
    return rows, unmatched
