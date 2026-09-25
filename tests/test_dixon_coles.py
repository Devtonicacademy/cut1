import pytest
from apps.api.app.services.dixon_coles import DixonColesEngine

def test_dixon_coles_probability_summation():
    """Verify that match outcome probabilities strictly sum to 1.0."""
    engine = DixonColesEngine()
    result = engine.calculate_match_probabilities(
        home_attack=1.4,
        away_defense=0.9,
        away_attack=1.1,
        home_defense=0.8,
        league_home_advantage=1.25
    )

    total_prob = result["prob_home_win"] + result["prob_draw"] + result["prob_away_win"]
    assert pytest.approx(total_prob, abs=1e-3) == 1.0
    assert result["expected_goals_home"] > 0
    assert result["expected_goals_away"] > 0
    assert 0.0 < result["prob_home_win"] < 1.0
    assert 0.0 < result["prob_draw"] < 1.0
    assert 0.0 < result["prob_away_win"] < 1.0

def test_home_advantage_impact():
    """Verify that higher home advantage increases home expected goals and win probability."""
    engine = DixonColesEngine()
    neutral = engine.calculate_match_probabilities(
        home_attack=1.2, away_defense=1.0, away_attack=1.2, home_defense=1.0, league_home_advantage=1.0
    )
    boosted = engine.calculate_match_probabilities(
        home_attack=1.2, away_defense=1.0, away_attack=1.2, home_defense=1.0, league_home_advantage=1.40
    )
    assert boosted["expected_goals_home"] > neutral["expected_goals_home"]
    assert boosted["prob_home_win"] > neutral["prob_home_win"]

def test_goal_market_probabilities():
    """Verify over/under goal probabilities are mathematically sound."""
    engine = DixonColesEngine()
    result = engine.calculate_match_probabilities(
        home_attack=1.5, away_defense=1.2, away_attack=1.3, home_defense=1.1
    )
    assert 0.0 < result["prob_over_1_5"] < 1.0
    assert 0.0 < result["prob_over_2_5"] < 1.0
    assert pytest.approx(result["prob_over_2_5"] + result["prob_under_2_5"], abs=1e-2) == 1.0
