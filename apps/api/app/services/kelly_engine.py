from typing import List
from apps.api.app.models.schemas import RiskLevel, ValueBetItem, BankrollAllocation

class KellyEngine:
    """
    Fractional Kelly Criterion staking and portfolio bankroll allocation engine.
    Calibrated specifically for Nigerian Naira bankroll preservation and compounding.
    """
    KELLY_FRACTIONS = {
        RiskLevel.CONSERVATIVE: 0.15, # 15% fractional Kelly
        RiskLevel.BALANCED: 0.25,     # 25% quarter Kelly
        RiskLevel.AGGRESSIVE: 0.40    # 40% fractional Kelly
    }

    MAX_SINGLE_STAKE_PCT = {
        RiskLevel.CONSERVATIVE: 0.025, # 2.5% max on any single game
        RiskLevel.BALANCED: 0.045,     # 4.5% max on any single game
        RiskLevel.AGGRESSIVE: 0.070    # 7.0% max on any single game
    }

    MAX_PORTFOLIO_RISK_PCT = {
        RiskLevel.CONSERVATIVE: 0.12,  # 12% total portfolio risk
        RiskLevel.BALANCED: 0.20,      # 20% total portfolio risk
        RiskLevel.AGGRESSIVE: 0.35     # 35% total portfolio risk
    }

    MIN_STAKE_NGN = 100.0 # Standard minimum stake in Nigeria

    @classmethod
    def calculate_single_kelly(
        cls,
        prob: float,
        odds: float,
        risk_level: RiskLevel
    ) -> float:
        """
        Calculates raw fractional Kelly stake fraction for a single bet.
        f* = [(b*p - q) / b] * fraction
        """
        b = odds - 1.0
        if b <= 0 or prob <= 0:
            return 0.0

        q = 1.0 - prob
        full_kelly = (b * prob - q) / b

        if full_kelly <= 0:
            return 0.0

        fraction = cls.KELLY_FRACTIONS.get(risk_level, 0.20)
        fractional_kelly = full_kelly * fraction
        
        # Cap at maximum allowed single bet percentage
        max_cap = cls.MAX_SINGLE_STAKE_PCT.get(risk_level, 0.03)
        return min(max_cap, fractional_kelly)

    @classmethod
    def allocate_bankroll(
        cls,
        bankroll_ngn: float,
        risk_level: RiskLevel,
        selected_bets: List[ValueBetItem]
    ) -> BankrollAllocation:
        """
        Calculates optimal simultaneous stake distribution across multiple value bets
        without over-leveraging the user's capital.
        """
        if not selected_bets or bankroll_ngn <= 0:
            return BankrollAllocation(
                bankroll_ngn=bankroll_ngn,
                risk_level=risk_level,
                total_staked_ngn=0.0,
                remaining_bankroll_ngn=bankroll_ngn,
                expected_profit_ngn=0.0,
                allocations=[]
            )

        raw_stakes = []
        total_raw_pct = 0.0

        for bet in selected_bets:
            k_pct = cls.calculate_single_kelly(bet.model_probability, bet.market_odds, risk_level)
            raw_stakes.append((bet, k_pct))
            total_raw_pct += k_pct

        # Check against maximum portfolio allocation cap
        portfolio_cap = cls.MAX_PORTFOLIO_RISK_PCT.get(risk_level, 0.15)
        scale_factor = 1.0
        if total_raw_pct > portfolio_cap and total_raw_pct > 0:
            scale_factor = portfolio_cap / total_raw_pct

        allocations: List[ValueBetItem] = []
        total_staked = 0.0
        expected_profit = 0.0

        for bet, k_pct in raw_stakes:
            final_pct = k_pct * scale_factor
            stake_amount = bankroll_ngn * final_pct
            
            # Practical rounding for Nigerian market (nearest 50 Naira)
            if stake_amount > cls.MIN_STAKE_NGN:
                rounded_stake = round(stake_amount / 50.0) * 50.0
            elif stake_amount > 0:
                rounded_stake = cls.MIN_STAKE_NGN
            else:
                rounded_stake = 0.0

            # Update bet item with exact personalized values
            updated_bet = bet.model_copy()
            updated_bet.recommended_stake_pct = round(final_pct * 100.0, 2)
            updated_bet.recommended_stake_ngn = float(rounded_stake)
            allocations.append(updated_bet)

            total_staked += rounded_stake
            expected_profit += rounded_stake * (bet.expected_value_pct / 100.0)

        remaining = max(0.0, bankroll_ngn - total_staked)

        return BankrollAllocation(
            bankroll_ngn=bankroll_ngn,
            risk_level=risk_level,
            total_staked_ngn=round(total_staked, 2),
            remaining_bankroll_ngn=round(remaining, 2),
            expected_profit_ngn=round(expected_profit, 2),
            allocations=allocations
        )
