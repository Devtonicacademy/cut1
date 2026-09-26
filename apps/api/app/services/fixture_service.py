import datetime as dt
import time
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from apps.api.app.data import db
from apps.api.app.data.football_data_uk import current_season_start
from apps.api.app.data.leagues import LEAGUES
from apps.api.app.data.ratings import (
    WINDOW_DAYS, LeagueHistory, LeagueModel, TeamRating, recent_form
)
from apps.api.app.ml.features import FeatureState, dc_features, market_features, replay_history, season_of
from apps.api.app.ml.predictor import MatchPredictor, key_factors
from apps.api.app.models.schemas import (
    BookmakerOdds, Fixture, HeadToHeadMatch, HeadToHeadStats, MarketType, PredictionDetail, Team
)
from apps.api.app.services.dixon_coles import DixonColesEngine
from apps.api.app.services.ev_engine import EvEngine
from apps.api.app.services.gemini_analyzer import GeminiAnalyzer

LAGOS_TZ = ZoneInfo("Africa/Lagos")
CACHE_TTL_SECONDS = 15 * 60
H2H_RECENT_MATCHES = 5
# Used only for a division with no history in the database yet.
FALLBACK_HOME_GOALS, FALLBACK_AWAY_GOALS = 1.45, 1.15


def describe_kickoff(kickoff_utc: dt.datetime, now_utc: dt.datetime) -> dict:
    """Formats a real kickoff time in West Africa Time (WAT) for display."""
    local = kickoff_utc.astimezone(LAGOS_TZ)
    days_ahead = (local.date() - now_utc.astimezone(LAGOS_TZ).date()).days
    if days_ahead == 0:
        day_str = "Today"
    elif days_ahead == 1:
        day_str = "Tomorrow"
    else:
        day_str = local.strftime("%a %d %b")
    t_str = local.strftime("%H:%M")
    is_upcoming = kickoff_utc > now_utc
    return {
        "kickoff": f"{day_str}, {t_str}",
        "match_date": f"{day_str} ({local.strftime('%d %b')})" if days_ahead <= 1 else local.strftime("%a, %d %b %Y"),
        "match_time": f"{t_str} WAT",
        "kickoff_timestamp": local.isoformat(),
        "is_upcoming": is_upcoming,
        "match_status": "UPCOMING" if is_upcoming else "STARTED",
    }


def _slug(name: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in name).split())


def _short_code(name: str) -> str:
    return "".join(ch for ch in name if ch.isalpha())[:3].upper() or "TBD"


@dataclass
class _Context:
    """Everything expensive to compute, shared by all bankroll sizes until it expires."""
    now: dt.datetime
    fixture_rows: List[Mapping]
    recent_history: List[Dict]
    h2h_by_pair: Dict[tuple, Sequence[Mapping]]
    league_models: Dict[str, LeagueModel]
    feature_state: Optional[FeatureState]


