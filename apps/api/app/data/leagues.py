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
