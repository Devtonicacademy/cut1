import pytest
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.services.accas_optimizer import AccasOptimizer
from apps.api.app.services.admin_service import AdminService
from apps.api.app.services.tracker_service import TrackerService
from apps.api.app.models.schemas import RiskLevel, BetStatus, AdminBroadcastRequest

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
        assert len(f.prediction.value_bets) > 0
        assert f.prediction.gemini_tactical_summary != ""

@pytest.mark.asyncio
async def test_smart_accumulator_and_cut_1():
    """Verify smart accumulator generation, booking codes, and WhatsApp share copy."""
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=10000.0)
    
    acc_response = AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures,
        target_odds=3.0,
        risk_level=RiskLevel.BALANCED,
        bankroll_ngn=10000.0,
        max_legs=4
    )

    assert acc_response.total_odds >= 1.5
    assert len(acc_response.legs) >= 2
    assert acc_response.sportybet_code.startswith("SB-")
    assert acc_response.bet9ja_code.startswith("B9-")
    assert "SportyBet Code" in acc_response.whatsapp_share_text
    assert acc_response.recommended_stake_ngn >= 100.0

def test_admin_broadcast_and_ladder_challenge():
    """Verify admin multi-channel broadcasting and ladder challenge progression."""
    admin = AdminService()
    req = AdminBroadcastRequest(
        title="🔥 Weekend 5-Odds VIP Slip Dropped!",
        message="AI confidence 84%. Use fractional Kelly 2.5% stake.",
        sportybet_code="SB-WKD82",
        bet9ja_code="B9-99120",
        channels=["web", "telegram"]
    )
    res = admin.broadcast_codes(req)
    assert res["success"] is True
    assert "broadcast_id" in res

    # Check ladder challenge
    ladder = admin.get_ladder_challenge_status()
    assert ladder["starting_amount_ngn"] == 1000.0
    assert ladder["current_bankroll_ngn"] > 1000.0
    assert len(ladder["history"]) >= 4

def test_tracker_service_roi():
    """Verify public track record calculations."""
    tracker = TrackerService()
    stats = tracker.get_public_stats()
    assert stats.total_bets >= 5
    assert stats.win_rate_pct > 50.0
    assert stats.roi_pct > 0.0
    assert stats.current_winning_streak >= 0

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
async def test_multi_game_accumulators_10_20_30_legs():
    """Verify multi-game accumulator builder for 10, 20, and 25+ games across leagues."""
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions(bankroll_ngn=10000.0)

    # Test 10-game accumulator
    acca_10 = AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures,
        bankroll_ngn=10000.0,
        target_legs=10,
        strategy="safest_winners"
    )
    assert len(acca_10.legs) == 10
    assert acca_10.total_odds > 1.5
    assert acca_10.sportybet_code.startswith("SB-")
    assert acca_10.bet9ja_code.startswith("B9-")
    assert acca_10.leagues_covered is not None
    assert len(acca_10.leagues_covered) >= 4 # Spans 4+ different leagues
    assert acca_10.recommended_game_count_note is not None
    assert "Sweet Spot" in acca_10.recommended_game_count_note

    # Test 20-game accumulator
    acca_20 = AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures,
        bankroll_ngn=10000.0,
        target_legs=20,
        strategy="safest_winners"
    )
    assert len(acca_20.legs) == 20
    assert len(acca_20.leagues_covered) >= 5 # Spans 5+ leagues
    assert acca_20.cut_1_warning is not None
    assert "Cut-2" in acca_20.cut_1_warning or "Cut-1" in acca_20.cut_1_warning

    # Test 25-game accumulator
    acca_25 = AccasOptimizer.build_smart_accumulator(
        fixtures=fixtures,
        bankroll_ngn=10000.0,
        target_legs=25,
        strategy="safest_winners"
    )
    assert len(acca_25.legs) >= 20
    assert acca_25.recommended_stake_ngn <= 500.0 # Stake is safely capped for long tickets
