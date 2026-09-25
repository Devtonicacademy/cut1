from typing import Dict, List
from apps.api.app.models.schemas import Team

class XgAnalyzer:
    """
    Analyzes underlying performance metrics:
    - Rolling Expected Goals (xG) created and conceded
    - Recent momentum / form decay
    - Rest days & schedule fatigue
    - Injury impact on team strength
    """
    
    @staticmethod
    def calculate_form_factor(form_string: str) -> float:
        """
        Computes weighted form score from last 5 games.
        E.g. "WWDWL" where most recent matches carry more weight.
        W=3 pts, D=1 pt, L=0 pts.
        """
        if not form_string:
            return 1.0
        
        weights = [1.0, 1.2, 1.4, 1.7, 2.0] # Exponential recency weighting
        points_map = {"W": 3.0, "D": 1.0, "L": 0.0}
        
        total_pts = 0.0
        max_possible = 0.0
        
        # Take up to last 5 characters
        recent_form = list(form_string.upper())[-5:]
        active_weights = weights[-len(recent_form):]
        
        for ch, w in zip(recent_form, active_weights):
            pts = points_map.get(ch, 1.0)
            total_pts += pts * w
            max_possible += 3.0 * w
            
        ratio = total_pts / max_possible if max_possible > 0 else 0.5
        # Maps 0.0-1.0 ratio to multiplier between 0.82 (slumping) and 1.20 (flying)
        return round(0.82 + (ratio * 0.38), 3)

    @staticmethod
    def adjust_team_parameters(
        team: Team,
        is_home: bool,
        days_since_last_match: int = 6,
        key_missing_count: int = 0
    ) -> Dict[str, float]:
        """
        Combines baseline team ratings with xG metrics, form, rest, and missing starters.
        """
        base_attack = team.home_attack_strength if is_home else team.away_attack_strength
        base_defense = team.home_defense_weakness if is_home else team.away_defense_weakness
        
        # xG adjustment factor: if rolling xG created is above 1.5, boost attack
        xg_attack_multiplier = (team.rolling_xg_created / 1.40)
        # if rolling xG conceded is high, defense weakness increases
        xg_defense_multiplier = (team.rolling_xg_conceded / 1.20)
        
        # Form multiplier
        form_multiplier = XgAnalyzer.calculate_form_factor(team.form)
        
        # Fatigue factor: playing within 3 days slightly lowers efficiency
        fatigue_penalty = 0.94 if days_since_last_match <= 3 else 1.0
        
        # Injury penalty: 3% attack/defense degradation per missing key player
        injury_penalty = max(0.80, 1.0 - (0.04 * key_missing_count))
        
        calibrated_attack = base_attack * (0.65 + 0.35 * xg_attack_multiplier) * form_multiplier * fatigue_penalty * injury_penalty
        calibrated_defense = base_defense * (0.70 + 0.30 * xg_defense_multiplier) / injury_penalty
        
        return {
            "attack": round(max(0.4, min(3.5, calibrated_attack)), 3),
            "defense": round(max(0.4, min(3.0, calibrated_defense)), 3)
        }
