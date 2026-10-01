from typing import NamedTuple


class League(NamedTuple):
    name: str
    country: str
    tier: int


# football-data.co.uk division codes. All of these share the same CSV format.
LEAGUES = {
    "E0": League("English Premier League", "England", 1),
    "E1": League("English Championship", "England", 2),
    "E2": League("English League One", "England", 3),
    "E3": League("English League Two", "England", 4),
    "EC": League("English National League", "England", 5),
    "SC0": League("Scottish Premiership", "Scotland", 1),
    "SC1": League("Scottish Championship", "Scotland", 2),
    "SC2": League("Scottish League One", "Scotland", 3),
    "SC3": League("Scottish League Two", "Scotland", 4),
    "D1": League("German Bundesliga", "Germany", 1),
    "D2": League("German 2. Bundesliga", "Germany", 2),
    "SP1": League("Spanish La Liga", "Spain", 1),
    "SP2": League("Spanish Segunda Division", "Spain", 2),
    "I1": League("Italian Serie A", "Italy", 1),
    "I2": League("Italian Serie B", "Italy", 2),
    "F1": League("French Ligue 1", "France", 1),
    "F2": League("French Ligue 2", "France", 2),
    "N1": League("Dutch Eredivisie", "Netherlands", 1),
    "B1": League("Belgian Pro League", "Belgium", 1),
    "P1": League("Portuguese Primeira Liga", "Portugal", 1),
    "T1": League("Turkish Super Lig", "Turkey", 1),
    "G1": League("Greek Super League", "Greece", 1),
}


# Competitions that mix clubs from different countries. They have no results history of their own
# here: predictions come from each club's domestic rating plus the league-strength offsets below.
class EuropeanCompetition(NamedTuple):
    name: str
    region: str


EUROPEAN_COMPETITIONS = {
    "CL": EuropeanCompetition("UEFA Champions League", "Europe"),
}

# Rough Elo-point gap between each country's top division and the English Premier League, hand-set
# from the UEFA country ranking. These are estimates, not fitted values: cross-league results are not
# in the free data, so predictions that rely on them are shown as lower confidence.
LEAGUE_STRENGTH_OFFSET = {
    "England": 0.0,
    "Spain": -10.0,
    "Germany": -30.0,
    "Italy": -30.0,
    "France": -60.0,
    "Portugal": -100.0,
    "Netherlands": -100.0,
    "Belgium": -130.0,
    "Turkey": -150.0,
    "Scotland": -160.0,
    "Greece": -170.0,
}


def strength_offset(country: str, tier: int) -> float:
    """Elo offset for a club: its country's top-flight offset, minus a tier step for lower divisions."""
    return LEAGUE_STRENGTH_OFFSET.get(country, -200.0) - 75.0 * (tier - 1)
