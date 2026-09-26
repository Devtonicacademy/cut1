import numpy as np
from starlette.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.ml.features import build_training_rows
from apps.api.app.ml.predictor import key_factors
from apps.api.app.ml.train import choose_value_policy, market_probs, metrics, value_bet_results

client = TestClient(app)


def _m(date, home, away, hg, ag, season="2526"):
    return {"div": "E0", "season": season, "match_date": date, "home_team": home, "away_team": away,
            "fthg": hg, "ftag": ag, "hst": 5, "ast": 3}


def test_training_rows_never_see_their_own_result():
    matches = [
        _m("2025-08-16", "A", "B", 3, 0),
        _m("2025-08-16", "C", "D", 0, 0),  # same day: must not see the A-B result either
        _m("2025-08-23", "A", "B", 2, 1),
    ]
    rows, labels, meta = build_training_rows(matches)
    assert labels == [0, 1, 0]
    first_day = [r for r, m in zip(rows, meta) if m["match_date"] == "2025-08-16"]
    for r in first_day:
        assert r["elo_diff"] == 0 and r["home_experience"] == 0 and r["h2h_n"] == 0
        assert r["home_form_pts"] is None
    later = rows[[m["match_date"] for m in meta].index("2025-08-23")]
    assert later["h2h_n"] == 1 and later["h2h_ppg_home"] == 3.0 and later["elo_diff"] > 0
    assert later["home_season_ppg"] == 3.0 and later["home_table_pct"] == 0.25


def test_metrics_and_market_probabilities():
    y = np.array([0, 1, 2])
    perfect = np.eye(3) * 0.98 + 0.01
    assert metrics(perfect, y)["accuracy"] == 1.0
    probs = market_probs([{"avg_h": 2.0, "avg_d": 4.0, "avg_a": 4.0}, {"avg_h": None, "avg_d": 3.0, "avg_a": 3.0}])
    assert np.allclose(probs[0], [0.5, 0.25, 0.25]) and np.isnan(probs[1]).all()


def test_value_bet_backtest_and_policy():
    meta = [{"avg_h": 2.5, "avg_d": 3.3, "avg_a": 3.0}] * 4
    probs = np.array([[0.5, 0.25, 0.25]] * 4)  # home priced at +25% EV
    wins = value_bet_results(probs, meta, np.array([0, 0, 1, 2]), ("avg_h", "avg_d", "avg_a"))
    assert wins[0]["bets"] == 4 and wins[0]["roi"] == 0.25  # 2 wins x 2.5 = 5 back from 4 staked

    profitable = [{"min_ev": 0.02, "bets": 500, "roi": 0.03}]
    losing = [{"min_ev": 0.02, "bets": 500, "roi": -0.05}]
    assert choose_value_policy(profitable, profitable)["enabled"] is True
    assert choose_value_policy(profitable, losing)["enabled"] is False
    assert choose_value_policy([{"min_ev": 0.02, "bets": 20, "roi": 0.5}], profitable)["enabled"] is False


def test_key_factors_are_readable_and_ranked():
    f = {"elo_diff": 180, "home_form_pts": 2.4, "away_form_pts": 0.8, "home_sot_for": 6.0, "away_sot_for": 3.0,
         "home_rest_days": 3, "away_rest_days": 7, "h2h_n": 0}
    factors = key_factors(f, "Arsenal", "Leeds")
    assert factors[0].startswith("Arsenal are the stronger side")
    assert factors[1].startswith("Arsenal in better recent form (2.4 vs 0.8")
    assert any("Leeds are fresher" in x for x in factors)
    assert key_factors({}, "A", "B") == ["No strong edge in rating, form or schedule; treat this as an open game"]


def test_fixtures_use_trained_model_and_explain_predictions():
    fixtures = client.get("/api/v1/fixtures").json()
    assert fixtures
    for f in fixtures:
        p = f["prediction"]
        # every synthetic fixture has odds, so the market-aware model is used
        assert p["prediction_source"].startswith("Trained logistic model on football data + bookmaker consensus")
        assert p["key_factors"]
        assert abs(p["prob_home_win"] + p["prob_draw"] + p["prob_away_win"] - 1) < 1e-3
        for vb in p["value_bets"]:  # policy in the test model: 1X2 only, vs market average
            assert vb["market"] in ("1", "X", "2") and vb["bookmaker"] == "Market Average"


def test_model_report_endpoint():
    report = client.get("/api/v1/model/report").json()
    assert set(report["variants"]) == {"with_market", "football_only"}
    assert report["value_policy"]["enabled"] is True
