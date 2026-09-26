import asyncio
import datetime as dt
import os
from typing import Dict, List, Optional, Sequence

from apps.api.app.data import db
from apps.api.app.models.schemas import Fixture, Team

NO_INJURY_DATA = "Injury and lineup data is not connected yet; check team news before kickoff."
PICKS = ("1", "X", "2")


def predicted_pick(prob_home: float, prob_draw: float, prob_away: float) -> str:
    probs = (prob_home, prob_draw, prob_away)
    return PICKS[max(range(3), key=lambda i: probs[i])]


def build_prompt(f: Fixture) -> str:
    p = f.prediction
    home, away = f.home_team, f.away_team
    return (
        f"Explain a football prediction to fans in 2 short, plain sentences.\n"
        f"Match: {home.name} (home) vs {away.name}, {f.league}.\n"
        f"Model probabilities: {home.name} win {p.prob_home_win:.0%}, draw {p.prob_draw:.0%}, "
        f"{away.name} win {p.prob_away_win:.0%}.\n"
        f"Recent form (oldest to newest): {home.name} {home.form or 'n/a'}, {away.name} {away.form or 'n/a'}.\n"
        f"Facts behind the prediction: {'; '.join(p.key_factors) or 'no strong edge either way'}.\n"
        f"Rules: use only these facts; do not invent injuries, lineups, news or tactics; "
        f"do not recommend a bet or a stake; say it is a probability, not a certainty."
    )


class GeminiAnalyzer:
    """
    Plain-English explanation for each prediction. Page requests only read explanations
    already saved in the database (or use a template), so they never wait on Gemini.
    The scheduler calls explain_missing() to write new ones in the background at a
    pace the free tier allows. Explanations are grounded only in the model's own facts.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
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
        prob_away: float,
        key_factors: Optional[List[str]] = None,
        fixture_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Returns {"tactical_summary", "lineup_risk"}: the saved AI explanation if there is one, else the template."""
        if fixture_id:
            with db.connect() as conn:
                saved = db.get_explanation(conn, fixture_id, predicted_pick(prob_home, prob_draw, prob_away))
            if saved:
                return {"tactical_summary": saved, "lineup_risk": NO_INJURY_DATA}
        return self._generate_heuristic_context(home_team, away_team, ev_bets, prob_home, prob_away)

    async def explain_missing(
        self, fixtures: Sequence[Fixture], max_calls: int = 30, pause_seconds: float = 4.0
    ) -> Dict:
        """
        Writes explanations for upcoming fixtures that lack one for their current prediction,
        soonest kickoff first. Stops for this round on the first error (e.g. a rate limit);
        the next scheduler cycle simply continues.
        """
        if not self.client:
            return {"written": 0, "skipped": "no working GEMINI_API_KEY"}
        todo = []
        with db.connect() as conn:
            for f in sorted((f for f in fixtures if f.prediction and f.is_upcoming), key=lambda f: f.kickoff_timestamp or ""):
                p = f.prediction
                pick = predicted_pick(p.prob_home_win, p.prob_draw, p.prob_away_win)
                if not db.get_explanation(conn, f.id, pick):
                    todo.append((f, pick))
        written = 0
        for f, pick in todo[:max_calls]:
            if written:
                await asyncio.sleep(pause_seconds)
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content, model=self.model, contents=build_prompt(f)
                )
                text = (response.text or "").strip()
            except Exception as e:
                return {"written": written, "remaining": len(todo) - written, "stopped": str(e)[:200]}
            if text:
                with db.connect() as conn:
                    db.save_explanation(conn, f.id, pick, text, dt.datetime.now(dt.timezone.utc).isoformat())
                written += 1
        return {"written": written, "remaining": len(todo) - written}
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
