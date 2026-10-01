import datetime as dt

import pytest

from apps.api.app.data import db
from apps.api.app.data import football_data_org as fdorg
from apps.api.app.data.leagues import strength_offset
from apps.api.app.ml.features import FeatureState, elo_outcome_probs
from apps.api.app.services.fixture_service import CROSS_LEAGUE_SOURCE, FixtureService
from apps.api.app.tracking import ledger


def _team(team_id, name, short):
    return {"id": team_id, "name": name, "shortName": short}


def test_strength_offset_ranks_countries_and_tiers():
    assert strength_offset("England", 1) > strength_offset("Portugal", 1) > strength_offset("Greece", 1)
    assert strength_offset("England", 2) < strength_offset("England", 1)
    assert strength_offset("Austria", 1) < strength_offset("Greece", 1)  # country we hold no data for


def test_elo_outcome_probs_sum_to_one_and_follow_the_gap():
    even = elo_outcome_probs(0.0)
    assert sum(even) == pytest.approx(1.0)
    assert even[0] == pytest.approx(even[2])
    big = elo_outcome_probs(300.0)
    assert sum(big) == pytest.approx(1.0)
    assert big[0] > even[0] > big[2]
    assert big[1] < even[1]  # mismatches end level less often


def test_cross_league_features_apply_the_league_offset():
    state = FeatureState()
    day = dt.date(2026, 10, 1)
    f = state.cross_league_features("E0", "P1", "A", "B", day)  # both clubs start at the same domestic Elo
    assert f["elo_diff"] == pytest.approx(strength_offset("England", 1) - strength_offset("Portugal", 1))
    assert f["elo_diff"] > 0
    assert "dc_p_home" not in f and "home_table_pct" not in f


def test_parse_cross_country_matches_tags_divisions_and_drops_unknown_clubs():
    team_divs = {"Real Madrid": "SP1", "Man City": "E0", "Benfica": "P1"}
    payload = {"matches": [
        {"status": "TIMED", "utcDate": "2026-10-21T19:00:00Z",
         "homeTeam": _team(1, "Real Madrid CF", "Real Madrid"), "awayTeam": _team(2, "Manchester City FC", "Man City")},
        {"status": "TIMED", "utcDate": "2026-10-22T19:00:00Z",
         "homeTeam": _team(3, "SL Benfica", "Benfica"), "awayTeam": _team(4, "FC Salzburg", "Salzburg")},
    ]}
    rows, unmatched = fdorg.parse_cross_country_matches(payload, "CL", team_divs)
    assert [(r["div"], r["home_team"], r["away_team"], r["home_div"], r["away_div"]) for r in rows] == [
        ("CL", "Real Madrid", "Man City", "SP1", "E0")
    ]
    assert unmatched == ["FC Salzburg"]


def test_fixture_columns_round_trip_home_and_away_divisions(tmp_path):
    row = {"div": "CL", "match_date": "2026-10-21", "kickoff_utc": "2026-10-21T19:00:00+00:00",
           "home_team": "A", "away_team": "B", "home_div": "SP1", "away_div": "E0"}
    with db.connect(tmp_path / "f.db") as conn:
        db.replace_fixtures(conn, [row], source=fdorg.SOURCE)
        stored = dict(conn.execute("SELECT * FROM fixtures").fetchone())
    assert (stored["home_div"], stored["away_div"]) == ("SP1", "E0")


async def test_cross_league_fixture_is_served_with_lower_confidence_and_stays_out_of_the_ledger(tmp_path):
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions()
    cl = [f for f in fixtures if f.div == "CL"]
    assert len(cl) == 1
    p = cl[0].prediction
    assert cl[0].league == "UEFA Champions League"
    assert p.prediction_source == CROSS_LEAGUE_SOURCE
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-3)
    assert p.value_bets == []
    assert "different leagues" in p.key_factors[0]

    with db.connect(tmp_path / "ledger.db") as conn:  # own database: locking must not touch the shared test ledger
        locked = ledger.lock_predictions(conn, fixtures, dt.datetime.now(dt.timezone.utc))
        cl_rows = conn.execute("SELECT COUNT(*) FROM predictions WHERE div = 'CL'").fetchone()[0]
    assert locked > 0 and cl_rows == 0
