"""
Match features for the prediction model, built strictly from information available
before kickoff. One `FeatureState` replays history in date order: features for a
match are read *before* its result is applied, so training rows never peek at the
outcome. Live fixtures are featurised by the same code after replaying all history.
"""
import datetime as dt
from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import groupby
from typing import Dict, List, Mapping, Optional, Tuple

from apps.api.app.data.football_data_uk import current_season_start, season_code
from apps.api.app.data.leagues import LEAGUES
from apps.api.app.data.ratings import LeagueHistory, LeagueModel
from apps.api.app.services.dixon_coles import DixonColesEngine

ELO_START = 1500.0
ELO_TIER_STEP = 75.0  # new teams in lower tiers start weaker
ELO_K = 20.0
ELO_HOME_ADVANTAGE = 65.0
EWM_ALPHA = 1 - 0.5 ** (1 / 5)  # recent-form averages with a half-life of 5 matches
REST_CAP_DAYS = 21
EXPERIENCE_CAP = 38
H2H_MEMORY = 6

FEATURE_NAMES = [
    "elo_diff", "elo_exp_home",
    "dc_p_home", "dc_p_draw", "dc_p_away", "dc_goals_home", "dc_goals_away",
    "league_home_goals", "league_away_goals", "tier",
    "home_form_pts", "away_form_pts",
    "home_gf", "home_ga", "away_gf", "away_ga",
    "home_sot_for", "home_sot_against", "away_sot_for", "away_sot_against",
    "home_rest_days", "away_rest_days", "home_matches_14d", "away_matches_14d",
    "home_experience", "away_experience",
    "home_season_ppg", "away_season_ppg", "home_table_pct", "away_table_pct", "season_games",
    "h2h_n", "h2h_ppg_home", "h2h_gd_home",
]
# Bookmaker consensus (pre-match average odds, margin removed). Used by the "with_market"
# model when a fixture has odds; fixtures without odds use the football-only model.
MARKET_FEATURE_NAMES = ["mkt_p_home", "mkt_p_draw", "mkt_p_away", "mkt_p_over25"]
FEATURE_SETS = {
    "with_market": FEATURE_NAMES + MARKET_FEATURE_NAMES,
    "football_only": FEATURE_NAMES,
}

_dc_engine = DixonColesEngine()


def elo_expected(diff: float) -> float:
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def season_of(day: dt.date) -> str:
    return season_code(current_season_start(day))


def season_start_date(season: str) -> dt.date:
    return dt.date(2000 + int(season[:2]), 7, 1)


def dc_features(model: Optional[LeagueModel], home: str, away: str) -> Dict[str, Optional[float]]:
    """Dixon-Coles probabilities from the league's fitted ratings (None if the league has no history)."""
    if model is None:
        return {k: None for k in ("dc_p_home", "dc_p_draw", "dc_p_away", "dc_goals_home",
                                  "dc_goals_away", "league_home_goals", "league_away_goals")}
    h, a = model.rating(home), model.rating(away)
    p = _dc_engine.calculate_match_probabilities(
        h.attack, a.defence, a.attack, h.defence, 1.0, model.avg_home_goals, model.avg_away_goals
    )
    return {
        "dc_p_home": p["prob_home_win"], "dc_p_draw": p["prob_draw"], "dc_p_away": p["prob_away_win"],
        "dc_goals_home": p["expected_goals_home"], "dc_goals_away": p["expected_goals_away"],
        "league_home_goals": model.avg_home_goals, "league_away_goals": model.avg_away_goals,
    }


def market_features(row: Mapping) -> Dict[str, Optional[float]]:
    """Margin-free bookmaker probabilities from a match/fixture row's average odds."""
    f: Dict[str, Optional[float]] = {k: None for k in MARKET_FEATURE_NAMES}
    odds = [row.get("avg_h"), row.get("avg_d"), row.get("avg_a")]
    if all(odds):
        inv = [1.0 / o for o in odds]
        f["mkt_p_home"], f["mkt_p_draw"], f["mkt_p_away"] = (x / sum(inv) for x in inv)
    over, under = row.get("avg_o25"), row.get("avg_u25")
    if over and under:
        f["mkt_p_over25"] = (1.0 / over) / (1.0 / over + 1.0 / under)
    return f


