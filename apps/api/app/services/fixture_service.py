from typing import List, Optional, Dict
from apps.api.app.models.schemas import (
    Fixture, Team, BookmakerOdds, PredictionDetail
)
from apps.api.app.services.dixon_coles import DixonColesEngine
from apps.api.app.services.xg_analyzer import XgAnalyzer
from apps.api.app.services.ev_engine import EvEngine
from apps.api.app.services.gemini_analyzer import GeminiAnalyzer

class FixtureService:
    """
    Supplies fixtures across 10 top leagues, live market odds, and runs the AI prediction pipeline.
    Identifies statistically likely winners and multi-game accumulator candidates.
    """
    def __init__(self):
        self.dixon_coles = DixonColesEngine()
        self.gemini = GeminiAnalyzer()
        self._raw_fixtures = self._seed_fixtures()
        self._enriched_cache: Dict[float, List[Fixture]] = {}

    def _seed_fixtures(self) -> List[Fixture]:
        """Seeds curated upcoming fixtures across top Nigerian & global betting leagues."""
        return [
            # =========================================================================
            # 1. ENGLISH PREMIER LEAGUE (EPL)
            # =========================================================================
            Fixture(
                id="fix-epl-001",
                league="English Premier League",
                kickoff="Today, 17:30",
                venue="Emirates Stadium, London",
                home_team=Team(
                    id="ars",
                    name="Arsenal",
                    short_code="ARS",
                    league="EPL",
                    home_attack_strength=1.45,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.35,
                    away_defense_weakness=0.80,
                    rolling_xg_created=2.20,
                    rolling_xg_conceded=0.85,
                    form="WWDWW",
                    key_injuries=["M. Odegaard (Doubt)"]
                ),
                away_team=Team(
                    id="che",
                    name="Chelsea",
                    short_code="CHE",
                    league="EPL",
                    home_attack_strength=1.30,
                    home_defense_weakness=1.15,
                    away_attack_strength=1.20,
                    away_defense_weakness=1.25,
                    rolling_xg_created=1.75,
                    rolling_xg_conceded=1.40,
                    form="WWLWD",
                    key_injuries=["R. James (Hamstring)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.88,
                    draw=3.95,
                    away_win=4.15,
                    over_1_5=1.22,
                    over_2_5=1.72,
                    under_2_5=2.15,
                    btts_yes=1.68,
                    btts_no=2.10,
                    double_chance_1x=1.24,
                    double_chance_x2=1.92,
                    double_chance_12=1.25
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.85,
                    draw=3.90,
                    away_win=4.25,
                    over_1_5=1.20,
                    over_2_5=1.70,
                    under_2_5=2.18,
                    btts_yes=1.65,
                    btts_no=2.15,
                    double_chance_1x=1.22,
                    double_chance_x2=1.95,
                    double_chance_12=1.24
                )
            ),
            Fixture(
                id="fix-epl-004",
                league="English Premier League",
                kickoff="Tomorrow, 14:00",
                venue="St. James' Park, Newcastle",
                home_team=Team(
                    id="new",
                    name="Newcastle United",
                    short_code="NEW",
                    league="EPL",
                    home_attack_strength=1.35,
                    home_defense_weakness=1.00,
                    away_attack_strength=1.15,
                    away_defense_weakness=1.15,
                    rolling_xg_created=1.85,
                    rolling_xg_conceded=1.35,
                    form="WDWLW",
                    key_injuries=["S. Botman (Knee)"]
                ),
                away_team=Team(
                    id="mci",
                    name="Manchester City",
                    short_code="MCI",
                    league="EPL",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.85,
                    away_attack_strength=1.55,
                    away_defense_weakness=0.90,
                    rolling_xg_created=2.40,
                    rolling_xg_conceded=1.05,
                    form="WWWDW",
                    key_injuries=["Rodri (ACL - Out)", "K. De Bruyne (Groin)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=5.20,
                    draw=4.40,
                    away_win=1.60,
                    over_1_5=1.18,
                    over_2_5=1.58,
                    under_2_5=2.35,
                    btts_yes=1.62,
                    btts_no=2.20,
                    double_chance_1x=2.30,
                    double_chance_x2=1.16,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=5.35,
                    draw=4.35,
                    away_win=1.58,
                    over_1_5=1.16,
                    over_2_5=1.55,
                    under_2_5=2.40,
                    btts_yes=1.60,
                    btts_no=2.25,
                    double_chance_1x=2.35,
                    double_chance_x2=1.15,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-epl-006",
                league="English Premier League",
                kickoff="Today, 15:00",
                venue="Anfield, Liverpool",
                home_team=Team(
                    id="liv",
                    name="Liverpool",
                    short_code="LIV",
                    league="EPL",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.70,
                    away_attack_strength=1.45,
                    away_defense_weakness=0.80,
                    rolling_xg_created=2.50,
                    rolling_xg_conceded=0.80,
                    form="WWLWW",
                    key_injuries=["H. Elliott (Foot)"]
                ),
                away_team=Team(
                    id="bou",
                    name="Bournemouth",
                    short_code="BOU",
                    league="EPL",
                    home_attack_strength=1.15,
                    home_defense_weakness=1.30,
                    away_attack_strength=1.05,
                    away_defense_weakness=1.40,
                    rolling_xg_created=1.35,
                    rolling_xg_conceded=1.80,
                    form="LDWWL",
                    key_injuries=["T. Adams (Back)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.28,
                    draw=6.20,
                    away_win=9.50,
                    over_1_5=1.12,
                    over_2_5=1.40,
                    under_2_5=2.90,
                    btts_yes=1.70,
                    btts_no=2.08,
                    double_chance_1x=1.06,
                    double_chance_x2=3.65,
                    double_chance_12=1.11
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.27,
                    draw=6.30,
                    away_win=9.80,
                    over_1_5=1.11,
                    over_2_5=1.38,
                    under_2_5=2.95,
                    btts_yes=1.68,
                    btts_no=2.12,
                    double_chance_1x=1.05,
                    double_chance_x2=3.70,
                    double_chance_12=1.10
                )
            ),
            Fixture(
                id="fix-epl-007",
                league="English Premier League",
                kickoff="Today, 15:00",
                venue="Villa Park, Birmingham",
                home_team=Team(
                    id="avl",
                    name="Aston Villa",
                    short_code="AVL",
                    league="EPL",
                    home_attack_strength=1.42,
                    home_defense_weakness=0.90,
                    away_attack_strength=1.30,
                    away_defense_weakness=1.05,
                    rolling_xg_created=1.95,
                    rolling_xg_conceded=1.10,
                    form="WWLWW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="wol",
                    name="Wolverhampton",
                    short_code="WOL",
                    league="EPL",
                    home_attack_strength=1.05,
                    home_defense_weakness=1.35,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.45,
                    rolling_xg_created=1.15,
                    rolling_xg_conceded=1.90,
                    form="LLDLL",
                    key_injuries=["B. Traore (Knee)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.55,
                    draw=4.30,
                    away_win=5.80,
                    over_1_5=1.20,
                    over_2_5=1.65,
                    under_2_5=2.20,
                    btts_yes=1.75,
                    btts_no=2.02,
                    double_chance_1x=1.14,
                    double_chance_x2=2.40,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.53,
                    draw=4.40,
                    away_win=6.00,
                    over_1_5=1.19,
                    over_2_5=1.62,
                    under_2_5=2.25,
                    btts_yes=1.72,
                    btts_no=2.06,
                    double_chance_1x=1.13,
                    double_chance_x2=2.45,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-epl-008",
                league="English Premier League",
                kickoff="Tomorrow, 16:30",
                venue="Tottenham Hotspur Stadium, London",
                home_team=Team(
                    id="tot",
                    name="Tottenham",
                    short_code="TOT",
                    league="EPL",
                    home_attack_strength=1.48,
                    home_defense_weakness=1.05,
                    away_attack_strength=1.35,
                    away_defense_weakness=1.15,
                    rolling_xg_created=2.10,
                    rolling_xg_conceded=1.30,
                    form="WLWLL",
                    key_injuries=["Richarlison (Calf)"]
                ),
                away_team=Team(
                    id="bre",
                    name="Brentford",
                    short_code="BRE",
                    league="EPL",
                    home_attack_strength=1.25,
                    home_defense_weakness=1.25,
                    away_attack_strength=1.10,
                    away_defense_weakness=1.35,
                    rolling_xg_created=1.50,
                    rolling_xg_conceded=1.60,
                    form="LWLWW",
                    key_injuries=["Y. Wissa (Ankle)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.58,
                    draw=4.40,
                    away_win=5.20,
                    over_1_5=1.15,
                    over_2_5=1.52,
                    under_2_5=2.48,
                    btts_yes=1.55,
                    btts_no=2.35,
                    double_chance_1x=1.16,
                    double_chance_x2=2.32,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.56,
                    draw=4.45,
                    away_win=5.30,
                    over_1_5=1.14,
                    over_2_5=1.50,
                    under_2_5=2.52,
                    btts_yes=1.53,
                    btts_no=2.40,
                    double_chance_1x=1.15,
                    double_chance_x2=2.35,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-epl-009",
                league="English Premier League",
                kickoff="Tomorrow, 16:30",
                venue="Old Trafford, Manchester",
                home_team=Team(
                    id="mun",
                    name="Manchester United",
                    short_code="MUN",
                    league="EPL",
                    home_attack_strength=1.32,
                    home_defense_weakness=1.10,
                    away_attack_strength=1.22,
                    away_defense_weakness=1.20,
                    rolling_xg_created=1.70,
                    rolling_xg_conceded=1.45,
                    form="DWLLW",
                    key_injuries=["L. Shaw (Calf)", "R. Hojlund (Hamstring)"]
                ),
                away_team=Team(
                    id="bha",
                    name="Brighton",
                    short_code="BHA",
                    league="EPL",
                    home_attack_strength=1.35,
                    home_defense_weakness=1.10,
                    away_attack_strength=1.25,
                    away_defense_weakness=1.20,
                    rolling_xg_created=1.80,
                    rolling_xg_conceded=1.35,
                    form="DDWWL",
                    key_injuries=["J. Pedro (Knock)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=2.25,
                    draw=3.75,
                    away_win=2.95,
                    over_1_5=1.18,
                    over_2_5=1.60,
                    under_2_5=2.30,
                    btts_yes=1.52,
                    btts_no=2.42,
                    double_chance_1x=1.38,
                    double_chance_x2=1.62,
                    double_chance_12=1.26
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=2.22,
                    draw=3.80,
                    away_win=3.00,
                    over_1_5=1.17,
                    over_2_5=1.58,
                    under_2_5=2.35,
                    btts_yes=1.50,
                    btts_no=2.48,
                    double_chance_1x=1.37,
                    double_chance_x2=1.65,
                    double_chance_12=1.25
                )
            ),

            # =========================================================================
            # 2. SPANISH LA LIGA
            # =========================================================================
            Fixture(
                id="fix-laliga-002",
                league="Spanish La Liga",
                kickoff="Today, 20:00",
                venue="Santiago Bernabéu, Madrid",
                home_team=Team(
                    id="rma",
                    name="Real Madrid",
                    short_code="RMA",
                    league="La Liga",
                    home_attack_strength=1.60,
                    home_defense_weakness=0.80,
                    away_attack_strength=1.40,
                    away_defense_weakness=0.90,
                    rolling_xg_created=2.35,
                    rolling_xg_conceded=0.95,
                    form="WWWWW",
                    key_injuries=["D. Alaba (Knee)"]
                ),
                away_team=Team(
                    id="vil",
                    name="Villarreal",
                    short_code="VIL",
                    league="La Liga",
                    home_attack_strength=1.25,
                    home_defense_weakness=1.20,
                    away_attack_strength=1.15,
                    away_defense_weakness=1.35,
                    rolling_xg_created=1.60,
                    rolling_xg_conceded=1.70,
                    form="WLWDL",
                    key_injuries=["G. Moreno (Hamstring)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.32,
                    draw=5.80,
                    away_win=8.50,
                    over_1_5=1.14,
                    over_2_5=1.48,
                    under_2_5=2.65,
                    btts_yes=1.75,
                    btts_no=2.00,
                    double_chance_1x=1.08,
                    double_chance_x2=3.35,
                    double_chance_12=1.14
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.30,
                    draw=6.00,
                    away_win=8.75,
                    over_1_5=1.12,
                    over_2_5=1.46,
                    under_2_5=2.70,
                    btts_yes=1.72,
                    btts_no=2.05,
                    double_chance_1x=1.07,
                    double_chance_x2=3.40,
                    double_chance_12=1.13
                )
            ),
            Fixture(
                id="fix-laliga-010",
                league="Spanish La Liga",
                kickoff="Tomorrow, 20:00",
                venue="Estadi Olímpic Lluís Companys, Barcelona",
                home_team=Team(
                    id="bar",
                    name="Barcelona",
                    short_code="BAR",
                    league="La Liga",
                    home_attack_strength=1.70,
                    home_defense_weakness=0.82,
                    away_attack_strength=1.50,
                    away_defense_weakness=0.90,
                    rolling_xg_created=2.60,
                    rolling_xg_conceded=0.90,
                    form="WWWWW",
                    key_injuries=["M. ter Stegen (Knee)", "Gavi (Fitness)"]
                ),
                away_team=Team(
                    id="sev",
                    name="Sevilla",
                    short_code="SEV",
                    league="La Liga",
                    home_attack_strength=1.10,
                    home_defense_weakness=1.25,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.40,
                    rolling_xg_created=1.20,
                    rolling_xg_conceded=1.75,
                    form="WDLLW",
                    key_injuries=["S. Niguez (Hamstring)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.30,
                    draw=5.90,
                    away_win=9.00,
                    over_1_5=1.13,
                    over_2_5=1.45,
                    under_2_5=2.70,
                    btts_yes=1.78,
                    btts_no=1.98,
                    double_chance_1x=1.07,
                    double_chance_x2=3.45,
                    double_chance_12=1.13
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.28,
                    draw=6.00,
                    away_win=9.25,
                    over_1_5=1.12,
                    over_2_5=1.42,
                    under_2_5=2.75,
                    btts_yes=1.75,
                    btts_no=2.02,
                    double_chance_1x=1.06,
                    double_chance_x2=3.50,
                    double_chance_12=1.12
                )
            ),
            Fixture(
                id="fix-laliga-011",
                league="Spanish La Liga",
                kickoff="Today, 17:30",
                venue="Metropolitano Stadium, Madrid",
                home_team=Team(
                    id="atm",
                    name="Atletico Madrid",
                    short_code="ATM",
                    league="La Liga",
                    home_attack_strength=1.40,
                    home_defense_weakness=0.68,
                    away_attack_strength=1.25,
                    away_defense_weakness=0.85,
                    rolling_xg_created=1.85,
                    rolling_xg_conceded=0.75,
                    form="DWWDW",
                    key_injuries=["C. Azpilicueta (Calf)"]
                ),
                away_team=Team(
                    id="rso",
                    name="Real Sociedad",
                    short_code="RSO",
                    league="La Liga",
                    home_attack_strength=1.15,
                    home_defense_weakness=1.00,
                    away_attack_strength=1.05,
                    away_defense_weakness=1.15,
                    rolling_xg_created=1.25,
                    rolling_xg_conceded=1.20,
                    form="LDLLD",
                    key_injuries=["H. Traore (ACL)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.65,
                    draw=3.80,
                    away_win=5.50,
                    over_1_5=1.35,
                    over_2_5=2.15,
                    under_2_5=1.70,
                    btts_yes=2.05,
                    btts_no=1.72,
                    double_chance_1x=1.15,
                    double_chance_x2=2.20,
                    double_chance_12=1.24
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.62,
                    draw=3.85,
                    away_win=5.60,
                    over_1_5=1.33,
                    over_2_5=2.12,
                    under_2_5=1.72,
                    btts_yes=2.02,
                    btts_no=1.75,
                    double_chance_1x=1.14,
                    double_chance_x2=2.25,
                    double_chance_12=1.23
                )
            ),
            Fixture(
                id="fix-laliga-012",
                league="Spanish La Liga",
                kickoff="Tomorrow, 15:15",
                venue="San Mames, Bilbao",
                home_team=Team(
                    id="ath",
                    name="Athletic Club",
                    short_code="ATH",
                    league="La Liga",
                    home_attack_strength=1.38,
                    home_defense_weakness=0.85,
                    away_attack_strength=1.20,
                    away_defense_weakness=1.05,
                    rolling_xg_created=1.75,
                    rolling_xg_conceded=0.95,
                    form="WWWDW",
                    key_injuries=["N. Williams (Ankle)"]
                ),
                away_team=Team(
                    id="cel",
                    name="Celta Vigo",
                    short_code="CEL",
                    league="La Liga",
                    home_attack_strength=1.20,
                    home_defense_weakness=1.30,
                    away_attack_strength=1.05,
                    away_defense_weakness=1.45,
                    rolling_xg_created=1.40,
                    rolling_xg_conceded=1.80,
                    form="LWLWW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.72,
                    draw=3.85,
                    away_win=4.80,
                    over_1_5=1.26,
                    over_2_5=1.85,
                    under_2_5=1.95,
                    btts_yes=1.82,
                    btts_no=1.94,
                    double_chance_1x=1.18,
                    double_chance_x2=2.10,
                    double_chance_12=1.25
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.70,
                    draw=3.90,
                    away_win=4.90,
                    over_1_5=1.24,
                    over_2_5=1.82,
                    under_2_5=1.98,
                    btts_yes=1.80,
                    btts_no=1.96,
                    double_chance_1x=1.17,
                    double_chance_x2=2.15,
                    double_chance_12=1.24
                )
            ),

            # =========================================================================
            # 3. ITALIAN SERIE A
            # =========================================================================
            Fixture(
                id="fix-seriea-005",
                league="Italian Serie A",
                kickoff="Tomorrow, 19:45",
                venue="San Siro, Milan",
                home_team=Team(
                    id="int",
                    name="Inter Milan",
                    short_code="INT",
                    league="Serie A",
                    home_attack_strength=1.50,
                    home_defense_weakness=0.70,
                    away_attack_strength=1.35,
                    away_defense_weakness=0.80,
                    rolling_xg_created=2.15,
                    rolling_xg_conceded=0.80,
                    form="DWWDL",
                    key_injuries=["N. Barella (Thigh)"]
                ),
                away_team=Team(
                    id="tor",
                    name="Torino",
                    short_code="TOR",
                    league="Serie A",
                    home_attack_strength=1.05,
                    home_defense_weakness=0.90,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.10,
                    rolling_xg_created=1.20,
                    rolling_xg_conceded=1.10,
                    form="WWDWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.38,
                    draw=4.80,
                    away_win=8.20,
                    over_1_5=1.24,
                    over_2_5=1.80,
                    under_2_5=2.02,
                    btts_yes=2.05,
                    btts_no=1.70,
                    double_chance_1x=1.09,
                    double_chance_x2=3.05,
                    double_chance_12=1.18
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.36,
                    draw=4.90,
                    away_win=8.50,
                    over_1_5=1.22,
                    over_2_5=1.78,
                    under_2_5=2.05,
                    btts_yes=2.10,
                    btts_no=1.68,
                    double_chance_1x=1.08,
                    double_chance_x2=3.10,
                    double_chance_12=1.17
                )
            ),
            Fixture(
                id="fix-seriea-014",
                league="Italian Serie A",
                kickoff="Today, 17:00",
                venue="Allianz Stadium, Turin",
                home_team=Team(
                    id="juv",
                    name="Juventus",
                    short_code="JUV",
                    league="Serie A",
                    home_attack_strength=1.35,
                    home_defense_weakness=0.60,
                    away_attack_strength=1.25,
                    away_defense_weakness=0.75,
                    rolling_xg_created=1.70,
                    rolling_xg_conceded=0.60,
                    form="WDDDW",
                    key_injuries=["T. Weah (Ankle)"]
                ),
                away_team=Team(
                    id="nap",
                    name="Napoli",
                    short_code="NAP",
                    league="Serie A",
                    home_attack_strength=1.40,
                    home_defense_weakness=0.85,
                    away_attack_strength=1.28,
                    away_defense_weakness=0.95,
                    rolling_xg_created=1.85,
                    rolling_xg_conceded=1.00,
                    form="WWWWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=2.20,
                    draw=3.25,
                    away_win=3.40,
                    over_1_5=1.38,
                    over_2_5=2.25,
                    under_2_5=1.62,
                    btts_yes=1.92,
                    btts_no=1.80,
                    double_chance_1x=1.32,
                    double_chance_x2=1.68,
                    double_chance_12=1.33
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=2.18,
                    draw=3.30,
                    away_win=3.45,
                    over_1_5=1.36,
                    over_2_5=2.20,
                    under_2_5=1.65,
                    btts_yes=1.90,
                    btts_no=1.82,
                    double_chance_1x=1.31,
                    double_chance_x2=1.70,
                    double_chance_12=1.32
                )
            ),
            Fixture(
                id="fix-seriea-015",
                league="Italian Serie A",
                kickoff="Today, 19:45",
                venue="San Siro, Milan",
                home_team=Team(
                    id="acm",
                    name="AC Milan",
                    short_code="ACM",
                    league="Serie A",
                    home_attack_strength=1.45,
                    home_defense_weakness=0.95,
                    away_attack_strength=1.30,
                    away_defense_weakness=1.05,
                    rolling_xg_created=2.00,
                    rolling_xg_conceded=1.15,
                    form="WWLDW",
                    key_injuries=["I. Bennacer (Calf)"]
                ),
                away_team=Team(
                    id="lec",
                    name="Lecce",
                    short_code="LEC",
                    league="Serie A",
                    home_attack_strength=0.95,
                    home_defense_weakness=1.25,
                    away_attack_strength=0.85,
                    away_defense_weakness=1.35,
                    rolling_xg_created=0.95,
                    rolling_xg_conceded=1.70,
                    form="DDWLL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.35,
                    draw=5.20,
                    away_win=8.50,
                    over_1_5=1.18,
                    over_2_5=1.65,
                    under_2_5=2.25,
                    btts_yes=1.95,
                    btts_no=1.78,
                    double_chance_1x=1.08,
                    double_chance_x2=3.15,
                    double_chance_12=1.16
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.34,
                    draw=5.30,
                    away_win=8.75,
                    over_1_5=1.17,
                    over_2_5=1.62,
                    under_2_5=2.28,
                    btts_yes=1.92,
                    btts_no=1.80,
                    double_chance_1x=1.07,
                    double_chance_x2=3.20,
                    double_chance_12=1.15
                )
            ),
            Fixture(
                id="fix-seriea-016",
                league="Italian Serie A",
                kickoff="Tomorrow, 17:00",
                venue="Gewiss Stadium, Bergamo",
                home_team=Team(
                    id="ata",
                    name="Atalanta",
                    short_code="ATA",
                    league="Serie A",
                    home_attack_strength=1.45,
                    home_defense_weakness=1.00,
                    away_attack_strength=1.30,
                    away_defense_weakness=1.10,
                    rolling_xg_created=2.10,
                    rolling_xg_conceded=1.25,
                    form="WLWLL",
                    key_injuries=["G. Scamacca (ACL)"]
                ),
                away_team=Team(
                    id="fio",
                    name="Fiorentina",
                    short_code="FIO",
                    league="Serie A",
                    home_attack_strength=1.25,
                    home_defense_weakness=1.10,
                    away_attack_strength=1.10,
                    away_defense_weakness=1.25,
                    rolling_xg_created=1.55,
                    rolling_xg_conceded=1.45,
                    form="DDDWW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.85,
                    draw=3.75,
                    away_win=4.10,
                    over_1_5=1.22,
                    over_2_5=1.70,
                    under_2_5=2.15,
                    btts_yes=1.65,
                    btts_no=2.15,
                    double_chance_1x=1.24,
                    double_chance_x2=1.95,
                    double_chance_12=1.26
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.83,
                    draw=3.80,
                    away_win=4.20,
                    over_1_5=1.20,
                    over_2_5=1.68,
                    under_2_5=2.20,
                    btts_yes=1.62,
                    btts_no=2.20,
                    double_chance_1x=1.23,
                    double_chance_x2=1.98,
                    double_chance_12=1.25
                )
            ),

            # =========================================================================
            # 4. GERMAN BUNDESLIGA
            # =========================================================================
            Fixture(
                id="fix-bundes-018",
                league="German Bundesliga",
                kickoff="Today, 17:30",
                venue="Allianz Arena, Munich",
                home_team=Team(
                    id="bay",
                    name="Bayern Munich",
                    short_code="BAY",
                    league="Bundesliga",
                    home_attack_strength=1.80,
                    home_defense_weakness=0.80,
                    away_attack_strength=1.60,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.85,
                    rolling_xg_conceded=0.90,
                    form="WWWWW",
                    key_injuries=["J. Stanisic (Knee)"]
                ),
                away_team=Team(
                    id="lev",
                    name="Bayer Leverkusen",
                    short_code="LEV",
                    league="Bundesliga",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.95,
                    away_attack_strength=1.55,
                    away_defense_weakness=1.05,
                    rolling_xg_created=2.45,
                    rolling_xg_conceded=1.20,
                    form="WWLWW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.70,
                    draw=4.40,
                    away_win=4.20,
                    over_1_5=1.10,
                    over_2_5=1.38,
                    under_2_5=3.00,
                    btts_yes=1.42,
                    btts_no=2.70,
                    double_chance_1x=1.22,
                    double_chance_x2=2.15,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.68,
                    draw=4.45,
                    away_win=4.30,
                    over_1_5=1.09,
                    over_2_5=1.35,
                    under_2_5=3.05,
                    btts_yes=1.40,
                    btts_no=2.75,
                    double_chance_1x=1.21,
                    double_chance_x2=2.20,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-bundes-019",
                league="German Bundesliga",
                kickoff="Today, 19:30",
                venue="Signal Iduna Park, Dortmund",
                home_team=Team(
                    id="bvb",
                    name="Borussia Dortmund",
                    short_code="BVB",
                    league="Bundesliga",
                    home_attack_strength=1.55,
                    home_defense_weakness=0.90,
                    away_attack_strength=1.35,
                    away_defense_weakness=1.10,
                    rolling_xg_created=2.25,
                    rolling_xg_conceded=1.15,
                    form="LWWDL",
                    key_injuries=["G. Reyna (Groin)"]
                ),
                away_team=Team(
                    id="boc",
                    name="VfL Bochum",
                    short_code="BOC",
                    league="Bundesliga",
                    home_attack_strength=1.00,
                    home_defense_weakness=1.40,
                    away_attack_strength=0.90,
                    away_defense_weakness=1.55,
                    rolling_xg_created=1.10,
                    rolling_xg_conceded=2.00,
                    form="DLLLL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.26,
                    draw=6.50,
                    away_win=10.00,
                    over_1_5=1.11,
                    over_2_5=1.36,
                    under_2_5=3.10,
                    btts_yes=1.68,
                    btts_no=2.10,
                    double_chance_1x=1.05,
                    double_chance_x2=3.85,
                    double_chance_12=1.11
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.25,
                    draw=6.60,
                    away_win=10.50,
                    over_1_5=1.10,
                    over_2_5=1.34,
                    under_2_5=3.15,
                    btts_yes=1.65,
                    btts_no=2.15,
                    double_chance_1x=1.04,
                    double_chance_x2=3.90,
                    double_chance_12=1.10
                )
            ),
            Fixture(
                id="fix-bundes-020",
                league="German Bundesliga",
                kickoff="Tomorrow, 14:30",
                venue="Red Bull Arena, Leipzig",
                home_team=Team(
                    id="rbl",
                    name="RB Leipzig",
                    short_code="RBL",
                    league="Bundesliga",
                    home_attack_strength=1.50,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.30,
                    away_defense_weakness=0.90,
                    rolling_xg_created=2.05,
                    rolling_xg_conceded=0.85,
                    form="DDWWL",
                    key_injuries=["K. Kampl (Thigh)"]
                ),
                away_team=Team(
                    id="aug",
                    name="FC Augsburg",
                    short_code="AUG",
                    league="Bundesliga",
                    home_attack_strength=1.10,
                    home_defense_weakness=1.35,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.45,
                    rolling_xg_created=1.20,
                    rolling_xg_conceded=1.85,
                    form="LWLLD",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.38,
                    draw=5.20,
                    away_win=7.50,
                    over_1_5=1.14,
                    over_2_5=1.45,
                    under_2_5=2.70,
                    btts_yes=1.68,
                    btts_no=2.10,
                    double_chance_1x=1.10,
                    double_chance_x2=3.00,
                    double_chance_12=1.16
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.36,
                    draw=5.30,
                    away_win=7.80,
                    over_1_5=1.13,
                    over_2_5=1.42,
                    under_2_5=2.75,
                    btts_yes=1.65,
                    btts_no=2.15,
                    double_chance_1x=1.09,
                    double_chance_x2=3.05,
                    double_chance_12=1.15
                )
            ),

            # =========================================================================
            # 5. FRENCH LIGUE 1
            # =========================================================================
            Fixture(
                id="fix-ligue1-022",
                league="French Ligue 1",
                kickoff="Today, 20:00",
                venue="Parc des Princes, Paris",
                home_team=Team(
                    id="psg",
                    name="Paris Saint-Germain",
                    short_code="PSG",
                    league="Ligue 1",
                    home_attack_strength=1.68,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.50,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.50,
                    rolling_xg_conceded=0.85,
                    form="DWWWW",
                    key_injuries=["G. Ramos (Ankle)"]
                ),
                away_team=Team(
                    id="ren",
                    name="Rennes",
                    short_code="REN",
                    league="Ligue 1",
                    home_attack_strength=1.20,
                    home_defense_weakness=1.20,
                    away_attack_strength=1.05,
                    away_defense_weakness=1.35,
                    rolling_xg_created=1.35,
                    rolling_xg_conceded=1.65,
                    form="DWLLW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.38,
                    draw=5.20,
                    away_win=7.50,
                    over_1_5=1.16,
                    over_2_5=1.52,
                    under_2_5=2.50,
                    btts_yes=1.75,
                    btts_no=2.00,
                    double_chance_1x=1.10,
                    double_chance_x2=3.00,
                    double_chance_12=1.16
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.36,
                    draw=5.30,
                    away_win=7.75,
                    over_1_5=1.15,
                    over_2_5=1.50,
                    under_2_5=2.55,
                    btts_yes=1.72,
                    btts_no=2.05,
                    double_chance_1x=1.09,
                    double_chance_x2=3.05,
                    double_chance_12=1.15
                )
            ),
            Fixture(
                id="fix-ligue1-023",
                league="French Ligue 1",
                kickoff="Tomorrow, 20:00",
                venue="Stade Louis II, Monaco",
                home_team=Team(
                    id="mon",
                    name="AS Monaco",
                    short_code="MON",
                    league="Ligue 1",
                    home_attack_strength=1.50,
                    home_defense_weakness=0.85,
                    away_attack_strength=1.35,
                    away_defense_weakness=0.95,
                    rolling_xg_created=2.15,
                    rolling_xg_conceded=0.95,
                    form="WWWWD",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="mpl",
                    name="Montpellier",
                    short_code="MPL",
                    league="Ligue 1",
                    home_attack_strength=1.10,
                    home_defense_weakness=1.45,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.60,
                    rolling_xg_created=1.15,
                    rolling_xg_conceded=2.10,
                    form="WLLLD",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.32,
                    draw=5.80,
                    away_win=8.50,
                    over_1_5=1.12,
                    over_2_5=1.42,
                    under_2_5=2.80,
                    btts_yes=1.70,
                    btts_no=2.08,
                    double_chance_1x=1.07,
                    double_chance_x2=3.35,
                    double_chance_12=1.14
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.30,
                    draw=5.90,
                    away_win=8.75,
                    over_1_5=1.11,
                    over_2_5=1.40,
                    under_2_5=2.85,
                    btts_yes=1.68,
                    btts_no=2.12,
                    double_chance_1x=1.06,
                    double_chance_x2=3.40,
                    double_chance_12=1.13
                )
            ),
            Fixture(
                id="fix-ligue1-024",
                league="French Ligue 1",
                kickoff="Tomorrow, 19:45",
                venue="Stade Vélodrome, Marseille",
                home_team=Team(
                    id="om",
                    name="Marseille",
                    short_code="OM",
                    league="Ligue 1",
                    home_attack_strength=1.45,
                    home_defense_weakness=0.90,
                    away_attack_strength=1.35,
                    away_defense_weakness=1.00,
                    rolling_xg_created=2.05,
                    rolling_xg_conceded=1.10,
                    form="WWWDW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="nic",
                    name="Nice",
                    short_code="NIC",
                    league="Ligue 1",
                    home_attack_strength=1.25,
                    home_defense_weakness=0.95,
                    away_attack_strength=1.15,
                    away_defense_weakness=1.10,
                    rolling_xg_created=1.50,
                    rolling_xg_conceded=1.20,
                    form="WLDWD",
                    key_injuries=["T. Moffi (ACL)"]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.75,
                    draw=3.80,
                    away_win=4.60,
                    over_1_5=1.22,
                    over_2_5=1.72,
                    under_2_5=2.10,
                    btts_yes=1.70,
                    btts_no=2.08,
                    double_chance_1x=1.20,
                    double_chance_x2=2.05,
                    double_chance_12=1.25
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.72,
                    draw=3.85,
                    away_win=4.75,
                    over_1_5=1.20,
                    over_2_5=1.70,
                    under_2_5=2.15,
                    btts_yes=1.68,
                    btts_no=2.12,
                    double_chance_1x=1.19,
                    double_chance_x2=2.10,
                    double_chance_12=1.24
                )
            ),

            # =========================================================================
            # 6. UEFA CHAMPIONS LEAGUE
            # =========================================================================
            Fixture(
                id="fix-ucl-026",
                league="UEFA Champions League",
                kickoff="Tuesday, 20:00",
                venue="Santiago Bernabéu, Madrid",
                home_team=Team(
                    id="rma-ucl",
                    name="Real Madrid",
                    short_code="RMA",
                    league="UCL",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.80,
                    away_attack_strength=1.45,
                    away_defense_weakness=0.88,
                    rolling_xg_created=2.40,
                    rolling_xg_conceded=0.90,
                    form="WWWDW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="bvb-ucl",
                    name="Borussia Dortmund",
                    short_code="BVB",
                    league="UCL",
                    home_attack_strength=1.40,
                    home_defense_weakness=1.10,
                    away_attack_strength=1.25,
                    away_defense_weakness=1.25,
                    rolling_xg_created=1.80,
                    rolling_xg_conceded=1.45,
                    form="WWLWW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.48,
                    draw=4.80,
                    away_win=6.00,
                    over_1_5=1.14,
                    over_2_5=1.48,
                    under_2_5=2.65,
                    btts_yes=1.62,
                    btts_no=2.20,
                    double_chance_1x=1.13,
                    double_chance_x2=2.60,
                    double_chance_12=1.18
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.46,
                    draw=4.90,
                    away_win=6.20,
                    over_1_5=1.13,
                    over_2_5=1.45,
                    under_2_5=2.70,
                    btts_yes=1.60,
                    btts_no=2.25,
                    double_chance_1x=1.12,
                    double_chance_x2=2.65,
                    double_chance_12=1.17
                )
            ),
            Fixture(
                id="fix-ucl-027",
                league="UEFA Champions League",
                kickoff="Wednesday, 20:00",
                venue="Etihad Stadium, Manchester",
                home_team=Team(
                    id="mci-ucl",
                    name="Manchester City",
                    short_code="MCI",
                    league="UCL",
                    home_attack_strength=1.70,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.50,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.50,
                    rolling_xg_conceded=0.85,
                    form="WWWDW",
                    key_injuries=["Rodri (ACL - Out)"]
                ),
                away_team=Team(
                    id="int-ucl",
                    name="Inter Milan",
                    short_code="INT",
                    league="UCL",
                    home_attack_strength=1.40,
                    home_defense_weakness=0.85,
                    away_attack_strength=1.28,
                    away_defense_weakness=0.95,
                    rolling_xg_created=1.85,
                    rolling_xg_conceded=1.10,
                    form="DWWDL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.52,
                    draw=4.40,
                    away_win=5.80,
                    over_1_5=1.18,
                    over_2_5=1.62,
                    under_2_5=2.28,
                    btts_yes=1.72,
                    btts_no=2.05,
                    double_chance_1x=1.14,
                    double_chance_x2=2.45,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.50,
                    draw=4.45,
                    away_win=6.00,
                    over_1_5=1.16,
                    over_2_5=1.60,
                    under_2_5=2.32,
                    btts_yes=1.70,
                    btts_no=2.10,
                    double_chance_1x=1.13,
                    double_chance_x2=2.50,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-ucl-028",
                league="UEFA Champions League",
                kickoff="Tuesday, 20:00",
                venue="Allianz Arena, Munich",
                home_team=Team(
                    id="bay-ucl",
                    name="Bayern Munich",
                    short_code="BAY",
                    league="UCL",
                    home_attack_strength=1.75,
                    home_defense_weakness=0.80,
                    away_attack_strength=1.55,
                    away_defense_weakness=0.90,
                    rolling_xg_created=2.70,
                    rolling_xg_conceded=0.95,
                    form="WWWWW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="psg-ucl",
                    name="Paris Saint-Germain",
                    short_code="PSG",
                    league="UCL",
                    home_attack_strength=1.45,
                    home_defense_weakness=1.05,
                    away_attack_strength=1.35,
                    away_defense_weakness=1.15,
                    rolling_xg_created=1.90,
                    rolling_xg_conceded=1.35,
                    form="DWWWW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.65,
                    draw=4.20,
                    away_win=4.80,
                    over_1_5=1.12,
                    over_2_5=1.45,
                    under_2_5=2.75,
                    btts_yes=1.50,
                    btts_no=2.50,
                    double_chance_1x=1.18,
                    double_chance_x2=2.20,
                    double_chance_12=1.21
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.62,
                    draw=4.25,
                    away_win=4.95,
                    over_1_5=1.11,
                    over_2_5=1.42,
                    under_2_5=2.80,
                    btts_yes=1.48,
                    btts_no=2.55,
                    double_chance_1x=1.17,
                    double_chance_x2=2.25,
                    double_chance_12=1.20
                )
            ),

            # =========================================================================
            # 7. NIGERIA PREMIER FOOTBALL LEAGUE (NPFL)
            # =========================================================================
            Fixture(
                id="fix-npfl-003",
                league="Nigeria Premier Football League (NPFL)",
                kickoff="Tomorrow, 16:00",
                venue="Enyimba International Stadium, Aba",
                home_team=Team(
                    id="eny",
                    name="Enyimba FC",
                    short_code="ENY",
                    league="NPFL",
                    home_attack_strength=1.35,
                    home_defense_weakness=0.60,
                    away_attack_strength=0.90,
                    away_defense_weakness=1.10,
                    rolling_xg_created=1.55,
                    rolling_xg_conceded=0.65,
                    form="WDWWW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="kan",
                    name="Kano Pillars",
                    short_code="KAN",
                    league="NPFL",
                    home_attack_strength=1.10,
                    home_defense_weakness=0.90,
                    away_attack_strength=0.75,
                    away_defense_weakness=1.30,
                    rolling_xg_created=1.05,
                    rolling_xg_conceded=1.45,
                    form="LDLLW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.48,
                    draw=3.80,
                    away_win=6.20,
                    over_1_5=1.38,
                    over_2_5=2.30,
                    under_2_5=1.58,
                    btts_yes=2.25,
                    btts_no=1.58,
                    double_chance_1x=1.10,
                    double_chance_x2=2.45,
                    double_chance_12=1.22
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.45,
                    draw=3.75,
                    away_win=6.50,
                    over_1_5=1.35,
                    over_2_5=2.25,
                    under_2_5=1.60,
                    btts_yes=2.30,
                    btts_no=1.55,
                    double_chance_1x=1.09,
                    double_chance_x2=2.50,
                    double_chance_12=1.23
                )
            ),
            Fixture(
                id="fix-npfl-030",
                league="Nigeria Premier Football League (NPFL)",
                kickoff="Tomorrow, 16:00",
                venue="Remo Stars Stadium, Ikenne",
                home_team=Team(
                    id="rem",
                    name="Remo Stars",
                    short_code="REM",
                    league="NPFL",
                    home_attack_strength=1.40,
                    home_defense_weakness=0.55,
                    away_attack_strength=0.95,
                    away_defense_weakness=1.05,
                    rolling_xg_created=1.65,
                    rolling_xg_conceded=0.60,
                    form="WWWDW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="3sc",
                    name="Shooting Stars (3SC)",
                    short_code="3SC",
                    league="NPFL",
                    home_attack_strength=1.05,
                    home_defense_weakness=0.95,
                    away_attack_strength=0.70,
                    away_defense_weakness=1.25,
                    rolling_xg_created=0.95,
                    rolling_xg_conceded=1.40,
                    form="LWLDD",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.42,
                    draw=4.00,
                    away_win=7.00,
                    over_1_5=1.35,
                    over_2_5=2.25,
                    under_2_5=1.60,
                    btts_yes=2.35,
                    btts_no=1.52,
                    double_chance_1x=1.08,
                    double_chance_x2=2.65,
                    double_chance_12=1.20
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.40,
                    draw=4.10,
                    away_win=7.25,
                    over_1_5=1.32,
                    over_2_5=2.20,
                    under_2_5=1.62,
                    btts_yes=2.40,
                    btts_no=1.50,
                    double_chance_1x=1.07,
                    double_chance_x2=2.70,
                    double_chance_12=1.19
                )
            ),
            Fixture(
                id="fix-npfl-031",
                league="Nigeria Premier Football League (NPFL)",
                kickoff="Tomorrow, 16:00",
                venue="Nnamdi Azikiwe Stadium, Enugu",
                home_team=Team(
                    id="ran",
                    name="Enugu Rangers",
                    short_code="RAN",
                    league="NPFL",
                    home_attack_strength=1.38,
                    home_defense_weakness=0.60,
                    away_attack_strength=0.90,
                    away_defense_weakness=1.00,
                    rolling_xg_created=1.60,
                    rolling_xg_conceded=0.70,
                    form="WDWWW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="riv",
                    name="Rivers United",
                    short_code="RIV",
                    league="NPFL",
                    home_attack_strength=1.20,
                    home_defense_weakness=0.85,
                    away_attack_strength=0.85,
                    away_defense_weakness=1.15,
                    rolling_xg_created=1.15,
                    rolling_xg_conceded=1.20,
                    form="DWWDL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.62,
                    draw=3.40,
                    away_win=5.20,
                    over_1_5=1.45,
                    over_2_5=2.50,
                    under_2_5=1.48,
                    btts_yes=2.40,
                    btts_no=1.50,
                    double_chance_1x=1.14,
                    double_chance_x2=2.15,
                    double_chance_12=1.28
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.60,
                    draw=3.45,
                    away_win=5.40,
                    over_1_5=1.42,
                    over_2_5=2.45,
                    under_2_5=1.50,
                    btts_yes=2.45,
                    btts_no=1.48,
                    double_chance_1x=1.13,
                    double_chance_x2=2.20,
                    double_chance_12=1.27
                )
            ),
            Fixture(
                id="fix-npfl-032",
                league="Nigeria Premier Football League (NPFL)",
                kickoff="Tomorrow, 16:00",
                venue="New Jos Stadium, Jos",
                home_team=Team(
                    id="pla",
                    name="Plateau United",
                    short_code="PLA",
                    league="NPFL",
                    home_attack_strength=1.35,
                    home_defense_weakness=0.65,
                    away_attack_strength=0.85,
                    away_defense_weakness=1.15,
                    rolling_xg_created=1.50,
                    rolling_xg_conceded=0.75,
                    form="WWLWD",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="ben",
                    name="Bendel Insurance",
                    short_code="BEN",
                    league="NPFL",
                    home_attack_strength=1.00,
                    home_defense_weakness=0.80,
                    away_attack_strength=0.70,
                    away_defense_weakness=1.20,
                    rolling_xg_created=0.90,
                    rolling_xg_conceded=1.30,
                    form="DDWLD",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.55,
                    draw=3.60,
                    away_win=5.80,
                    over_1_5=1.42,
                    over_2_5=2.40,
                    under_2_5=1.52,
                    btts_yes=2.30,
                    btts_no=1.55,
                    double_chance_1x=1.12,
                    double_chance_x2=2.30,
                    double_chance_12=1.25
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.52,
                    draw=3.65,
                    away_win=6.00,
                    over_1_5=1.40,
                    over_2_5=2.35,
                    under_2_5=1.55,
                    btts_yes=2.35,
                    btts_no=1.52,
                    double_chance_1x=1.11,
                    double_chance_x2=2.35,
                    double_chance_12=1.24
                )
            ),

            # =========================================================================
            # 8. PORTUGUESE PRIMEIRA LIGA
            # =========================================================================
            Fixture(
                id="fix-primeira-033",
                league="Portuguese Primeira Liga",
                kickoff="Today, 20:30",
                venue="Estádio José Alvalade, Lisbon",
                home_team=Team(
                    id="spo",
                    name="Sporting CP",
                    short_code="SPO",
                    league="Primeira Liga",
                    home_attack_strength=1.75,
                    home_defense_weakness=0.65,
                    away_attack_strength=1.55,
                    away_defense_weakness=0.75,
                    rolling_xg_created=2.65,
                    rolling_xg_conceded=0.70,
                    form="WWWWW",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="bra",
                    name="SC Braga",
                    short_code="BRA",
                    league="Primeira Liga",
                    home_attack_strength=1.25,
                    home_defense_weakness=1.15,
                    away_attack_strength=1.15,
                    away_defense_weakness=1.25,
                    rolling_xg_created=1.55,
                    rolling_xg_conceded=1.45,
                    form="WDWWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.35,
                    draw=5.20,
                    away_win=7.50,
                    over_1_5=1.14,
                    over_2_5=1.48,
                    under_2_5=2.60,
                    btts_yes=1.75,
                    btts_no=1.98,
                    double_chance_1x=1.08,
                    double_chance_x2=3.10,
                    double_chance_12=1.15
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.34,
                    draw=5.30,
                    away_win=7.80,
                    over_1_5=1.13,
                    over_2_5=1.45,
                    under_2_5=2.65,
                    btts_yes=1.72,
                    btts_no=2.02,
                    double_chance_1x=1.07,
                    double_chance_x2=3.15,
                    double_chance_12=1.14
                )
            ),
            Fixture(
                id="fix-primeira-034",
                league="Portuguese Primeira Liga",
                kickoff="Tomorrow, 18:00",
                venue="Estádio da Luz, Lisbon",
                home_team=Team(
                    id="ben-pt",
                    name="Benfica",
                    short_code="BEN",
                    league="Primeira Liga",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.70,
                    away_attack_strength=1.45,
                    away_defense_weakness=0.80,
                    rolling_xg_created=2.40,
                    rolling_xg_conceded=0.80,
                    form="WWWDW",
                    key_injuries=["Renato Sanches (Thigh)"]
                ),
                away_team=Team(
                    id="gil",
                    name="Gil Vicente",
                    short_code="GIL",
                    league="Primeira Liga",
                    home_attack_strength=1.00,
                    home_defense_weakness=1.30,
                    away_attack_strength=0.85,
                    away_defense_weakness=1.45,
                    rolling_xg_created=1.05,
                    rolling_xg_conceded=1.75,
                    form="DDDWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.24,
                    draw=6.50,
                    away_win=11.00,
                    over_1_5=1.12,
                    over_2_5=1.40,
                    under_2_5=2.85,
                    btts_yes=2.00,
                    btts_no=1.72,
                    double_chance_1x=1.04,
                    double_chance_x2=4.00,
                    double_chance_12=1.10
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.22,
                    draw=6.60,
                    away_win=11.50,
                    over_1_5=1.11,
                    over_2_5=1.38,
                    under_2_5=2.90,
                    btts_yes=1.98,
                    btts_no=1.75,
                    double_chance_1x=1.03,
                    double_chance_x2=4.10,
                    double_chance_12=1.09
                )
            ),
            Fixture(
                id="fix-primeira-035",
                league="Portuguese Primeira Liga",
                kickoff="Tomorrow, 20:30",
                venue="Estádio do Dragão, Porto",
                home_team=Team(
                    id="por",
                    name="FC Porto",
                    short_code="POR",
                    league="Primeira Liga",
                    home_attack_strength=1.60,
                    home_defense_weakness=0.72,
                    away_attack_strength=1.40,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.30,
                    rolling_xg_conceded=0.85,
                    form="WWLWW",
                    key_injuries=["I. Marcano (ACL)"]
                ),
                away_team=Team(
                    id="aro",
                    name="Arouca",
                    short_code="ARO",
                    league="Primeira Liga",
                    home_attack_strength=1.05,
                    home_defense_weakness=1.35,
                    away_attack_strength=0.90,
                    away_defense_weakness=1.45,
                    rolling_xg_created=1.10,
                    rolling_xg_conceded=1.80,
                    form="WLLWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.25,
                    draw=6.20,
                    away_win=10.50,
                    over_1_5=1.13,
                    over_2_5=1.42,
                    under_2_5=2.80,
                    btts_yes=1.95,
                    btts_no=1.78,
                    double_chance_1x=1.05,
                    double_chance_x2=3.85,
                    double_chance_12=1.11
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.24,
                    draw=6.30,
                    away_win=11.00,
                    over_1_5=1.12,
                    over_2_5=1.40,
                    under_2_5=2.85,
                    btts_yes=1.92,
                    btts_no=1.80,
                    double_chance_1x=1.04,
                    double_chance_x2=3.90,
                    double_chance_12=1.10
                )
            ),

            # =========================================================================
            # 9. DUTCH EREDIVISIE
            # =========================================================================
            Fixture(
                id="fix-erediv-036",
                league="Dutch Eredivisie",
                kickoff="Today, 19:00",
                venue="Philips Stadion, Eindhoven",
                home_team=Team(
                    id="psv",
                    name="PSV Eindhoven",
                    short_code="PSV",
                    league="Eredivisie",
                    home_attack_strength=1.85,
                    home_defense_weakness=0.70,
                    away_attack_strength=1.65,
                    away_defense_weakness=0.80,
                    rolling_xg_created=3.10,
                    rolling_xg_conceded=0.80,
                    form="WWWWW",
                    key_injuries=["J. Veerman (Groin)"]
                ),
                away_team=Team(
                    id="twe",
                    name="FC Twente",
                    short_code="TWE",
                    league="Eredivisie",
                    home_attack_strength=1.30,
                    home_defense_weakness=1.05,
                    away_attack_strength=1.15,
                    away_defense_weakness=1.20,
                    rolling_xg_created=1.60,
                    rolling_xg_conceded=1.30,
                    form="DWWDL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.38,
                    draw=5.20,
                    away_win=7.00,
                    over_1_5=1.10,
                    over_2_5=1.38,
                    under_2_5=3.00,
                    btts_yes=1.58,
                    btts_no=2.25,
                    double_chance_1x=1.10,
                    double_chance_x2=2.90,
                    double_chance_12=1.15
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.36,
                    draw=5.30,
                    away_win=7.20,
                    over_1_5=1.09,
                    over_2_5=1.35,
                    under_2_5=3.05,
                    btts_yes=1.55,
                    btts_no=2.30,
                    double_chance_1x=1.09,
                    double_chance_x2=2.95,
                    double_chance_12=1.14
                )
            ),
            Fixture(
                id="fix-erediv-037",
                league="Dutch Eredivisie",
                kickoff="Tomorrow, 13:30",
                venue="De Kuip, Rotterdam",
                home_team=Team(
                    id="fey",
                    name="Feyenoord",
                    short_code="FEY",
                    league="Eredivisie",
                    home_attack_strength=1.65,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.45,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.45,
                    rolling_xg_conceded=0.85,
                    form="WDWDD",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="nac",
                    name="NAC Breda",
                    short_code="NAC",
                    league="Eredivisie",
                    home_attack_strength=0.95,
                    home_defense_weakness=1.40,
                    away_attack_strength=0.80,
                    away_defense_weakness=1.60,
                    rolling_xg_created=0.95,
                    rolling_xg_conceded=2.00,
                    form="LWLLW",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.20,
                    draw=7.20,
                    away_win=12.50,
                    over_1_5=1.08,
                    over_2_5=1.32,
                    under_2_5=3.30,
                    btts_yes=1.85,
                    btts_no=1.85,
                    double_chance_1x=1.03,
                    double_chance_x2=4.40,
                    double_chance_12=1.09
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.19,
                    draw=7.40,
                    away_win=13.00,
                    over_1_5=1.07,
                    over_2_5=1.30,
                    under_2_5=3.35,
                    btts_yes=1.82,
                    btts_no=1.88,
                    double_chance_1x=1.02,
                    double_chance_x2=4.50,
                    double_chance_12=1.08
                )
            ),

            # =========================================================================
            # 10. ENGLISH CHAMPIONSHIP
            # =========================================================================
            Fixture(
                id="fix-champ-038",
                league="English Championship",
                kickoff="Today, 15:00",
                venue="Elland Road, Leeds",
                home_team=Team(
                    id="lee",
                    name="Leeds United",
                    short_code="LEE",
                    league="Championship",
                    home_attack_strength=1.45,
                    home_defense_weakness=0.75,
                    away_attack_strength=1.30,
                    away_defense_weakness=0.85,
                    rolling_xg_created=2.10,
                    rolling_xg_conceded=0.80,
                    form="WWLWD",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="cov",
                    name="Coventry City",
                    short_code="COV",
                    league="Championship",
                    home_attack_strength=1.15,
                    home_defense_weakness=1.15,
                    away_attack_strength=1.05,
                    away_defense_weakness=1.25,
                    rolling_xg_created=1.35,
                    rolling_xg_conceded=1.45,
                    form="LDDWL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.58,
                    draw=4.20,
                    away_win=5.40,
                    over_1_5=1.22,
                    over_2_5=1.70,
                    under_2_5=2.15,
                    btts_yes=1.75,
                    btts_no=2.00,
                    double_chance_1x=1.15,
                    double_chance_x2=2.30,
                    double_chance_12=1.21
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.56,
                    draw=4.25,
                    away_win=5.50,
                    over_1_5=1.20,
                    over_2_5=1.68,
                    under_2_5=2.20,
                    btts_yes=1.72,
                    btts_no=2.05,
                    double_chance_1x=1.14,
                    double_chance_x2=2.35,
                    double_chance_12=1.20
                )
            ),
            Fixture(
                id="fix-champ-039",
                league="English Championship",
                kickoff="Tomorrow, 12:30",
                venue="Turf Moor, Burnley",
                home_team=Team(
                    id="bur",
                    name="Burnley",
                    short_code="BUR",
                    league="Championship",
                    home_attack_strength=1.40,
                    home_defense_weakness=0.70,
                    away_attack_strength=1.25,
                    away_defense_weakness=0.80,
                    rolling_xg_created=1.95,
                    rolling_xg_conceded=0.75,
                    form="WWWDL",
                    key_injuries=[]
                ),
                away_team=Team(
                    id="pne",
                    name="Preston North End",
                    short_code="PNE",
                    league="Championship",
                    home_attack_strength=0.95,
                    home_defense_weakness=1.20,
                    away_attack_strength=0.85,
                    away_defense_weakness=1.35,
                    rolling_xg_created=1.00,
                    rolling_xg_conceded=1.60,
                    form="DDWLL",
                    key_injuries=[]
                ),
                sportybet_odds=BookmakerOdds(
                    bookmaker="SportyBet",
                    home_win=1.52,
                    draw=4.10,
                    away_win=6.20,
                    over_1_5=1.25,
                    over_2_5=1.85,
                    under_2_5=1.95,
                    btts_yes=1.95,
                    btts_no=1.78,
                    double_chance_1x=1.12,
                    double_chance_x2=2.45,
                    double_chance_12=1.22
                ),
                bet9ja_odds=BookmakerOdds(
                    bookmaker="Bet9ja",
                    home_win=1.50,
                    draw=4.15,
                    away_win=6.40,
                    over_1_5=1.24,
                    over_2_5=1.82,
                    under_2_5=2.00,
                    btts_yes=1.92,
                    btts_no=1.80,
                    double_chance_1x=1.11,
                    double_chance_x2=2.50,
                    double_chance_12=1.21
                )
            ),
        ]

    async def get_all_fixtures_with_predictions(self, bankroll_ngn: float = 10000.0) -> List[Fixture]:
        """
        Runs the full AI prediction and value detection pipeline for all fixtures.
        Identifies likely winners, safe anchors, and +EV betting edges.
        """
        if bankroll_ngn in self._enriched_cache:
            return self._enriched_cache[bankroll_ngn]

        enriched_fixtures: List[Fixture] = []

        for f in self._raw_fixtures:
            # 1. Calibrate team ratings with xG and form
            home_cal = XgAnalyzer.adjust_team_parameters(
                f.home_team, is_home=True, key_missing_count=len(f.home_team.key_injuries)
            )
            away_cal = XgAnalyzer.adjust_team_parameters(
                f.away_team, is_home=False, key_missing_count=len(f.away_team.key_injuries)
            )

            # 2. Dixon-Coles goal distribution & outcome probabilities
            home_adv = 1.45 if "NPFL" in f.league else 1.25
            probs = self.dixon_coles.calculate_match_probabilities(
                home_attack=home_cal["attack"],
                away_defense=away_cal["defense"],
                away_attack=away_cal["attack"],
                home_defense=home_cal["defense"],
                league_home_advantage=home_adv
            )

            # 3. Expected Value (+EV) Discovery vs SportyBet and Bet9ja
            ev_bets = EvEngine.evaluate_match_markets(
                home_team=f.home_team.name,
                away_team=f.away_team.name,
                probs=probs,
                sporty_odds=f.sportybet_odds,
                bet9ja_odds=f.bet9ja_odds,
                default_bankroll=bankroll_ngn
            )

            # 4. Contextual AI synthesis (Gemini or heuristic)
            context = await self.gemini.analyze_matchup_context(
                home_team=f.home_team,
                away_team=f.away_team,
                league=f.league,
                ev_bets=[b.model_dump() for b in ev_bets],
                prob_home=probs["prob_home_win"],
                prob_draw=probs["prob_draw"],
                prob_away=probs["prob_away_win"]
            )

            # 5. Statistical Likely Winner determination
            prob_home = probs["prob_home_win"]
            prob_draw = probs["prob_draw"]
            prob_away = probs["prob_away_win"]

            if prob_home >= prob_away and prob_home >= 0.42:
                likely_team = f.home_team.name
                likely_prob = prob_home
                safe_pick = f"{f.home_team.name} Win or Draw (1X)"
                safe_odds = f.sportybet_odds.double_chance_1x or round(1.0 / max(0.1, prob_home + prob_draw) * 0.95, 2)
            elif prob_away > prob_home and prob_away >= 0.42:
                likely_team = f.away_team.name
                likely_prob = prob_away
                safe_pick = f"{f.away_team.name} Win or Draw (X2)"
                safe_odds = f.sportybet_odds.double_chance_x2 or round(1.0 / max(0.1, prob_away + prob_draw) * 0.95, 2)
            else:
                likely_team = "Draw / Even Match"
                likely_prob = max(prob_home, prob_away, prob_draw)
                safe_pick = "Over 1.5 Goals" if probs["prob_over_1_5"] >= 0.70 else "Double Chance 12"
                safe_odds = f.sportybet_odds.over_1_5 or 1.22

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
                    f"({confidence_tier}). xG expectancy: {f.home_team.name} ({probs['expected_goals_home']:.2f}) vs "
                    f"{f.away_team.name} ({probs['expected_goals_away']:.2f}). Safe anchor: {safe_pick} ({safe_odds:.2f})."
                )
            else:
                verdict = (
                    f"Evenly matched statistics (xG {probs['expected_goals_home']:.2f} vs {probs['expected_goals_away']:.2f}). "
                    f"High variance matchup; safest play is {safe_pick} ({safe_odds:.2f})."
                )

            pred_detail = PredictionDetail(
                home_team=f.home_team.name,
                away_team=f.away_team.name,
                league=f.league,
                kickoff_time=f.kickoff,
                expected_goals_home=probs["expected_goals_home"],
                expected_goals_away=probs["expected_goals_away"],
                prob_home_win=probs["prob_home_win"],
                prob_draw=probs["prob_draw"],
                prob_away_win=probs["prob_away_win"],
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
                recommended_safe_odds=round(safe_odds, 2)
            )

            fixture_copy = f.model_copy()
            fixture_copy.prediction = pred_detail
            enriched_fixtures.append(fixture_copy)

        self._enriched_cache[bankroll_ngn] = enriched_fixtures
        return enriched_fixtures

    async def get_fixture_by_id(self, fixture_id: str, bankroll_ngn: float = 10000.0) -> Optional[Fixture]:
        all_fixtures = await self.get_all_fixtures_with_predictions(bankroll_ngn)
        for f in all_fixtures:
            if f.id == fixture_id:
                return f
        return None
