"""
Team strength ratings learned from real results.

Each team gets an attack and defence multiplier relative to its league average,
fitted with an opponent-adjusted Poisson model (iterative proportional fitting):
    expected home goals = league_home_avg * attack[home] * defence[away]
    expected away goals = league_away_avg * attack[away] * defence[home]
Recent matches count more (exponential decay), and every team is shrunk toward a
prior so a handful of games cannot produce extreme ratings. Newly promoted teams
start from a weaker prior.

This is the Phase 1 baseline; Phase 2 layers a trained ML model on top.
"""
import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional

import numpy as np

HALF_LIFE_DAYS = 180.0
WINDOW_DAYS = 730
PRIOR_WEIGHT = 4.0  # pseudo-goals pulling each rating toward its prior
PROMOTED_PRIOR = (0.85, 1.15)  # (attack, defence) for teams new to the division
UNKNOWN_TEAM = (0.90, 1.10)
ITERATIONS = 50
FORM_LENGTH = 5
SHOTS_WINDOW = 6
# Long-run conversion rate across the top European leagues (~30% of shots on target are goals).
GOALS_PER_SHOT_ON_TARGET = 0.30


@dataclass
class TeamRating:
    name: str
    attack: float
    defence: float
    weighted_matches: float
    form: str = ""
    shots_xg_for: Optional[float] = None
    shots_xg_against: Optional[float] = None


@dataclass
class LeagueModel:
    div: str
    avg_home_goals: float
    avg_away_goals: float
    ratings: Dict[str, TeamRating] = field(default_factory=dict)

    def rating(self, team: str) -> TeamRating:
        if team in self.ratings:
            return self.ratings[team]
        attack, defence = UNKNOWN_TEAM
        return TeamRating(name=team, attack=attack, defence=defence, weighted_matches=0.0)

    def expected_goals(self, home: str, away: str) -> tuple:
        h, a = self.rating(home), self.rating(away)
        return (
            self.avg_home_goals * h.attack * a.defence,
            self.avg_away_goals * a.attack * h.defence,
        )


def _date(row: Mapping) -> dt.date:
    return dt.date.fromisoformat(row["match_date"])


class LeagueHistory:
    """
    One division's results as numpy arrays, sorted by date, so ratings can be refitted
    quickly at any point in time (the training pipeline refits thousands of times).
    """
    def __init__(self, div: str, matches: Iterable[Mapping]):
        rows = sorted((m for m in matches if m["div"] == div), key=lambda m: m["match_date"])
        self.div = div
        self.teams = sorted({m["home_team"] for m in rows} | {m["away_team"] for m in rows})
        index = {t: i for i, t in enumerate(self.teams)}
        self.days = np.array([_date(m).toordinal() for m in rows], dtype=np.int64)
        self.home = np.array([index[m["home_team"]] for m in rows], dtype=np.int64)
        self.away = np.array([index[m["away_team"]] for m in rows], dtype=np.int64)
        self.home_goals = np.array([m["fthg"] for m in rows], dtype=float)
        self.away_goals = np.array([m["ftag"] for m in rows], dtype=float)

    def fit(self, as_of: dt.date, season_start: dt.date) -> Optional[LeagueModel]:
        """Fits ratings from matches in the window before `as_of`."""
        lo = np.searchsorted(self.days, (as_of - dt.timedelta(days=WINDOW_DAYS)).toordinal(), side="left")
        hi = np.searchsorted(self.days, as_of.toordinal(), side="left")
        if hi <= lo:
            return None
        n = len(self.teams)
        h, a = self.home[lo:hi], self.away[lo:hi]
        hg, ag = self.home_goals[lo:hi], self.away_goals[lo:hi]
        w = np.exp(-(math.log(2) / HALF_LIFE_DAYS) * (as_of.toordinal() - self.days[lo:hi]))
        mu_home = float((w * hg).sum() / w.sum())
        mu_away = float((w * ag).sum() / w.sum())

        played = np.bincount(h, w, n) + np.bincount(a, w, n)
        present = played > 0
        before = self.days[lo:hi] < season_start.toordinal()
        seen_before = np.zeros(n, dtype=bool)
        seen_before[h[before]] = True
        seen_before[a[before]] = True
        prior_att, prior_def = np.ones(n), np.ones(n)
        if seen_before.any():
            promoted = present & ~seen_before
            prior_att[promoted], prior_def[promoted] = PROMOTED_PRIOR

        scored = np.bincount(h, w * hg, n) + np.bincount(a, w * ag, n)
        conceded = np.bincount(h, w * ag, n) + np.bincount(a, w * hg, n)
        attack, defence = np.ones(n), np.ones(n)
        for _ in range(ITERATIONS):
            exp_scored = np.bincount(h, w * mu_home * defence[a], n) + np.bincount(a, w * mu_away * defence[h], n)
            exp_conceded = np.bincount(h, w * mu_away * attack[a], n) + np.bincount(a, w * mu_home * attack[h], n)
            new_attack = (scored + PRIOR_WEIGHT * prior_att) / (exp_scored + PRIOR_WEIGHT)
            new_defence = (conceded + PRIOR_WEIGHT * prior_def) / (exp_conceded + PRIOR_WEIGHT)
            attack = new_attack / new_attack[present].mean()
            defence = new_defence / new_defence[present].mean()

        ratings = {
            self.teams[i]: TeamRating(
                name=self.teams[i],
                attack=round(float(attack[i]), 4),
                defence=round(float(defence[i]), 4),
                weighted_matches=round(float(played[i]), 2),
            )
            for i in np.flatnonzero(present)
        }
        return LeagueModel(div=self.div, avg_home_goals=mu_home, avg_away_goals=mu_away, ratings=ratings)


def build_league_model(
    div: str,
    matches: Iterable[Mapping],
    as_of: dt.date,
    season_start: dt.date,
) -> Optional[LeagueModel]:
    """Fits ratings for one division using matches played before `as_of`."""
    return LeagueHistory(div, matches).fit(as_of, season_start)

def recent_form(matches: List[Mapping], team: str, as_of: dt.date) -> Dict:
    """
    Last results (oldest -> newest, across all divisions) and a shots-based
    expected-goals estimate: shots on target x the league-wide goals-per-shot-on-target rate.
    `matches` must be sorted by date ascending.
    """
    played = [m for m in matches if _date(m) < as_of and team in (m["home_team"], m["away_team"])]
    form = ""
    for m in played[-FORM_LENGTH:]:
        is_home = m["home_team"] == team
        gf, ga = (m["fthg"], m["ftag"]) if is_home else (m["ftag"], m["fthg"])
        form += "W" if gf > ga else ("D" if gf == ga else "L")

    recent = played[-SHOTS_WINDOW:]
    xg_for = xg_against = None
    with_shots = [m for m in recent if m.get("hst") is not None and m.get("ast") is not None]
    if with_shots:
        sot_for = sot_against = 0
        for m in with_shots:
            is_home = m["home_team"] == team
            sot_for += m["hst"] if is_home else m["ast"]
            sot_against += m["ast"] if is_home else m["hst"]
        n = len(with_shots)
        xg_for = round(sot_for / n * GOALS_PER_SHOT_ON_TARGET, 2)
        xg_against = round(sot_against / n * GOALS_PER_SHOT_ON_TARGET, 2)
    return {"form": form, "shots_xg_for": xg_for, "shots_xg_against": xg_against}
