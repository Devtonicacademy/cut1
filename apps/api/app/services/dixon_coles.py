import math
from typing import Dict, Tuple

class DixonColesEngine:
    """
    Implements Dixon-Coles modified bivariate Poisson model for football match prediction.
    Accounts for low-score dependence (0-0, 1-0, 0-1, 1-1) and league home advantage.
    """
    def __init__(self, rho: float = -0.11):
        self.rho = rho

    def _tau(self, x: int, y: int, lambda_: float, mu: float) -> float:
        """Low-scoring match correlation factor from Dixon & Coles (1997)."""
        if x == 0 and y == 0:
            return 1.0 - (lambda_ * mu * self.rho)
        elif x == 0 and y == 1:
            return 1.0 + (lambda_ * self.rho)
        elif x == 1 and y == 0:
            return 1.0 + (mu * self.rho)
        elif x == 1 and y == 1:
            return 1.0 - self.rho
        else:
            return 1.0

    def _poisson_pmf(self, k: int, lambda_: float) -> float:
        """Calculates Poisson probability mass function."""
        return (math.pow(lambda_, k) * math.exp(-lambda_)) / math.factorial(k)

    def calculate_match_probabilities(
        self,
        home_attack: float,
        away_defense: float,
        away_attack: float,
        home_defense: float,
        league_home_advantage: float = 1.25,
        league_avg_goals_home: float = 1.45,
        league_avg_goals_away: float = 1.15,
        max_goals: int = 7
    ) -> Dict[str, any]:
        """
        Calculates expected goals and full probability distribution over match outcomes.
        """
        # Expected goals (lambda for home, mu for away)
        lambda_ = home_attack * away_defense * league_home_advantage * league_avg_goals_home
        mu = away_attack * home_defense * league_avg_goals_away

        # Bound lambda and mu to sensible football bounds (0.3 to 4.5)
        lambda_ = max(0.3, min(4.5, lambda_))
        mu = max(0.2, min(4.0, mu))

        # Compute score probability grid
        score_matrix = {}
        prob_home = 0.0
        prob_draw = 0.0
        prob_away = 0.0
        prob_over_1_5 = 0.0
        prob_over_2_5 = 0.0
        prob_btts = 0.0

        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                tau_val = self._tau(x, y, lambda_, mu)
                p_x = self._poisson_pmf(x, lambda_)
                p_y = self._poisson_pmf(y, mu)
                prob = max(0.0, tau_val * p_x * p_y)
                
                score_str = f"{x}-{y}"
                score_matrix[score_str] = prob

                # Outcome accumulators
                if x > y:
                    prob_home += prob
                elif x == y:
                    prob_draw += prob
                else:
                    prob_away += prob

                if x + y > 1:
                    prob_over_1_5 += prob
                if x + y > 2:
                    prob_over_2_5 += prob
                if x >= 1 and y >= 1:
                    prob_btts += prob

        # Normalize 1X2 so they sum exactly to 1.00
        total_1x2 = prob_home + prob_draw + prob_away
        if total_1x2 > 0:
            prob_home /= total_1x2
            prob_draw /= total_1x2
            prob_away /= total_1x2

        # Sort top exact scores
        top_scores = dict(sorted(score_matrix.items(), key=lambda item: item[1], reverse=True)[:5])

        # Calculate fair decimal odds (1 / probability)
        fair_odds_home = round(1.0 / max(0.01, prob_home), 2)
        fair_odds_draw = round(1.0 / max(0.01, prob_draw), 2)
        fair_odds_away = round(1.0 / max(0.01, prob_away), 2)

        return {
            "expected_goals_home": round(lambda_, 2),
            "expected_goals_away": round(mu, 2),
            "prob_home_win": round(prob_home, 4),
            "prob_draw": round(prob_draw, 4),
            "prob_away_win": round(prob_away, 4),
            "prob_over_1_5": round(min(0.99, prob_over_1_5), 4),
            "prob_over_2_5": round(min(0.99, prob_over_2_5), 4),
            "prob_under_2_5": round(max(0.01, 1.0 - prob_over_2_5), 4),
            "prob_btts": round(min(0.99, prob_btts), 4),
            "fair_odds_home": fair_odds_home,
            "fair_odds_draw": fair_odds_draw,
            "fair_odds_away": fair_odds_away,
            "top_exact_scores": {k: round(v, 4) for k, v in top_scores.items()},
        }