def has_market(features: Mapping) -> bool:
    return all(features.get(k) is not None for k in ("mkt_p_home", "mkt_p_draw", "mkt_p_away"))


@dataclass
class TeamState:
    elo: float
    matches: int = 0
    last_day: Optional[int] = None
    recent_days: deque = field(default_factory=lambda: deque(maxlen=10))
    ewm: Dict[str, float] = field(default_factory=dict)

    def ewm_update(self, key: str, value: Optional[float]) -> None:
        if value is None:
            return
        prev = self.ewm.get(key)
        self.ewm[key] = value if prev is None else prev + EWM_ALPHA * (value - prev)


class FeatureState:
    def __init__(self):
        self.teams: Dict[Tuple[str, str], TeamState] = {}
        # (div, season) -> team -> [points, goal_diff, goals_for, played]
        self.tables: Dict[Tuple[str, str], Dict[str, List[int]]] = defaultdict(dict)
        # frozenset(team keys) -> recent meetings as (home_key, home_goals, away_goals)
        self.h2h: Dict[frozenset, deque] = defaultdict(lambda: deque(maxlen=H2H_MEMORY))

    def _team(self, div: str, name: str) -> TeamState:
        key = (LEAGUES[div].country, name)
        if key not in self.teams:
            self.teams[key] = TeamState(elo=ELO_START - ELO_TIER_STEP * (LEAGUES[div].tier - 1))
        return self.teams[key]

    def features(self, div: str, season: str, home: str, away: str, day: dt.date, dc: Dict) -> Dict:
        h, a = self._team(div, home), self._team(div, away)
        f: Dict[str, Optional[float]] = {
            "elo_diff": h.elo - a.elo,
            "elo_exp_home": elo_expected(h.elo - a.elo + ELO_HOME_ADVANTAGE),
            "tier": LEAGUES[div].tier,
            **dc,
        }
        table = self.tables[(div, season)]
        ranked = sorted(table, key=lambda t: (table[t][0], table[t][1], table[t][2]), reverse=True)
        ordinal = day.toordinal()
        for side, name, t in (("home", home, h), ("away", away, a)):
            f[f"{side}_form_pts"] = t.ewm.get("pts")
            f[f"{side}_gf"] = t.ewm.get("gf")
            f[f"{side}_ga"] = t.ewm.get("ga")
            f[f"{side}_sot_for"] = t.ewm.get("sot_for")
            f[f"{side}_sot_against"] = t.ewm.get("sot_against")
            f[f"{side}_rest_days"] = min(REST_CAP_DAYS, ordinal - t.last_day) if t.last_day else REST_CAP_DAYS
            f[f"{side}_matches_14d"] = sum(1 for d in t.recent_days if ordinal - d <= 14)
            f[f"{side}_experience"] = min(EXPERIENCE_CAP, t.matches)
            row = table.get(name)
            f[f"{side}_season_ppg"] = row[0] / row[3] if row else None
            f[f"{side}_table_pct"] = (ranked.index(name) + 1) / len(ranked) if row else None
        f["season_games"] = min(table.get(home, [0, 0, 0, 0])[3], table.get(away, [0, 0, 0, 0])[3])

        home_key, away_key = (LEAGUES[div].country, home), (LEAGUES[div].country, away)
        meetings = self.h2h.get(frozenset((home_key, away_key)), ())
        f["h2h_n"] = len(meetings)
        if meetings:
            pts = gd = 0
            for venue_home, hg, ag in meetings:
                gf, ga = (hg, ag) if venue_home == home_key else (ag, hg)
                pts += 3 if gf > ga else (1 if gf == ga else 0)
                gd += gf - ga
            f["h2h_ppg_home"] = pts / len(meetings)
            f["h2h_gd_home"] = gd / len(meetings)
        else:
            f["h2h_ppg_home"] = f["h2h_gd_home"] = None
        return f

    def update(self, m: Mapping) -> None:
        div, home, away = m["div"], m["home_team"], m["away_team"]
        hg, ag = m["fthg"], m["ftag"]
        h, a = self._team(div, home), self._team(div, away)

        result = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        margin = abs(hg - ag)
        multiplier = 1.0 if margin <= 1 else (1.5 if margin == 2 else (11 + margin) / 8)
        delta = ELO_K * multiplier * (result - elo_expected(h.elo - a.elo + ELO_HOME_ADVANTAGE))
        h.elo += delta
        a.elo -= delta

        ordinal = dt.date.fromisoformat(m["match_date"]).toordinal()
        for t, gf, ga, sot_for, sot_against in ((h, hg, ag, m.get("hst"), m.get("ast")),
                                                (a, ag, hg, m.get("ast"), m.get("hst"))):
            t.ewm_update("pts", 3 if gf > ga else (1 if gf == ga else 0))
            t.ewm_update("gf", gf)
            t.ewm_update("ga", ga)
            t.ewm_update("sot_for", sot_for)
            t.ewm_update("sot_against", sot_against)
            t.matches += 1
            t.last_day = ordinal
            t.recent_days.append(ordinal)

        table = self.tables[(div, m.get("season") or season_of(dt.date.fromisoformat(m["match_date"])))]
        for name, gf, ga in ((home, hg, ag), (away, ag, hg)):
            row = table.setdefault(name, [0, 0, 0, 0])
            row[0] += 3 if gf > ga else (1 if gf == ga else 0)
            row[1] += gf - ga
            row[2] += gf
            row[3] += 1

        country = LEAGUES[div].country
        self.h2h[frozenset(((country, home), (country, away)))].append(((country, home), hg, ag))


