import math
import pytest
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.services.accas_optimizer import AccasOptimizer
from apps.api.app.services.accas_optimizer import MAX_LEGS
from apps.api.app.services.tracker_service import TrackerService
from apps.api.app.models.schemas import RiskLevel

@pytest.mark.asyncio
async def test_fixture_enrichment_and_prediction():
    """Verify that fixture service generates full predictions and EV plays."""
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=15000.0)
    
    assert len(fixtures) >= 5
    for f in fixtures:
        assert f.prediction is not None
        assert f.prediction.expected_goals_home > 0
        assert f.prediction.expected_goals_away > 0
        assert f.prediction.gemini_tactical_summary != ""
        # Value bets are only ever priced against real quoted odds
        for vb in f.prediction.value_bets:
            assert vb.bookmaker in ("Market Average", "Best Price")
            assert vb.expected_value_pct >= 2.0  # the test model's value policy threshold
    assert any(f.prediction.value_bets for f in fixtures)

@pytest.mark.asyncio
async def test_target_odds_slip_uses_real_prices_and_honest_probability():
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=10000.0)
    slip = AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures, target_odds=3.0, risk_level=RiskLevel.BALANCED, bankroll_ngn=10000.0, max_legs=4
    )
    assert 2 <= len(slip.legs) <= 4
    assert slip.sportybet_code is None and slip.bet9ja_code is None  # no fake booking codes
    assert slip.total_odds == pytest.approx(math.prod(l.odds for l in slip.legs), abs=0.02)
    assert slip.win_probability == pytest.approx(math.prod(l.model_probability for l in slip.legs), rel=1e-3)
    assert f"{slip.win_probability:.1%}" in slip.cut_1_warning
    assert slip.recommended_stake_ngn == 100.0  # at most 1% of bankroll (min ₦100)
    assert "18+" in slip.whatsapp_share_text
def test_tracker_service_reads_the_verifiable_ledger():
    """The public track record comes only from the hash-chained prediction ledger."""
    tracker = TrackerService()
    stats = tracker.get_public_stats()
    assert stats.total_bets == len(stats.entries)
    assert stats.wins + stats.losses + stats.voids <= stats.total_bets
    assert tracker.verify()["valid"] is True
    assert not hasattr(tracker, "record_bet_result")  # no manual result entry

@pytest.mark.asyncio
async def test_likely_winner_statistics():
    """Verify that every fixture outputs the statistically projected winner and verdict."""
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=10000.0)
    assert len(fixtures) >= 20
    for f in fixtures:
        p = f.prediction
        assert p is not None
        assert p.likely_winner_team != ""
        assert p.likely_winner_prob > 0.30
        assert p.likely_winner_confidence in ["Banker (70%+)", "Strong Favorite", "Moderate Edge", "Evenly Contested"]
        assert len(p.statistical_verdict) > 10
        assert p.recommended_safe_pick != ""
        assert p.recommended_safe_odds >= 1.01

@pytest.mark.asyncio
async def test_multi_game_slips_are_diverse_capped_and_only_priced():
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=10000.0)
    by_id = {f.id: f for f in fixtures}

    safest = AccasOptimizer.build_smart_accumulator(fixtures=fixtures, target_legs=10, strategy="safest")
    assert len(safest.legs) == 10
    assert len(safest.leagues_covered) >= 4
    for leg in safest.legs:
        f = by_id[leg.fixture_id]
        assert f.sportybet_odds.bookmaker == "Market Average"
        assert leg.model_probability >= 0.5 and ("1X" in leg.market or "X2" in leg.market)

    straight = AccasOptimizer.build_smart_accumulator(fixtures=fixtures, target_legs=5, strategy="straight_win")
    for leg in straight.legs:
        f = by_id[leg.fixture_id]
        assert leg.odds in (f.sportybet_odds.home_win, f.sportybet_odds.away_win)

    long_slip = AccasOptimizer.build_smart_accumulator(fixtures=fixtures, target_legs=30, strategy="safest_winners")
    assert len(long_slip.legs) <= MAX_LEGS
    assert f"capped at {MAX_LEGS}" in long_slip.recommended_game_count_note