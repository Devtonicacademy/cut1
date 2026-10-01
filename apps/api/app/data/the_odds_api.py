"""
The Odds API client (the-odds-api.com, key in ODDS_API_KEY). A second source of real market odds for
fixtures that football-data.co.uk has not priced yet (it only publishes odds a few days ahead, and the
other fixture feeds carry none). Prices from several bookmakers are averaged, the same idea as the
"Market Average" columns of football-data.co.uk, and only used when enough bookmakers quote the match.
"""
import datetime as dt
from typing import Dict, Iterable, List, Mapping, Tuple

from apps.api.app.data.football_data_org import match_teams

API_URL = "https://api.the-odds-api.com/v4"
MIN_BOOKMAKERS = 3  # fewer quotes is not a market average
MATCH_THRESHOLD = 0.6  # candidates are only the teams of one league's unpriced fixtures, so this can be loose
KICKOFF_TOLERANCE = dt.timedelta(hours=36)

# our division -> The Odds API sport key (leagues it does not list are simply not covered)
SPORT_KEYS = {
    "E0": "soccer_epl", "E1": "soccer_efl_champ", "E2": "soccer_england_league1", "E3": "soccer_england_league2",
    "SC0": "soccer_spl", "D1": "soccer_germany_bundesliga", "D2": "soccer_germany_bundesliga2",
    "SP1": "soccer_spain_la_liga", "SP2": "soccer_spain_segunda_division",
    "I1": "soccer_italy_serie_a", "I2": "soccer_italy_serie_b",
    "F1": "soccer_france_ligue_one", "F2": "soccer_france_ligue_two",
    "N1": "soccer_netherlands_eredivisie", "B1": "soccer_belgium_first_div",
    "P1": "soccer_portugal_primeira_liga", "T1": "soccer_turkey_super_league", "G1": "soccer_greece_super_league",
    "CL": "soccer_uefa_champs_league",
}

# Names too different for fuzzy matching: The Odds API name -> football-data.co.uk name
NAME_OVERRIDES = {
    "Wolverhampton Wanderers": "Wolves", "Nottingham Forest": "Nott'm Forest", "Sheffield Wednesday": "Sheffield Weds",
    "Queens Park Rangers": "QPR", "West Bromwich Albion": "West Brom", "Athletic Bilbao": "Ath Bilbao",
    "Atlético Madrid": "Ath Madrid", "Espanyol": "Espanol", "Rayo Vallecano": "Vallecano", "Real Betis": "Betis",
    "Celta Vigo": "Celta", "Bayern Munich": "Bayern Munich", "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt", "1. FC Köln": "FC Koln", "FSV Mainz 05": "Mainz", "Hamburger SV": "Hamburg",
    "Paris Saint Germain": "Paris SG", "Paris Saint-Germain": "Paris SG", "Olympique Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon", "AS Saint-Étienne": "St Etienne", "Stade Rennais": "Rennes", "PSV Eindhoven": "PSV Eindhoven",
    "Sporting CP": "Sp Lisbon", "Sporting Braga": "Sp Braga", "Vitória SC": "Guimaraes", "Inter Milan": "Inter",
    "Manchester City": "Man City", "Manchester United": "Man United", "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham", "Leicester City": "Leicester", "Leeds United": "Leeds",
}


def odds_url(sport_key: str, regions: str) -> str:
    # h2h only: every market and region multiplies the quota cost of a request
    return f"{API_URL}/sports/{sport_key}/odds?regions={regions}&markets=h2h&oddsFormat=decimal&dateFormat=iso"


def average_h2h(event: Mapping) -> Dict:
    """Mean and best price per outcome over the bookmakers that quote all three. Empty if too few do."""
    home, away = event["home_team"], event["away_team"]
    quotes = []
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            prices = {o["name"]: o["price"] for o in market.get("outcomes", []) if o.get("price")}
            if {home, away, "Draw"} <= prices.keys():
                quotes.append((prices[home], prices["Draw"], prices[away]))
    if len(quotes) < MIN_BOOKMAKERS:
        return {}
    avg = [round(sum(q[i] for q in quotes) / len(quotes), 3) for i in range(3)]
    best = [max(q[i] for q in quotes) for i in range(3)]
    return {"avg_h": avg[0], "avg_d": avg[1], "avg_a": avg[2],
            "max_h": best[0], "max_d": best[1], "max_a": best[2], "bookmakers": len(quotes)}


def parse_events(events: Iterable[Mapping], div: str, fixtures: List[Mapping]) -> Tuple[List[Dict], List[str]]:
    """
    Matches priced events to our fixtures of one division (both teams and kickoff within 36 hours) and
    returns overlay rows plus the event team names that could not be placed.
    """
    events = list(events)
    names = {n for e in events for n in (e["home_team"], e["away_team"])}
    candidates = {t for f in fixtures for t in (f["home_team"], f["away_team"])}
    mapping = {n: NAME_OVERRIDES[n] for n in names if NAME_OVERRIDES.get(n) in candidates}
    rest = [{"id": n, "name": n} for n in names if n not in mapping]
    fuzzy, unmatched = match_teams(rest, candidates - set(mapping.values()), MATCH_THRESHOLD)
    mapping.update(fuzzy)
    by_pair = {(f["home_team"], f["away_team"]): f for f in fixtures}
    rows = []
    for e in events:
        fixture = by_pair.get((mapping.get(e["home_team"]), mapping.get(e["away_team"])))
        odds = average_h2h(e) if fixture else {}
        if not odds:
            continue
        commence = dt.datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
        if abs(commence - dt.datetime.fromisoformat(fixture["kickoff_utc"])) > KICKOFF_TOLERANCE:
            continue
        rows.append({"div": div, "home_team": fixture["home_team"], "away_team": fixture["away_team"],
                     "kickoff_utc": fixture["kickoff_utc"], **odds})
    return rows, unmatched
