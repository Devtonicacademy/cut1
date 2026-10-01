import datetime as dt

import pytest

from apps.api.app.data import api_football, db
from apps.api.app.data import national
from apps.api.app.services.fixture_service import NATIONAL_SOURCE, FixtureService
from apps.api.app.tracking import ledger

CSV = """date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
2026-03-20,France,Italy,2,0,UEFA Nations League,Paris,France,FALSE
2026-03-21,Spain,Wales,NA,NA,Friendly,Madrid,Spain,FALSE
2026-06-10,Brazil,Chile,1,1,FIFA World Cup qualification,Rio,Brazil,TRUE
"""


def test_parse_results_skips_unplayed_games_and_reads_neutral():
    rows = national.parse_results_csv(CSV)
    assert [(r["home_team"], r["fthg"], r["ftag"], r["neutral"]) for r in rows] == [("France", 2, 0, 0), ("Brazil", 1, 1, 1)]


def test_elo_replay_rewards_winners_and_is_zero_sum():
    ratings = national.replay([
        {"match_date": "2026-01-01", "home_team": "A", "away_team": "B", "fthg": 3, "ftag": 0, "tournament": "FIFA World Cup", "neutral": 0},
    ])
    assert ratings.rating("A") > national.ELO_START > ratings.rating("B")
    assert ratings.rating("A") + ratings.rating("B") == pytest.approx(2 * national.ELO_START)
    assert ratings.games == {"A": 1, "B": 1}


def test_friendlies_move_ratings_less_than_qualifiers():
    def gain(tournament):
        r = national.replay([{"match_date": "2026-01-01", "home_team": "A", "away_team": "B", "fthg": 1, "ftag": 0,
                              "tournament": tournament, "neutral": 1}])
        return r.rating("A") - national.ELO_START
    assert gain("Friendly") < gain("FIFA World Cup qualification") < gain("FIFA World Cup")


def test_neutral_venue_removes_home_advantage():
    r = national.NationalRatings()
    assert r.gap("A", "B", neutral=False) == national.ELO_HOME_ADVANTAGE
    assert r.gap("A", "B", neutral=True) == 0.0
    home, draw, away = national.outcome_probs(0.0)
    assert home == pytest.approx(away) and home + draw + away == pytest.approx(1.0)


def _api_match(fid, date, home, away, status="NS"):
    return {"fixture": {"id": fid, "date": date, "status": {"short": status}},
            "teams": {"home": {"id": fid * 10, "name": home}, "away": {"id": fid * 10 + 1, "name": away}}}


def test_api_football_parser_maps_names_and_drops_unplaceable_games():
    payload = {"response": [
        _api_match(1, "2026-10-10T18:45:00+00:00", "Korea Republic", "USA"),
        _api_match(2, "2026-10-11T18:45:00+00:00", "France", "Italy", status="FT"),
        _api_match(3, "2026-10-12T18:45:00+00:00", "France", "Atlantis"),
    ]}
    rows, unmatched = api_football.parse_fixtures(payload, "FRI", ["South Korea", "United States", "France", "Italy"])
    assert [(r["div"], r["home_team"], r["away_team"], r["match_date"]) for r in rows] == [
        ("FRI", "South Korea", "United States", "2026-10-10")]
    assert unmatched == ["Atlantis"]


def test_api_football_fixtures_survive_a_snapshot_round_trip(tmp_path):
    rows, _ = api_football.parse_fixtures(
        {"response": [_api_match(1, "2026-10-10T18:45:00+00:00", "France", "Italy")]}, "UNL", ["France", "Italy"])
    with db.connect(tmp_path / "f.db") as conn:
        assert db.replace_fixtures(conn, rows, source=api_football.SOURCE) == 1


async def test_national_fixture_is_served_from_elo_and_stays_out_of_the_ledger(tmp_path):
    fixtures = await FixtureService().get_all_fixtures_with_predictions()
    fri = [f for f in fixtures if f.div == "FRI"]
    assert len(fri) == 1
    f, p = fri[0], fri[0].prediction
    assert f.league == "International Friendly" and p.prediction_source == NATIONAL_SOURCE
    assert p.prob_home_win > 0.7 > p.prob_away_win  # Strongland has beaten Weakland 30 times
    assert p.prob_home_win + p.prob_draw + p.prob_away_win == pytest.approx(1.0, abs=1e-3)
    assert f.h2h.total_meetings == 30 and "meetings" in f.h2h.summary

    with db.connect(tmp_path / "ledger.db") as conn:
        ledger.lock_predictions(conn, fixtures, dt.datetime.now(dt.timezone.utc))
        assert conn.execute("SELECT COUNT(*) FROM predictions WHERE div = 'FRI'").fetchone()[0] == 0
