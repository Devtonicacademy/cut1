"""
Accumulator builder.

Every leg is the model's predicted winner (straight or double chance) priced at the
real market-average odds, and the ticket states the honest combined chance that
every leg wins. Fixtures without market odds are never used, and slips are capped
at MAX_LEGS because each extra leg multiplies the bookmaker's margin.
"""
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from apps.api.app.models.schemas import AccumulatorLeg, AccumulatorResponse, Fixture, RiskLevel

MAX_LEGS = 10
MIN_LEG_PROBABILITY = 0.50
SUGGESTED_MAX_STAKE_PCT = 0.01  # never suggest more than 1% of bankroll on one accumulator
MIN_STAKE_NGN = 100.0
STRATEGIES = {
    "safest": "Double chance on each predicted winner",
    "straight_win": "Each predicted winner to win outright",
}
_LEGACY_STRATEGIES = {"safest_winners": "safest", "balanced_value": "safest"}


@dataclass
class _Candidate:
    fixture: Fixture
    market: str
    odds: float
    prob: float


class AccasOptimizer:

    @classmethod
    def build_smart_accumulator(
        cls,
        fixtures: List[Fixture],
        target_odds: float = 2.0,
        risk_level: RiskLevel = RiskLevel.CONSERVATIVE,
        bankroll_ngn: float = 10000.0,
        max_legs: int = 4,
        target_legs: Optional[int] = None,
        strategy: str = "safest",
        selected_leagues: Optional[List[str]] = None,
    ) -> AccumulatorResponse:
        """
        With `target_legs`, picks that many of the most likely legs spread across leagues.
        Otherwise adds the most likely legs until the total odds reach `target_odds`.
        """
        strategy = _LEGACY_STRATEGIES.get(strategy, strategy)
        if strategy not in STRATEGIES:
            strategy = "safest"
        fixtures = [f for f in fixtures if f.is_upcoming]
        if selected_leagues and "All" not in selected_leagues:
            chosen = [f for f in fixtures if any(lg.lower() in f.league.lower() for lg in selected_leagues)]
            fixtures = chosen if len(chosen) >= 2 else fixtures

        candidates = [c for c in (cls._candidate(f, strategy) for f in fixtures) if c]
        candidates.sort(key=lambda c: c.prob, reverse=True)

        if target_legs:
            legs = cls._spread_across_leagues(candidates, min(target_legs, MAX_LEGS))
        else:
            legs = []
            for c in candidates:
                if len(legs) >= min(max_legs, MAX_LEGS) or (len(legs) >= 2 and math.prod(l.odds for l in legs) >= target_odds * 0.9):
                    break
                legs.append(c)
        return cls._ticket(legs, strategy, bankroll_ngn, requested=target_legs)

    @staticmethod
    def _candidate(f: Fixture, strategy: str) -> Optional[_Candidate]:
        p = f.prediction
        if not p or f.sportybet_odds.bookmaker != "Market Average":
            return None  # no real market price to quote
        if p.likely_winner_team == f.home_team.name:
            win_prob, win_odds, dc_label = p.prob_home_win, f.sportybet_odds.home_win, "1X"
        elif p.likely_winner_team == f.away_team.name:
            win_prob, win_odds, dc_label = p.prob_away_win, f.sportybet_odds.away_win, "X2"
        else:
            return None  # no clear favourite

        if strategy == "straight_win":
            market, odds, prob = f"{p.likely_winner_team} to Win", win_odds, win_prob
        else:
            # Double-chance price estimated from the 1X2 market (bookmakers price it close to this)
            odds = round(1 / (1 / win_odds + 1 / f.sportybet_odds.draw), 2)
            market, prob = f"{p.likely_winner_team} or Draw ({dc_label})", win_prob + p.prob_draw
        if prob < MIN_LEG_PROBABILITY or odds <= 1.0:
            return None
        return _Candidate(fixture=f, market=market, odds=odds, prob=prob)

    @staticmethod
    def _spread_across_leagues(candidates: List[_Candidate], count: int) -> List[_Candidate]:
        """Round-robin over leagues (each league's most likely legs first) for a varied slip."""
        by_league: Dict[str, List[_Candidate]] = defaultdict(list)
        for c in candidates:
            by_league[c.fixture.league].append(c)
        legs: List[_Candidate] = []
        depth = 0
        while len(legs) < count and any(depth < len(v) for v in by_league.values()):
            layer = sorted((v[depth] for v in by_league.values() if depth < len(v)), key=lambda c: c.prob, reverse=True)
            legs.extend(layer[: count - len(legs)])
            depth += 1
        return legs

    @staticmethod
    def _ticket(legs: List[_Candidate], strategy: str, bankroll_ngn: float, requested: Optional[int]) -> AccumulatorResponse:
        n = len(legs)
        total_odds = round(math.prod(c.odds for c in legs), 2) if legs else 1.0
        win_prob = math.prod(c.prob for c in legs) if legs else 0.0
        stake = max(MIN_STAKE_NGN, round(bankroll_ngn * SUGGESTED_MAX_STAKE_PCT / 50) * 50)

        acc_legs = [
            AccumulatorLeg(
                fixture_id=c.fixture.id,
                match_name=f"{c.fixture.home_team.name} vs {c.fixture.away_team.name}",
                market=c.market,
                odds=c.odds,
                model_probability=round(c.prob, 4),
                ev_pct=round((c.prob * c.odds - 1) * 100, 1),
                risk_assessment="Strong" if c.prob >= 0.70 else ("Moderate" if c.prob >= 0.58 else "Open"),
                league=c.fixture.league,
                likely_winner=c.fixture.prediction.likely_winner_team,
                bookmaker_search_text=f"{c.fixture.home_team.name} vs {c.fixture.away_team.name}: {c.market}",
                kickoff=c.fixture.kickoff,
            )
            for c in legs
        ]

        if n:
            warning = f"All {n} picks must win. The model's estimated chance of that is {win_prob:.1%}"
            warning += f" (about 1 in {round(1 / win_prob)})." if win_prob > 0 else "."
            if n >= 4:
                warning += " Every extra game multiplies the bookmaker's margin, so shorter slips lose less often."
        else:
            warning = "No upcoming matches with market prices and a clear favourite right now."
        notes = []
        if requested and requested > MAX_LEGS:
            notes.append(f"Slips are capped at {MAX_LEGS} games.")
        if requested and n < min(requested, MAX_LEGS):
            notes.append(f"Only {n} upcoming matches have market prices and a clear favourite.")
        if strategy == "safest":
            notes.append("Double-chance odds are estimated from the win/draw market; check the exact price with your bookmaker.")

        search_list = "\n".join(f"{i}. [{l.league}] {l.bookmaker_search_text} (@ {l.odds:.2f})" for i, l in enumerate(acc_legs, 1))
        share = f"*LivelyBorg {n}-pick slip* | Total odds {total_odds:.2f}\n"
        share += "".join(f"{i}. {l.match_name}: *{l.market}* ({l.odds:.2f}, {l.model_probability:.0%})\n"
                         for i, l in enumerate(acc_legs, 1))
        share += f"\nChance all win (model estimate): {win_prob:.1%}\nPredictions, not guarantees. 18+ only. Bet responsibly."

        return AccumulatorResponse(
            ticket_type=f"{n}-Pick Slip: {STRATEGIES[strategy]}",
            total_odds=total_odds,
            win_probability=round(win_prob, 6),
            recommended_stake_ngn=stake,
            potential_payout_ngn=round(stake * total_odds, 2),
            legs=acc_legs,
            cut_1_insured=False,
            cut_1_warning=warning,
            whatsapp_share_text=share,
            recommended_game_count_note=" ".join(notes) or None,
            leagues_covered=sorted({l.league for l in acc_legs if l.league}),
            match_search_list=search_list,
            is_upcoming_verified=True,
        )