class FixtureService:
    """
    Serves real upcoming fixtures (football-data.co.uk snapshot stored in SQLite).
    Win/draw/loss probabilities come from the trained model when one is available
    (see apps/api/app/ml/train.py), otherwise from Dixon-Coles team ratings. Goal
    markets (over/under, BTTS, scores) always come from Dixon-Coles.
    """
    def __init__(self):
        self.dixon_coles = DixonColesEngine()
        self.gemini = GeminiAnalyzer()
        self.predictor = MatchPredictor()
        self._context_cache: Optional[_Context] = None
        self._enriched_cache: Dict[float, List[Fixture]] = {}
        self._cache_built_at = 0.0

    def refresh_fixtures(self):
        """Drops cached predictions so the next request rebuilds them from the database."""
        self._context_cache = None
        self._enriched_cache.clear()

    def _context(self) -> _Context:
        if self._context_cache and time.monotonic() - self._cache_built_at <= CACHE_TTL_SECONDS:
            return self._context_cache
        self.predictor.reload_if_changed()
        now = dt.datetime.now(dt.timezone.utc)
        today = now.date()
        season_start = dt.date(current_season_start(today), 7, 1)
        window_start = (today - dt.timedelta(days=WINDOW_DAYS)).isoformat()
        with db.connect() as conn:
            fixture_rows = [dict(r) for r in db.load_fixtures_after(conn, now.isoformat())]
            all_history = [dict(r) for r in db.load_matches_since(conn, "0000-01-01")] if self.predictor.available else None
            recent = [m for m in all_history if m["match_date"] >= window_start] if all_history is not None else \
                [dict(r) for r in db.load_matches_since(conn, window_start)]
            h2h_by_pair = {
                (r["home_team"], r["away_team"]): db.load_head_to_head(conn, r["home_team"], r["away_team"])
                for r in fixture_rows
            }

        league_models = {}
        for div in {r["div"] for r in fixture_rows}:
            league_models[div] = LeagueHistory(div, recent).fit(today, season_start) or LeagueModel(
                div=div, avg_home_goals=FALLBACK_HOME_GOALS, avg_away_goals=FALLBACK_AWAY_GOALS
            )
        self._context_cache = _Context(
            now=now,
            fixture_rows=fixture_rows,
            recent_history=recent,
            h2h_by_pair=h2h_by_pair,
            league_models=league_models,
            feature_state=replay_history(all_history) if all_history is not None else None,
        )
        self._enriched_cache.clear()
        self._cache_built_at = time.monotonic()
        return self._context_cache

    async def get_all_fixtures_with_predictions(self, bankroll_ngn: float = 10000.0) -> List[Fixture]:
        """Runs the prediction and value-detection pipeline for every upcoming fixture."""
        ctx = self._context()
        if bankroll_ngn not in self._enriched_cache:
            self._enriched_cache[bankroll_ngn] = [
                await self._build_fixture(row, ctx, bankroll_ngn) for row in ctx.fixture_rows
            ]
        return self._enriched_cache[bankroll_ngn]

    async def get_fixture_by_id(self, fixture_id: str, bankroll_ngn: float = 10000.0) -> Optional[Fixture]:
        for f in await self.get_all_fixtures_with_predictions(bankroll_ngn):
            if f.id == fixture_id:
                return f
        return None

    async def _build_fixture(self, row: Mapping, ctx: _Context, bankroll_ngn: float) -> Fixture:
        now = ctx.now
        model = ctx.league_models[row["div"]]
        league = LEAGUES[row["div"]]
        home_name, away_name = row["home_team"], row["away_team"]
        home_rating, away_rating = model.rating(home_name), model.rating(away_name)
        home_team = self._team(home_name, league.name, home_rating, recent_form(ctx.recent_history, home_name, now.date()))
        away_team = self._team(away_name, league.name, away_rating, recent_form(ctx.recent_history, away_name, now.date()))

        probs = self.dixon_coles.calculate_match_probabilities(
            home_attack=home_rating.attack,
            away_defense=away_rating.defence,
            away_attack=away_rating.attack,
            home_defense=home_rating.defence,
            league_home_advantage=1.0,  # already inside the league's home/away goal averages
            league_avg_goals_home=model.avg_home_goals,
            league_avg_goals_away=model.avg_away_goals,
        )
        source, factors = "Dixon-Coles team ratings", []
        kickoff_utc = dt.datetime.fromisoformat(row["kickoff_utc"])
        if self.predictor.available and ctx.feature_state is not None:
            match_day = kickoff_utc.date()
            features = ctx.feature_state.features(
                row["div"], season_of(match_day), home_name, away_name, match_day,
                dc_features(model, home_name, away_name),
            )
            features.update(market_features(row))
            (p_home, p_draw, p_away), variant = self.predictor.predict(features)
            probs.update(
                prob_home_win=round(p_home, 4), prob_draw=round(p_draw, 4), prob_away_win=round(p_away, 4),
                fair_odds_home=round(1 / p_home, 2), fair_odds_draw=round(1 / p_draw, 2), fair_odds_away=round(1 / p_away, 2),
            )
            source = self.predictor.describe(variant)
            factors = key_factors(features, home_name, away_name)

        fair = (probs["fair_odds_home"], probs["fair_odds_draw"], probs["fair_odds_away"])
        market_avg = self._odds(row, "avg", "Market Average", fair)
        best_price = self._odds(row, "max", "Best Price", fair)
        ev_bets = self._value_bets(home_name, away_name, probs, market_avg, bankroll_ngn)
        context = await self.gemini.analyze_matchup_context(
            home_team=home_team,
            away_team=away_team,
            league=league.name,
            ev_bets=[b.model_dump() for b in ev_bets],
            prob_home=probs["prob_home_win"],
            prob_draw=probs["prob_draw"],
            prob_away=probs["prob_away_win"],
            key_factors=factors,
        )

        timing = describe_kickoff(kickoff_utc, now)
        prediction = self._prediction(home_team, away_team, league.name, timing["kickoff"], probs, ev_bets, context)
        prediction.key_factors = factors
        prediction.prediction_source = source

        return Fixture(
            id=f"{row['div'].lower()}-{row['match_date']}-{home_team.id}-{away_team.id}",
            div=row["div"],
            home_team=home_team,
            away_team=away_team,
            league=league.name,
            venue=league.country,
            sportybet_odds=market_avg,
            bet9ja_odds=best_price,
            prediction=prediction,
            h2h=self._h2h(home_name, away_name, ctx.h2h_by_pair[(home_name, away_name)]),
            **timing,
        )

    def _value_bets(
        self, home: str, away: str, probs: Dict, market_avg: BookmakerOdds, bankroll_ngn: float
    ) -> List:
        """
        Flags value bets only when the backtest found a profitable, validated policy.
        Probabilities are blended with the market (weight chosen in training) and priced
        against the market average, exactly as the policy was tested.
        """
        policy = self.predictor.value_policy if self.predictor.available else {}
        if not policy.get("enabled") or market_avg.bookmaker != "Market Average":
            return []
        implied = [1 / market_avg.home_win, 1 / market_avg.draw, 1 / market_avg.away_win]
        market_p = [p / sum(implied) for p in implied]
        w = policy["blend_weight"]
        blended = dict(probs)
        for key, mp in zip(("prob_home_win", "prob_draw", "prob_away_win"), market_p):
            blended[key] = w * probs[key] + (1 - w) * mp
        return EvEngine.evaluate_match_markets(
            home_team=home,
            away_team=away,
            probs=blended,
            sporty_odds=market_avg,
            default_bankroll=bankroll_ngn,
            min_ev=policy["min_ev"],
            markets={MarketType.HOME_WIN, MarketType.DRAW, MarketType.AWAY_WIN},
        )

    @staticmethod
    def _team(name: str, league_name: str, rating: TeamRating, form_info: Dict) -> Team:
        return Team(
            id=_slug(name),
            name=name,
            short_code=_short_code(name),
            league=league_name,
            home_attack_strength=rating.attack,
            home_defense_weakness=rating.defence,
            away_attack_strength=rating.attack,
            away_defense_weakness=rating.defence,
            rolling_xg_created=form_info["shots_xg_for"] or 0.0,
            rolling_xg_conceded=form_info["shots_xg_against"] or 0.0,
            form=form_info["form"],
            key_injuries=[],  # no free injury feed connected yet
        )

    @staticmethod
    def _odds(row: Mapping, prefix: str, label: str, fair: tuple) -> BookmakerOdds:
        h, d, a = row[f"{prefix}_h"], row[f"{prefix}_d"], row[f"{prefix}_a"]
        if None in (h, d, a):
            h, d, a = fair
            label = "Model Fair Odds (no market price)"
        return BookmakerOdds(
            bookmaker=label,
            home_win=h,
            draw=d,
            away_win=a,
            over_2_5=row[f"{prefix}_o25"],
            under_2_5=row[f"{prefix}_u25"],
        )

    @staticmethod
    def _prediction(
        home: Team, away: Team, league: str, kickoff: str, probs: Dict, ev_bets: List, context: Dict
    ) -> PredictionDetail:
        """Picks the statistically likely winner and a safer anchor selection."""
        prob_home, prob_draw, prob_away = probs["prob_home_win"], probs["prob_draw"], probs["prob_away_win"]

        if prob_home >= prob_away and prob_home >= 0.42:
            likely_team, likely_prob = home.name, prob_home
            safe_pick = f"{home.name} Win or Draw (1X)"
            safe_odds = round(1.0 / max(0.1, prob_home + prob_draw), 2)
        elif prob_away > prob_home and prob_away >= 0.42:
            likely_team, likely_prob = away.name, prob_away
            safe_pick = f"{away.name} Win or Draw (X2)"
            safe_odds = round(1.0 / max(0.1, prob_away + prob_draw), 2)
        else:
            likely_team, likely_prob = "Draw / Even Match", max(prob_home, prob_away, prob_draw)
            if probs["prob_over_1_5"] >= 0.70:
                safe_pick, safe_odds = "Over 1.5 Goals", round(1.0 / probs["prob_over_1_5"], 2)
            else:
                safe_pick, safe_odds = "Double Chance 12", round(1.0 / max(0.1, prob_home + prob_away), 2)
        safe_odds = max(1.01, safe_odds)

        if likely_prob >= 0.70:
            confidence_tier = "Banker (70%+)"
        elif likely_prob >= 0.58:
            confidence_tier = "Strong Favorite"
        elif likely_prob >= 0.45:
            confidence_tier = "Moderate Edge"
        else:
            confidence_tier = "Evenly Contested"

        if likely_team != "Draw / Even Match":
            verdict = (
                f"Statistical analysis favors {likely_team} with a {likely_prob*100:.1f}% straight win probability "
                f"({confidence_tier}). Expected goals: {home.name} ({probs['expected_goals_home']:.2f}) vs "
                f"{away.name} ({probs['expected_goals_away']:.2f}). Safe anchor: {safe_pick} (fair odds {safe_odds:.2f})."
            )
        else:
            verdict = (
                f"Evenly matched (expected goals {probs['expected_goals_home']:.2f} vs {probs['expected_goals_away']:.2f}). "
                f"High variance matchup; safest play is {safe_pick} (fair odds {safe_odds:.2f})."
            )

        return PredictionDetail(
            home_team=home.name,
            away_team=away.name,
            league=league,
            kickoff_time=kickoff,
            expected_goals_home=probs["expected_goals_home"],
            expected_goals_away=probs["expected_goals_away"],
            prob_home_win=prob_home,
            prob_draw=prob_draw,
            prob_away_win=prob_away,
            prob_over_1_5=probs["prob_over_1_5"],
            prob_over_2_5=probs["prob_over_2_5"],
            prob_under_2_5=probs["prob_under_2_5"],
            prob_btts=probs["prob_btts"],
            fair_odds_home=probs["fair_odds_home"],
            fair_odds_draw=probs["fair_odds_draw"],
            fair_odds_away=probs["fair_odds_away"],
            top_exact_scores=probs["top_exact_scores"],
            gemini_tactical_summary=context["tactical_summary"],
            gemini_lineup_risk=context["lineup_risk"],
            value_bets=ev_bets,
            likely_winner_team=likely_team,
            likely_winner_prob=round(likely_prob, 4),
            likely_winner_confidence=confidence_tier,
            statistical_verdict=verdict,
            recommended_safe_pick=safe_pick,
            recommended_safe_odds=safe_odds,
        )

    @staticmethod
    def _h2h(home: str, away: str, rows: Sequence[Mapping]) -> HeadToHeadStats:
        """Real head-to-head record from the database, counted from the upcoming home team's perspective."""
        if not rows:
            return HeadToHeadStats(
                total_meetings=0, home_team_wins=0, draws=0, away_team_wins=0,
                home_goals_total=0, away_goals_total=0,
                summary=f"No league meetings between {home} and {away} in our database.",
            )

        wins = draws = losses = goals_home = goals_away = 0
        for r in rows:
            gf, ga = (r["fthg"], r["ftag"]) if r["home_team"] == home else (r["ftag"], r["fthg"])
            goals_home += gf
            goals_away += ga
            if gf > ga:
                wins += 1
            elif gf == ga:
                draws += 1
            else:
                losses += 1

        last_matches = []
        for r in rows[:H2H_RECENT_MATCHES]:
            h, a = r["fthg"], r["ftag"]
            last_matches.append(HeadToHeadMatch(
                date=dt.date.fromisoformat(r["match_date"]).strftime("%d %b %Y"),
                competition=LEAGUES[r["div"]].name if r["div"] in LEAGUES else r["div"],
                home_team=r["home_team"],
                away_team=r["away_team"],
                home_score=h,
                away_score=a,
                winner="home" if h > a else ("draw" if h == a else "away"),
            ))

        since = dt.date.fromisoformat(rows[-1]["match_date"]).year
        n = len(rows)
        return HeadToHeadStats(
            total_meetings=n,
            home_team_wins=wins,
            draws=draws,
            away_team_wins=losses,
            home_goals_total=goals_home,
            away_goals_total=goals_away,
            last_matches=last_matches,
            summary=(
                f"Since {since}: {home} {wins}W {draws}D {losses}L against {away} in {n} league meeting"
                f"{'s' if n != 1 else ''}, averaging {(goals_home + goals_away) / n:.1f} goals per game."
            ),
        )
