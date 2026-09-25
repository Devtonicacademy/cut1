from typing import List, Dict
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
        bet9ja_odds: BookmakerOdds,
        default_bankroll: float = 10000.0
    ) -> List[ValueBetItem]:
        """
        Cross-checks all standard football markets across SportyBet and Bet9ja
        to find all +EV value opportunities.
        """
        value_bets: List[ValueBetItem] = []

        markets_to_check = [
            (
                MarketType.HOME_WIN,
                f"{home_team} to Win (1)",
                f"{home_team} Win",
                probs["prob_home_win"],
                sporty_odds.home_win,
                bet9ja_odds.home_win
            ),
            (
                MarketType.DRAW,
                f"Draw (X)",
                "Full Time Draw",
                probs["prob_draw"],
                sporty_odds.draw,
                bet9ja_odds.draw
            ),
            (
                MarketType.AWAY_WIN,
                f"{away_team} to Win (2)",
                f"{away_team} Win",
                probs["prob_away_win"],
                sporty_odds.away_win,
                bet9ja_odds.away_win
            ),
            (
                MarketType.DOUBLE_CHANCE_1X,
                f"{home_team} or Draw (1X)",
                "Double Chance 1X",
                probs["prob_home_win"] + probs["prob_draw"],
                sporty_odds.double_chance_1x or 1.25,
                bet9ja_odds.double_chance_1x or 1.24
            ),
            (
                MarketType.DOUBLE_CHANCE_X2,
                f"{away_team} or Draw (X2)",
                "Double Chance X2",
                probs["prob_away_win"] + probs["prob_draw"],
                sporty_odds.double_chance_x2 or 1.45,
                bet9ja_odds.double_chance_x2 or 1.43
            ),
            (
                MarketType.OVER_1_5,
                "Over 1.5 Goals",
                "Over 1.5 Goals",
                probs["prob_over_1_5"],
                sporty_odds.over_1_5 or 1.30,
                bet9ja_odds.over_1_5 or 1.28
            ),
            (
                MarketType.OVER_2_5,
                "Over 2.5 Goals",
                "Over 2.5 Goals",
                probs["prob_over_2_5"],
                sporty_odds.over_2_5 or 1.95,
                bet9ja_odds.over_2_5 or 1.92
            ),
            (
                MarketType.UNDER_2_5,
                "Under 2.5 Goals",
                "Under 2.5 Goals",
                probs["prob_under_2_5"],
                sporty_odds.under_2_5 or 1.88,
                bet9ja_odds.under_2_5 or 1.90
            ),
            (
                MarketType.BTTS_YES,
                "Both Teams To Score (GG)",
                "Both Teams Score: Yes",
                probs["prob_btts"],
                sporty_odds.btts_yes or 1.85,
                bet9ja_odds.btts_yes or 1.82
            ),
        ]

        for m_type, m_name, selection, model_prob, s_odds, b_odds in markets_to_check:
            # Pick the best available market price
            best_odds = max(s_odds, b_odds)
            best_bookie = "SportyBet" if s_odds >= b_odds else "Bet9ja"
            
            ev = cls.calculate_ev(model_prob, best_odds)
            
            if ev >= cls.MIN_EV_THRESHOLD:
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
