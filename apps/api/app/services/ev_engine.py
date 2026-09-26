from typing import Collection, List, Dict, Optional
from apps.api.app.models.schemas import BookmakerOdds, ValueBetItem, MarketType

class EvEngine:
    """
    Expected Value (+EV) calculator.
    Finds mathematical discrepancies where Model Probability > Implied Bookmaker Probability.
    """
    MIN_EV_THRESHOLD = 0.04 # 4% minimum positive expectation

    @staticmethod
    def calculate_ev(prob: float, odds: float) -> float:
        """Calculates expected value percentage."""
        return (prob * odds) - 1.0

    @classmethod
    def evaluate_match_markets(
        cls,
        home_team: str,
        away_team: str,
        probs: Dict[str, float],
        sporty_odds: BookmakerOdds,
        bet9ja_odds: Optional[BookmakerOdds] = None,
        default_bankroll: float = 10000.0,
        min_ev: Optional[float] = None,
        markets: Optional[Collection[MarketType]] = None,
    ) -> List[ValueBetItem]:
        """
        Cross-checks football markets across one or two price sources to find +EV
        opportunities. `markets` limits which markets are considered and `min_ev`
        overrides the default threshold (both come from the backtested value policy).
        """
        value_bets: List[ValueBetItem] = []
        threshold = cls.MIN_EV_THRESHOLD if min_ev is None else min_ev
        books = [b for b in (sporty_odds, bet9ja_odds) if b is not None]

        markets_to_check = [
            (MarketType.HOME_WIN, f"{home_team} to Win (1)", f"{home_team} Win", probs["prob_home_win"], "home_win"),
            (MarketType.DRAW, "Draw (X)", "Full Time Draw", probs["prob_draw"], "draw"),
            (MarketType.AWAY_WIN, f"{away_team} to Win (2)", f"{away_team} Win", probs["prob_away_win"], "away_win"),
            (MarketType.DOUBLE_CHANCE_1X, f"{home_team} or Draw (1X)", "Double Chance 1X",
             probs["prob_home_win"] + probs["prob_draw"], "double_chance_1x"),
            (MarketType.DOUBLE_CHANCE_X2, f"{away_team} or Draw (X2)", "Double Chance X2",
             probs["prob_away_win"] + probs["prob_draw"], "double_chance_x2"),
            (MarketType.OVER_1_5, "Over 1.5 Goals", "Over 1.5 Goals", probs["prob_over_1_5"], "over_1_5"),
            (MarketType.OVER_2_5, "Over 2.5 Goals", "Over 2.5 Goals", probs["prob_over_2_5"], "over_2_5"),
            (MarketType.UNDER_2_5, "Under 2.5 Goals", "Under 2.5 Goals", probs["prob_under_2_5"], "under_2_5"),
            (MarketType.BTTS_YES, "Both Teams To Score (GG)", "Both Teams Score: Yes", probs["prob_btts"], "btts_yes"),
        ]

        for m_type, m_name, selection, model_prob, odds_field in markets_to_check:
            if markets is not None and m_type not in markets:
                continue
            # Only real prices count; a market with no quoted odds is skipped
            prices = [(getattr(b, odds_field), b.bookmaker) for b in books if getattr(b, odds_field)]
            if not prices:
                continue
            best_odds, best_bookie = max(prices, key=lambda p: p[0])
            ev = cls.calculate_ev(model_prob, best_odds)
            
            if ev >= threshold:
                implied_prob = 1.0 / best_odds
                fair_odds = round(1.0 / max(0.01, model_prob), 2)
                
                # Confidence tier classification
                if ev >= 0.12:
                    tier = "High Value (Gold)"
                elif ev >= 0.07:
                    tier = "Moderate Value (Silver)"
                else:
                    tier = "Solid Edge"

                # Initial default stake estimate (1.5% to 3.5% of bankroll)
                stake_pct = min(0.04, max(0.01, ev * 0.25))
                recommended_stake = round(default_bankroll * stake_pct, -1) # rounded to nearest 10 Naira

                reasoning = (
                    f"Bookmaker implies {implied_prob*100:.1f}% chance ({best_odds:.2f} odds), "
                    f"while AI models calculate true probability at {model_prob*100:.1f}%. "
                    f"Mathematical edge: +{ev*100:.1f}%."
                )

                value_bets.append(
                    ValueBetItem(
                        market=m_type,
                        market_name=m_name,
                        selection=selection,
                        bookmaker=best_bookie,
                        market_odds=best_odds,
                        fair_odds=fair_odds,
                        model_probability=round(model_prob, 4),
                        implied_probability=round(implied_prob, 4),
                        expected_value_pct=round(ev * 100.0, 2),
                        recommended_stake_pct=round(stake_pct * 100.0, 2),
                        recommended_stake_ngn=max(100.0, recommended_stake),
                        confidence_tier=tier,
                        reasoning=reasoning
                    )
                )

        # Sort descending by Expected Value percentage
        value_bets.sort(key=lambda x: x.expected_value_pct, reverse=True)
        return value_bets
