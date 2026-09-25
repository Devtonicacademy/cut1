import pytest
from apps.api.app.services.ev_engine import EvEngine
from apps.api.app.services.kelly_engine import KellyEngine
from apps.api.app.models.schemas import RiskLevel, ValueBetItem, MarketType

def test_ev_calculation():
    """Verify expected value (+EV) logic."""
    # Model probability = 60%, Bookmaker Odds = 2.00 -> EV = (0.60 * 2.00) - 1 = +0.20 (+20%)
    ev = EvEngine.calculate_ev(0.60, 2.00)
    assert pytest.approx(ev, abs=1e-4) == 0.20

    # Model probability = 40%, Bookmaker Odds = 2.00 -> EV = (0.40 * 2.00) - 1 = -0.20 (-20%)
    ev_neg = EvEngine.calculate_ev(0.40, 2.00)
    assert pytest.approx(ev_neg, abs=1e-4) == -0.20

def test_fractional_kelly_bounds():
    """Verify Fractional Kelly single bet caps."""
    # Extreme edge: 90% probability at 3.00 odds
    stake_conservative = KellyEngine.calculate_single_kelly(0.90, 3.00, RiskLevel.CONSERVATIVE)
    assert stake_conservative <= KellyEngine.MAX_SINGLE_STAKE_PCT[RiskLevel.CONSERVATIVE]
    assert stake_conservative > 0

    # Negative EV should output 0 stake
    stake_zero = KellyEngine.calculate_single_kelly(0.30, 2.00, RiskLevel.CONSERVATIVE)
    assert stake_zero == 0.0

def test_bankroll_allocation_rounding_and_caps():
    """Verify Naira bankroll allocation never exceeds portfolio cap and rounds to practical Naira."""
    bets = [
        ValueBetItem(
            market=MarketType.HOME_WIN,
            market_name="Arsenal Win",
            selection="Arsenal",
            bookmaker="SportyBet",
            market_odds=1.90,
            fair_odds=1.65,
            model_probability=0.606,
            implied_probability=0.526,
            expected_value_pct=15.1,
            recommended_stake_pct=2.5,
            recommended_stake_ngn=500.0,
            confidence_tier="High Value (Gold)",
            reasoning="Strong xG dominance"
        ),
        ValueBetItem(
            market=MarketType.OVER_1_5,
            market_name="Over 1.5 Goals",
            selection="Over 1.5",
            bookmaker="Bet9ja",
            market_odds=1.35,
            fair_odds=1.20,
            model_probability=0.833,
            implied_probability=0.741,
            expected_value_pct=12.5,
            recommended_stake_pct=2.5,
            recommended_stake_ngn=500.0,
            confidence_tier="High Value (Gold)",
            reasoning="High goal expectancy"
        )
    ]

    bankroll = 20000.0 # ₦20,000
    allocation = KellyEngine.allocate_bankroll(bankroll, RiskLevel.CONSERVATIVE, bets)
    
    assert allocation.bankroll_ngn == 20000.0
    assert allocation.total_staked_ngn <= bankroll * KellyEngine.MAX_PORTFOLIO_RISK_PCT[RiskLevel.CONSERVATIVE]
    assert allocation.remaining_bankroll_ngn == bankroll - allocation.total_staked_ngn
    assert len(allocation.allocations) == 2
    
    for item in allocation.allocations:
        assert item.recommended_stake_ngn >= KellyEngine.MIN_STAKE_NGN
        assert item.recommended_stake_ngn % 50.0 == 0 # Clean 50 Naira multiple
