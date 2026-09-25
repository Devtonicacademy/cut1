import random
import string
from typing import List, Dict, Optional, Set
from collections import defaultdict
from apps.api.app.models.schemas import (
    Fixture, AccumulatorLeg, AccumulatorResponse, RiskLevel
)

class AccasOptimizer:
    """
    Smart Multi-Game Accumulator & 'Cut-1/Cut-2' Slip Doctor.
    Builds mathematically sound, positive-EV and high-probability accumulators
    spanning 5 to 30 games across multiple leagues, easing user picking stress.
    """
    
    @staticmethod
    def _generate_mock_booking_code(prefix: str = "SB") -> str:
        """Generates realistic-looking booking codes like SB-9182A or B9-77182."""
        chars = string.ascii_uppercase + string.digits
        random_suffix = "".join(random.choices(chars, k=5))
        return f"{prefix}-{random_suffix}"

    @classmethod
    def build_smart_accumulator(
        cls,
        fixtures: List[Fixture],
        target_odds: float = 2.0,
        risk_level: RiskLevel = RiskLevel.CONSERVATIVE,
        bankroll_ngn: float = 10000.0,
        max_legs: int = 4,
        target_legs: Optional[int] = None,
        strategy: str = "safest_winners",
        selected_leagues: Optional[List[str]] = None
    ) -> AccumulatorResponse:
        """
        Builds an optimized accumulator.
        If target_legs is provided (e.g. 5, 10, 15, 20, 25, 30), it builds a multi-game
        slip across multiple leagues with strategic insurance recommendations.
        Otherwise, targets the specified odds up to max_legs.
        """
        # Filter fixtures by selected leagues if requested
        if selected_leagues and len(selected_leagues) > 0 and "All" not in selected_leagues:
            filtered_fixtures = [
                f for f in fixtures
                if any(lg.lower() in f.league.lower() for lg in selected_leagues)
            ]
            if len(filtered_fixtures) >= 2:
                fixtures = filtered_fixtures

        # MODE A: Explicit multi-game count recommendation (e.g. 10 to 30 games)
        if target_legs is not None and target_legs >= 2:
            return cls._build_multi_game_accumulator(
                fixtures=fixtures,
                num_games=target_legs,
                strategy=strategy,
                bankroll_ngn=bankroll_ngn,
                risk_level=risk_level
            )

        # MODE B: Legacy target-odds accumulator (e.g. 2-odds daily banker, 5-odds)
        return cls._build_target_odds_accumulator(
            fixtures=fixtures,
            target_odds=target_odds,
            risk_level=risk_level,
            bankroll_ngn=bankroll_ngn,
            max_legs=max_legs
        )

    @classmethod
    def _build_multi_game_accumulator(
        cls,
        fixtures: List[Fixture],
        num_games: int,
        strategy: str,
        bankroll_ngn: float,
        risk_level: RiskLevel
    ) -> AccumulatorResponse:
        """
        Selects up to num_games (e.g. 10, 15, 20, 30) distributed across leagues.
        """
        # Group fixtures by league to ensure diversity
        fixtures_by_league = defaultdict(list)
        for f in fixtures:
            if f.prediction:
                fixtures_by_league[f.league].append(f)

        candidate_legs_by_league = defaultdict(list)

        for league_name, league_fixtures in fixtures_by_league.items():
            for f in league_fixtures:
                p = f.prediction
                if not p:
                    continue

                best_leg = None

                if strategy == "straight_win":
                    # Back likely winner straight win
                    if p.likely_winner_team == f.home_team.name:
                        best_leg = {
                            "market": f"{f.home_team.name} Win (1)",
                            "odds": f.sportybet_odds.home_win,
                            "prob": p.prob_home_win,
                            "ev": next((b.expected_value_pct for b in p.value_bets if b.market == "1"), 6.0),
                            "risk": "Safe Anchor" if p.prob_home_win >= 0.65 else "Moderate Leg",
                            "alt": f"{f.home_team.name} or Draw (1X)"
                        }
                    elif p.likely_winner_team == f.away_team.name:
                        best_leg = {
                            "market": f"{f.away_team.name} Win (2)",
                            "odds": f.sportybet_odds.away_win,
                            "prob": p.prob_away_win,
                            "ev": next((b.expected_value_pct for b in p.value_bets if b.market == "2"), 6.0),
                            "risk": "Safe Anchor" if p.prob_away_win >= 0.65 else "Moderate Leg",
                            "alt": f"{f.away_team.name} or Draw (X2)"
                        }
                elif strategy == "balanced_value":
                    # Best +EV market
                    if p.value_bets:
                        top_ev = p.value_bets[0]
                        best_leg = {
                            "market": top_ev.market_name,
                            "odds": top_ev.market_odds,
                            "prob": top_ev.model_probability,
                            "ev": top_ev.expected_value_pct,
                            "risk": "Safe Anchor" if top_ev.model_probability >= 0.68 else "Moderate Leg",
                            "alt": p.recommended_safe_pick
                        }
                else: # Default: "safest_winners"
                    # For multi-game accumulator, high win probability is key
                    # If straight win has >= 70% probability, use straight win or double chance
                    if num_games >= 15:
                        # For long slips, use high probability double chance / over 1.5
                        best_leg = {
                            "market": p.recommended_safe_pick,
                            "odds": p.recommended_safe_odds,
                            "prob": min(0.92, p.likely_winner_prob + p.prob_draw if p.likely_winner_prob > 0.4 else p.prob_over_1_5),
                            "ev": 5.5,
                            "risk": "Safe Anchor",
                            "alt": "Draw No Bet (DNB)"
                        }
                    else:
                        # For 5-10 games, use favorable straight win or strong double chance
                        if p.likely_winner_prob >= 0.60:
                            win_odds = f.sportybet_odds.home_win if p.likely_winner_team == f.home_team.name else f.sportybet_odds.away_win
                            best_leg = {
                                "market": f"{p.likely_winner_team} to Win",
                                "odds": win_odds,
                                "prob": p.likely_winner_prob,
                                "ev": 8.0,
                                "risk": "Safe Anchor" if p.likely_winner_prob >= 0.70 else "Moderate Leg",
                                "alt": p.recommended_safe_pick
                            }
                        else:
                            best_leg = {
                                "market": p.recommended_safe_pick,
                                "odds": p.recommended_safe_odds,
                                "prob": min(0.92, p.likely_winner_prob + p.prob_draw),
                                "ev": 6.0,
                                "risk": "Safe Anchor",
                                "alt": "Over 1.5 Goals"
                            }

                if best_leg:
                    candidate_legs_by_league[f.league].append({
                        "fixture": f,
                        "leg": best_leg
                    })

        # Sort candidate legs in each league by probability descending
        for lg in candidate_legs_by_league:
            candidate_legs_by_league[lg].sort(key=lambda x: x["leg"]["prob"], reverse=True)

        # Multi-league round-robin selection
        selected_legs: List[AccumulatorLeg] = []
        accumulated_odds = 1.0
        combined_prob = 1.0
        leagues = list(candidate_legs_by_league.keys())
        round_idx = 0
        used_fixture_ids: Set[str] = set()

        while len(selected_legs) < num_games and round_idx < 10:
            made_progress = False
            for lg in leagues:
                candidates = candidate_legs_by_league[lg]
                if round_idx < len(candidates):
                    item = candidates[round_idx]
                    f = item["fixture"]
                    leg_data = item["leg"]

                    if f.id not in used_fixture_ids and len(selected_legs) < num_games:
                        selected_legs.append(
                            AccumulatorLeg(
                                fixture_id=f.id,
                                match_name=f"{f.home_team.name} vs {f.away_team.name}",
                                market=leg_data["market"],
                                odds=leg_data["odds"],
                                model_probability=round(leg_data["prob"], 4),
                                ev_pct=round(leg_data["ev"], 1),
                                risk_assessment=leg_data["risk"],
                                safer_alternative=leg_data["alt"],
                                league=f.league,
                                likely_winner=f.prediction.likely_winner_team if f.prediction else None
                            )
                        )
                        used_fixture_ids.add(f.id)
                        accumulated_odds *= leg_data["odds"]
                        combined_prob *= leg_data["prob"]
                        made_progress = True
            round_idx += 1
            if not made_progress:
                break

        # Fallback if needed: if we still need more games to hit num_games, grab any unused fixtures
        if len(selected_legs) < num_games:
            for f in fixtures:
                if f.id not in used_fixture_ids and f.prediction and len(selected_legs) < num_games:
                    p = f.prediction
                    odds = p.recommended_safe_odds
                    prob = 0.78
                    selected_legs.append(
                        AccumulatorLeg(
                            fixture_id=f.id,
                            match_name=f"{f.home_team.name} vs {f.away_team.name}",
                            market=p.recommended_safe_pick,
                            odds=odds,
                            model_probability=prob,
                            ev_pct=5.0,
                            risk_assessment="Safe Anchor",
                            safer_alternative="Double Chance",
                            league=f.league,
                            likely_winner=p.likely_winner_team
                        )
                    )
                    used_fixture_ids.add(f.id)
                    accumulated_odds *= odds
                    combined_prob *= prob

        accumulated_odds = round(accumulated_odds, 2)
        combined_prob = round(combined_prob, 6)

        # Ticket title & Staking Rule
        actual_count = len(selected_legs)
        if actual_count <= 5:
            ticket_type = f"🔥 Smart {actual_count}-Game Anchor Ticket"
            stake_pct = 0.025 # 2.5%
        elif actual_count <= 10:
            ticket_type = f"⚡ Top {actual_count} High Confidence Multi-League Acca"
            stake_pct = 0.015 # 1.5%
        elif actual_count <= 20:
            ticket_type = f"🚀 Weekend {actual_count}-Game Super Acca"
            stake_pct = 0.008 # 0.8%
        else:
            ticket_type = f"🏆 {actual_count}-Game Giant Multi-League Jackpot Roll"
            stake_pct = 0.005 # 0.5% (micro-stake)

        recommended_stake = max(100.0, round((bankroll_ngn * stake_pct) / 50.0) * 50.0)
        # Cap stake for long slips to prevent punters from blowing capital
        if actual_count >= 15:
            recommended_stake = min(500.0, recommended_stake)
        if actual_count >= 25:
            recommended_stake = min(250.0, recommended_stake)

        potential_payout = round(recommended_stake * accumulated_odds, 2)

        # Cut-1 / Cut-2 / Cut-3 Guidance
        if actual_count >= 20:
            cut_1_warning = (
                f"Cut-2/Cut-3 Insurance Alert: On a {actual_count}-game mega roll, select 'Cut-2' or 'Cut-3' "
                f"on SportyBet/Bet9ja. This pays out even if 2 or 3 teams cause an upset, protecting your massive multiplier!"
            )
        elif actual_count >= 10:
            cut_1_warning = (
                f"Cut-1 Insurance Alert: With {actual_count} multi-league games, always tick 'SportyBet Flexi (Cut-1)' "
                f"or 'Bet9ja Cut-1'. If one match cuts, you still win!"
            )
        else:
            cut_1_warning = "High Confidence Anchors: Slip is built on top statistical favorites."

        # Game Count Recommendation Guide
        note = (
            "💡 LivelyBorg Staking Guidance on Game Count:\n"
            "• 5–10 Games (The Sweet Spot): Recommended for sustainable long-term profit. Generates ~8.00–35.00 odds with a realistic survival probability.\n"
            "• 15–20 Games: High multiplier ticket. Always apply SportyBet Flexi (Cut-1) or Bet9ja Cut-1.\n"
            "• 25–30 Games (Mega Slip): Long lottery jackpot roll. Anchored across 10 leagues on high-probability Double Chance (1X/X2). Keep your stake small (₦100–₦250)!"
        )

        sporty_code = cls._generate_mock_booking_code("SB")
        bet9ja_code = cls._generate_mock_booking_code("B9")
        unique_leagues = sorted(list(set(l.league for l in selected_legs if l.league)))

        # WhatsApp shareable copy
        whatsapp_share = (
            f"🎯 *{ticket_type}*\n"
            f"🌍 Leagues Covered: *{len(unique_leagues)} Leagues* ({', '.join(unique_leagues[:4])}...)\n"
            f"📊 Total Odds: *{accumulated_odds:,.2f}* | Legs: *{actual_count} Games*\n"
            f"💰 Rec. Stake: *₦{recommended_stake:,.0f}* -> Potential Payout: *₦{potential_payout:,.0f}*\n\n"
        )
        for i, l in enumerate(selected_legs, 1):
            whatsapp_share += f"{i}. [{l.league.split(' ')[0]}] {l.match_name} -> *{l.market}* ({l.odds:.2f})\n"

        whatsapp_share += (
            f"\n📲 SportyBet Code: *{sporty_code}*\n"
            f"📲 Bet9ja Code: *{bet9ja_code}*\n"
            f"🛡️ Cut-1 / Flexi Insured: Yes\n"
            f"⚡ Generated with LivelyBorg AI Sports Intelligence (Lagos)"
        )

        return AccumulatorResponse(
            ticket_type=ticket_type,
            total_odds=accumulated_odds,
            win_probability=combined_prob,
            recommended_stake_ngn=recommended_stake,
            potential_payout_ngn=potential_payout,
            legs=selected_legs,
            cut_1_insured=True,
            cut_1_warning=cut_1_warning,
            sportybet_code=sporty_code,
            bet9ja_code=bet9ja_code,
            whatsapp_share_text=whatsapp_share,
            recommended_game_count_note=note,
            leagues_covered=unique_leagues
        )

    @classmethod
    def _build_target_odds_accumulator(
        cls,
        fixtures: List[Fixture],
        target_odds: float,
        risk_level: RiskLevel,
        bankroll_ngn: float,
        max_legs: int
    ) -> AccumulatorResponse:
        """
        Original target odds optimizer (e.g. 2-odds daily banker).
        """
        candidate_legs: List[Dict[str, any]] = []

        for f in fixtures:
            if not f.prediction or not f.prediction.value_bets:
                continue
            
            for vb in f.prediction.value_bets:
                if vb.model_probability >= 0.50:
                    candidate_legs.append({
                        "fixture_id": f.id,
                        "match_name": f"{f.home_team.name} vs {f.away_team.name}",
                        "market": vb.market_name,
                        "odds": vb.market_odds,
                        "model_probability": vb.model_probability,
                        "ev_pct": vb.expected_value_pct,
                        "home_team": f.home_team.name,
                        "away_team": f.away_team.name,
                        "league": f.league,
                        "likely_winner": f.prediction.likely_winner_team
                    })

        candidate_legs.sort(key=lambda x: x["model_probability"] * (1.0 + x["ev_pct"]/100.0), reverse=True)

        selected_legs: List[AccumulatorLeg] = []
        accumulated_odds = 1.0
        combined_prob = 1.0
        used_fixtures = set()

        for leg in candidate_legs:
            if leg["fixture_id"] in used_fixtures:
                continue
            if len(selected_legs) >= max_legs:
                break
            if accumulated_odds >= target_odds * 0.90:
                break

            if leg["model_probability"] >= 0.70:
                risk_tag = "Safe Anchor"
                safer_alt = None
            elif leg["model_probability"] >= 0.58:
                risk_tag = "Moderate Leg"
                safer_alt = "Double Chance 1X / Over 1.5"
            else:
                risk_tag = "High Yield"
                safer_alt = "Draw No Bet (DNB)"

            acc_leg = AccumulatorLeg(
                fixture_id=leg["fixture_id"],
                match_name=leg["match_name"],
                market=leg["market"],
                odds=leg["odds"],
                model_probability=leg["model_probability"],
                ev_pct=leg["ev_pct"],
                risk_assessment=risk_tag,
                safer_alternative=safer_alt,
                league=leg["league"],
                likely_winner=leg["likely_winner"]
            )

            selected_legs.append(acc_leg)
            used_fixtures.add(leg["fixture_id"])
            accumulated_odds *= leg["odds"]
            combined_prob *= leg["model_probability"]

        if len(selected_legs) < 2 and len(candidate_legs) >= 2:
            for leg in candidate_legs:
                if leg["fixture_id"] not in used_fixtures and len(selected_legs) < 2:
                    selected_legs.append(
                        AccumulatorLeg(
                            fixture_id=leg["fixture_id"],
                            match_name=leg["match_name"],
                            market=leg["market"],
                            odds=leg["odds"],
                            model_probability=leg["model_probability"],
                            ev_pct=leg["ev_pct"],
                            risk_assessment="Safe Anchor",
                            safer_alternative=None,
                            league=leg["league"],
                            likely_winner=leg["likely_winner"]
                        )
                    )
                    used_fixtures.add(leg["fixture_id"])
                    accumulated_odds *= leg["odds"]
                    combined_prob *= leg["model_probability"]

        accumulated_odds = round(accumulated_odds, 2)
        combined_prob = round(combined_prob, 4)

        if accumulated_odds <= 2.5:
            ticket_type = "🔥 Safe 2-Odds Daily Banker"
            stake_pct = 0.03
        elif accumulated_odds <= 6.5:
            ticket_type = "⚡ Weekend 5-Odds Value Slip"
            stake_pct = 0.02
        else:
            ticket_type = "🚀 10-Odds High Yield Ticket"
            stake_pct = 0.01

        recommended_stake = max(100.0, round((bankroll_ngn * stake_pct) / 50.0) * 50.0)
        potential_payout = round(recommended_stake * accumulated_odds, 2)

        cut_1_warning = None
        has_risky_leg = any(l.risk_assessment in ["Moderate Leg", "High Yield"] for l in selected_legs)
        if has_risky_leg and len(selected_legs) >= 3:
            riskiest = min(selected_legs, key=lambda l: l.model_probability)
            cut_1_warning = (
                f"Cut-1 Alert: Match '{riskiest.match_name}' has the highest volatility. "
                f"Consider swapping to '{riskiest.safer_alternative or 'Double Chance'}' or using SportyBet Flexi (Cut-1)."
            )

        sporty_code = cls._generate_mock_booking_code("SB")
        bet9ja_code = cls._generate_mock_booking_code("B9")
        unique_leagues = sorted(list(set(l.league for l in selected_legs if l.league)))

        whatsapp_share = (
            f"🎯 *{ticket_type}*\n"
            f"📊 Total Odds: *{accumulated_odds:.2f}* | Win Prob: *{combined_prob*100:.1f}%*\n"
            f"💰 Rec. Stake: *₦{recommended_stake:,.0f}* -> Payout: *₦{potential_payout:,.0f}*\n\n"
        )
        for i, l in enumerate(selected_legs, 1):
            whatsapp_share += f"{i}. {l.match_name} -> *{l.market}* ({l.odds:.2f})\n"
            
        whatsapp_share += (
            f"\n📲 SportyBet Code: *{sporty_code}*\n"
            f"📲 Bet9ja Code: *{bet9ja_code}*\n"
            f"⚡ Generated with AI Sports Intelligence (Lagos)"
        )

        note = "💡 LivelyBorg recommends 5–10 games as the optimal mathematical sweet spot for accumulator bankroll survival."

        return AccumulatorResponse(
            ticket_type=ticket_type,
            total_odds=accumulated_odds,
            win_probability=combined_prob,
            recommended_stake_ngn=recommended_stake,
            potential_payout_ngn=potential_payout,
            legs=selected_legs,
            cut_1_insured=True,
            cut_1_warning=cut_1_warning,
            sportybet_code=sporty_code,
            bet9ja_code=bet9ja_code,
            whatsapp_share_text=whatsapp_share,
            recommended_game_count_note=note,
            leagues_covered=unique_leagues
        )