def outcome(m: Mapping) -> int:
    """0 = home win, 1 = draw, 2 = away win."""
    return 0 if m["fthg"] > m["ftag"] else (1 if m["fthg"] == m["ftag"] else 2)


def build_training_rows(matches: List[Mapping]) -> Tuple[List[Dict], List[int], List[Mapping]]:
    """
    Replays history in date order and returns (features, outcomes, matches).
    Dixon-Coles ratings are refitted weekly per league from data before that week.
    """
    matches = sorted((m for m in matches if m["div"] in LEAGUES), key=lambda m: (m["match_date"], m["div"]))
    histories = {div: LeagueHistory(div, matches) for div in {m["div"] for m in matches}}
    dc_models: Dict[Tuple[str, dt.date], Optional[LeagueModel]] = {}
    state = FeatureState()
    rows, labels, meta = [], [], []

    for match_date, day_matches in groupby(matches, key=lambda m: m["match_date"]):
        day_matches = list(day_matches)
        day = dt.date.fromisoformat(match_date)
        monday = day - dt.timedelta(days=day.weekday())
        for m in day_matches:
            key = (m["div"], monday)
            if key not in dc_models:
                dc_models[key] = histories[m["div"]].fit(monday, season_start_date(m["season"]))
            dc = dc_features(dc_models[key], m["home_team"], m["away_team"])
            row = state.features(m["div"], m["season"], m["home_team"], m["away_team"], day, dc)
            row.update(market_features(m))
            rows.append(row)
            labels.append(outcome(m))
            meta.append(m)
        for m in day_matches:  # results are applied only after the whole day is featurised
            state.update(m)
    return rows, labels, meta


def replay_history(matches: List[Mapping]) -> FeatureState:
    """State after every known result, ready to featurise upcoming fixtures."""
    state = FeatureState()
    for m in sorted((m for m in matches if m["div"] in LEAGUES), key=lambda m: (m["match_date"], m["div"])):
        state.update(m)
    return state
