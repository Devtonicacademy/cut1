"""
National-team results (Mart Jürisoo's open international results dataset, 1872 to today, no key needed)
and an Elo rating built from them, in the style of eloratings.net. Used for competitions between
countries (Nations League, AFCON, Asian Cup, friendlies), which the club-league model cannot rate.
"""
import csv
import io
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
ELO_START = 1500.0
ELO_HOME_ADVANTAGE = 100.0
# Share of evenly matched internationals that end level. Chosen by walk-forward testing on 4,671
# matches from 2022 on (log loss 0.879 vs 1.051 for always predicting the base rates).
DRAW_RATE = 0.32


def parse_results_csv(text: str) -> List[Dict]:
    """Played matches only: rows without a score (not yet played) are skipped."""
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        try:
            hg, ag = int(r["home_score"]), int(r["away_score"])
        except (TypeError, ValueError):
            continue
        rows.append({
            "match_date": r["date"], "home_team": r["home_team"].strip(), "away_team": r["away_team"].strip(),
            "fthg": hg, "ftag": ag, "tournament": r["tournament"].strip(),
            "neutral": 1 if r["neutral"].strip().upper() == "TRUE" else 0,
        })
    return rows


def k_factor(tournament: str) -> float:
    """How much a result moves ratings: World Cup finals most, friendlies least."""
    t = tournament.lower()
    if t == "fifa world cup":
        return 60.0
    if "qualification" in t:
        return 40.0
    if t == "friendly":
        return 20.0
    if t in ("uefa euro", "copa américa", "african cup of nations", "afc asian cup", "gold cup",
             "confederations cup", "uefa nations league", "concacaf nations league"):
        return 50.0
    return 30.0


def expected(diff: float) -> float:
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


@dataclass
class NationalRatings:
    elo: Dict[str, float] = field(default_factory=dict)
    games: Dict[str, int] = field(default_factory=dict)
    last_played: Dict[str, str] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.elo.get(team, ELO_START)

    def gap(self, home: str, away: str, neutral: bool) -> float:
        """Home minus away Elo, including home advantage unless the venue is neutral."""
        return self.rating(home) - self.rating(away) + (0.0 if neutral else ELO_HOME_ADVANTAGE)

    def update(self, m: Mapping) -> None:
        home, away = m["home_team"], m["away_team"]
        hg, ag = m["fthg"], m["ftag"]
        result = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        margin = abs(hg - ag)
        multiplier = 1.0 if margin <= 1 else (1.5 if margin == 2 else (11 + margin) / 8)
        delta = k_factor(m["tournament"]) * multiplier * (result - expected(self.gap(home, away, bool(m["neutral"]))))
        self.elo[home] = self.rating(home) + delta
        self.elo[away] = self.rating(away) - delta
        for team in (home, away):
            self.games[team] = self.games.get(team, 0) + 1
            self.last_played[team] = m["match_date"]


def replay(matches: Iterable[Mapping]) -> NationalRatings:
    ratings = NationalRatings()
    for m in sorted(matches, key=lambda m: m["match_date"]):
        ratings.update(m)
    return ratings


def outcome_probs(diff: float, draw_rate: float = DRAW_RATE) -> Tuple[float, float, float]:
    """(home, draw, away) from an Elo gap: Elo expectation is win + half the draw; draws thin out as gaps grow."""
    e = expected(diff)
    draw = draw_rate * (1 - (2 * e - 1) ** 2)
    return e - draw / 2, draw, 1 - e - draw / 2
