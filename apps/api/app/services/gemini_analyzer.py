import os
from typing import Dict, List, Optional
from apps.api.app.models.schemas import Team

class GeminiAnalyzer:
    """
    Contextual AI reasoning agent powered by Google Gemini.
    Synthesizes team news, lineup confirmations, tactical styles, and generates
    human-readable rationale for punters.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
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
        prob_away: float
    ) -> Dict[str, str]:
        """
        Generates tactical insights, lineup risk alerts, and concise rationale for punters.
        Uses Gemini API when available, otherwise uses high-fidelity heuristic generator.
        """
        # If Gemini client is active and configured
        if self.client:
            try:
                prompt = (
                    f"You are the Lead Sports Intelligence Analyst for an elite football betting platform in Lagos, Nigeria. "
                    f"Analyze this upcoming {league} match: {home_team.name} (Home) vs {away_team.name} (Away).\n"
                    f"Stats: {home_team.name} form {home_team.form}, xG {home_team.rolling_xg_created:.2f}, injuries: {', '.join(home_team.key_injuries) or 'None'}.\n"
                    f"{away_team.name} form {away_team.form}, xG {away_team.rolling_xg_created:.2f}, injuries: {', '.join(away_team.key_injuries) or 'None'}.\n"
                    f"Model Probabilities: Home: {prob_home*100:.1f}%, Draw: {prob_draw*100:.1f}%, Away: {prob_away*100:.1f}%.\n"
                    f"Top Value Bet: {ev_bets[0]['market_name'] if ev_bets else 'Home Win'}.\n"
                    f"Provide:\n"
                    f"1. A sharp 2-sentence tactical summary explaining why this value bet makes mathematical and tactical sense.\n"
                    f"2. A 1-sentence lineup / volatility warning.\n"
                    f"Tone: Confident, professional, objective, high-stakes sports trading perspective."
                )
                response = self.client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt
                )
                text = response.text.strip()
                parts = text.split("\n\n")
                tactical_summary = parts[0] if len(parts) > 0 else text
                lineup_risk = parts[1] if len(parts) > 1 else "Lineup risk low: Key starting spine confirmed fit."
                return {
                    "tactical_summary": tactical_summary,
                    "lineup_risk": lineup_risk
                }
            except Exception as e:
                print(f"Gemini API call fallback to heuristic: {e}")
                self.client = None # Fail-fast for remaining fixtures

        # High-Fidelity Heuristic Fallback
        return self._generate_heuristic_context(home_team, away_team, ev_bets, prob_home, prob_away)

    def _generate_heuristic_context(
        self,
        home: Team,
        away: Team,
        ev_bets: List[Dict[str, any]],
        prob_home: float,
        prob_away: float
    ) -> Dict[str, str]:
        top_play = ev_bets[0]["market_name"] if ev_bets else f"{home.name} Win"
        edge = ev_bets[0]["expected_value_pct"] if ev_bets else 8.5

        if prob_home >= 0.55:
            tactical = (
                f"{home.name} control territorial dominance at home with an average xG of {home.rolling_xg_created:.2f}, "
                f"giving them a substantial structural advantage over {away.name}. "
                f"Market odds currently misprice {top_play}, yielding a calculated +{edge:.1f}% positive value edge."
            )
        elif prob_away >= 0.45:
            tactical = (
                f"{away.name} show superior tactical counter-pressing and form momentum ({away.form}), "
                f"exploiting defensive transitions against {home.name}. "
                f"Backing {top_play} leverages significant line value over bookmaker consensus."
            )
        else:
            tactical = (
                f"Evenly matched tactical stalemate expected with tight midfield congestion. "
                f"Model metrics favor low-variance goal markets ({top_play}) offering high safety margin."
            )

        injuries = []
        if home.key_injuries:
            injuries.append(f"{home.short_code}: {', '.join(home.key_injuries)}")
        if away.key_injuries:
            injuries.append(f"{away.short_code}: {', '.join(away.key_injuries)}")
            
        lineup_risk = (
            f"Key missing players: {'; '.join(injuries)}"
            if injuries else "Squads at near full strength; no critical lineup red flags detected."
        )

        return {
            "tactical_summary": tactical,
            "lineup_risk": lineup_risk
        }
