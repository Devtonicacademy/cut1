import os
from typing import Dict, List, Optional
from apps.api.app.models.schemas import Team

NO_INJURY_DATA = "Injury and lineup data is not connected yet; check team news before kickoff."


class GeminiAnalyzer:
    """
    Writes a short plain-English explanation of each prediction with Google Gemini,
    grounded only in the model's own facts (probabilities, form, key factors).
    Without a working key it falls back to a template built from the same facts.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.client = None
        self._cache: Dict[tuple, Dict[str, str]] = {}  # the free tier has tight request limits
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Notice: Google GenAI client could not be initialized: {e}")

    async def analyze_matchup_context(
        self,
        home_team: Team,
        away_team: Team,
        league: str,
        ev_bets: List[Dict[str, any]],
        prob_home: float,
        prob_draw: float,
        prob_away: float,
        key_factors: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Returns {"tactical_summary", "lineup_risk"} for one match."""
        key_factors = key_factors or []
        if self.client:
            cache_key = (home_team.name, away_team.name, round(prob_home, 2), round(prob_draw, 2), tuple(key_factors))
            if cache_key in self._cache:
                return self._cache[cache_key]
            try:
                prompt = (
                    f"Explain a football prediction to fans in 2 short, plain sentences.\n"
                    f"Match: {home_team.name} (home) vs {away_team.name}, {league}.\n"
                    f"Model probabilities: {home_team.name} win {prob_home:.0%}, draw {prob_draw:.0%}, "
                    f"{away_team.name} win {prob_away:.0%}.\n"
                    f"Recent form (oldest to newest): {home_team.name} {home_team.form or 'n/a'}, "
                    f"{away_team.name} {away_team.form or 'n/a'}.\n"
                    f"Facts behind the prediction: {'; '.join(key_factors) or 'no strong edge either way'}.\n"
                    f"Rules: use only these facts; do not invent injuries, lineups, news or tactics; "
                    f"do not recommend a bet or a stake; say it is a probability, not a certainty."
                )
                response = self.client.models.generate_content(model=self.model, contents=prompt)
                result = {"tactical_summary": response.text.strip(), "lineup_risk": NO_INJURY_DATA}
                self._cache[cache_key] = result
                return result
            except Exception as e:
                print(f"Gemini API call fallback to template: {e}")
                self.client = None  # fail fast for the remaining fixtures

        return self._generate_heuristic_context(home_team, away_team, ev_bets, prob_home, prob_away)
    def _generate_heuristic_context(
        self,
        home: Team,
        away: Team,
        ev_bets: List[Dict[str, any]],
        prob_home: float,
        prob_away: float
    ) -> Dict[str, str]:
        value_note = (
            f" The model rates {ev_bets[0]['market_name']} {ev_bets[0]['expected_value_pct']:.1f}% above the market price."
            if ev_bets else " No selection is priced above the model's fair odds."
        )

        if prob_home >= 0.55:
            tactical = (
                f"{home.name} are clear favourites at home ({prob_home*100:.0f}%), with recent form {home.form or 'n/a'} "
                f"against {away.name}'s {away.form or 'n/a'}." + value_note
            )
        elif prob_away >= 0.45:
            tactical = (
                f"{away.name} are rated stronger despite playing away ({prob_away*100:.0f}%), with recent form "
                f"{away.form or 'n/a'} against {home.name}'s {home.form or 'n/a'}." + value_note
            )
        else:
            tactical = (
                f"Closely matched teams ({home.name} {prob_home*100:.0f}% / {away.name} {prob_away*100:.0f}%); "
                f"a draw or a narrow margin is a realistic outcome." + value_note
            )

        injuries = []
        if home.key_injuries:
            injuries.append(f"{home.short_code}: {', '.join(home.key_injuries)}")
        if away.key_injuries:
            injuries.append(f"{away.short_code}: {', '.join(away.key_injuries)}")
            
        lineup_risk = (
            f"Key missing players: {'; '.join(injuries)}"
            if injuries else NO_INJURY_DATA
        )

        return {
            "tactical_summary": tactical,
            "lineup_risk": lineup_risk
        }
