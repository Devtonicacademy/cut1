import datetime as dt

from apps.api.app.data import football_data_uk as fduk
from apps.api.app.data.ratings import build_league_model, recent_form
from apps.api.app.models.schemas import BookmakerOdds
from apps.api.app.services.ev_engine import EvEngine
from apps.api.app.services.fixture_service import FixtureService, describe_kickoff

RESULTS_CSV = (
    "﻿Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,HST,AST,AvgH,AvgD,AvgA,Avg>2.5,Avg<2.5,PSCH,PSCD,PSCA\n"
    "E0,15/08/2025,20:00,Liverpool,Bournemouth,4,2,10,3,1.31,5.96,8.31,1.36,3.2,1.29,6.55,9.75\n"
    "E0,16/08/25,15:00,Arsenal,Chelsea,,,,,1.9,3.6,4.1,,,,,\n"
    "XX,16/08/2025,15:00,Foo,Bar,1,0,,,,,,,,,,\n"
)


def test_parse_results_csv_handles_bom_short_dates_and_incomplete_rows():
    rows = fduk.parse_results_csv(RESULTS_CSV, "2526")
    assert len(rows) == 1  # unplayed row and unknown division are skipped
    r = rows[0]
    assert (r["div"], r["home_team"], r["away_team"], r["fthg"], r["ftag"]) == ("E0", "Liverpool", "Bournemouth", 4, 2)
    assert r["match_date"] == "2025-08-15"
    assert r["hst"] == 10 and r["avg_h"] == 1.31 and r["avg_o25"] == 1.36 and r["psc_h"] == 1.29
    assert r["max_h"] is None


def test_uk_kickoff_converts_to_utc_in_summer_and_winter():
    summer = fduk.uk_kickoff_to_utc(dt.date(2026, 9, 26), "15:00")
    winter = fduk.uk_kickoff_to_utc(dt.date(2026, 12, 26), "15:00")
    assert summer.hour == 14  # BST = UTC+1
    assert winter.hour == 15  # GMT = UTC
    assert fduk.uk_kickoff_to_utc(dt.date(2026, 9, 26), "") is None


def test_season_codes():
    assert fduk.season_code(2026) == "2627"
    assert fduk.season_code(2099) == "9900"
    assert fduk.current_season_start(dt.date(2026, 9, 26)) == 2026
    assert fduk.current_season_start(dt.date(2027, 3, 1)) == 2026


def _match(date, home, away, hg, ag):
    return {"div": "E0", "match_date": date, "home_team": home, "away_team": away,
            "fthg": hg, "ftag": ag, "hst": hg * 3, "ast": ag * 3}


def test_ratings_reward_the_stronger_team_and_track_form():
    goals_scored = {"Strong": 3, "Mid": 1, "Other": 1, "Weak": 0}
    rounds = [(("Strong", "Weak"), ("Mid", "Other")),
              (("Mid", "Strong"), ("Weak", "Other")),
              (("Strong", "Other"), ("Mid", "Weak"))]
    matches = []
    start = dt.date(2026, 1, 1)
    for week in range(21):
        d = (start + dt.timedelta(days=7 * week)).isoformat()
        for home, away in rounds[week % 3]:
            matches.append(_match(d, home, away, goals_scored[home], goals_scored[away]))
    as_of = dt.date(2026, 6, 1)
    model = build_league_model("E0", matches, as_of, season_start=dt.date(2025, 7, 1))

    assert model.rating("Strong").attack > 1.3 > model.rating("Weak").attack
    assert model.rating("Strong").defence < model.rating("Weak").defence
    assert model.rating("Unknown FC").weighted_matches == 0.0
    home_xg, away_xg = model.expected_goals("Strong", "Weak")
    assert home_xg > 2 * away_xg

    form = recent_form(matches, "Weak", as_of)
    assert form["form"] == "LLLLL"
    assert form["shots_xg_for"] == 0.0 and form["shots_xg_against"] > 1.0


def test_ev_engine_skips_markets_without_real_odds():
    avg = BookmakerOdds(bookmaker="Market Average", home_win=2.0, draw=3.4, away_win=3.8)
    best = BookmakerOdds(bookmaker="Best Price", home_win=2.1, draw=3.5, away_win=4.0)
    probs = {"prob_home_win": 0.60, "prob_draw": 0.22, "prob_away_win": 0.18,
             "prob_over_1_5": 0.95, "prob_over_2_5": 0.9, "prob_under_2_5": 0.1, "prob_btts": 0.9}
    bets = EvEngine.evaluate_match_markets("A", "B", probs, avg, best)
    assert [b.market.value for b in bets] == ["1"]  # goal markets have no quoted price
    assert bets[0].bookmaker == "Best Price" and bets[0].market_odds == 2.1


def test_describe_kickoff_uses_west_africa_time():
    now = dt.datetime(2026, 9, 26, 10, 0, tzinfo=dt.timezone.utc)
    info = describe_kickoff(dt.datetime(2026, 9, 26, 14, 0, tzinfo=dt.timezone.utc), now)
    assert info["kickoff"] == "Today, 15:00"
    assert info["is_upcoming"] and info["match_status"] == "UPCOMING"
    assert describe_kickoff(dt.datetime(2026, 9, 27, 14, 0, tzinfo=dt.timezone.utc), now)["kickoff"].startswith("Tomorrow")
    assert describe_kickoff(dt.datetime(2026, 9, 26, 9, 0, tzinfo=dt.timezone.utc), now)["is_upcoming"] is False


def test_head_to_head_counts_from_upcoming_home_teams_perspective():
    rows = [
        {"div": "E0", "match_date": "2026-03-01", "home_team": "B", "away_team": "A", "fthg": 0, "ftag": 2},
        {"div": "E0", "match_date": "2025-10-01", "home_team": "A", "away_team": "B", "fthg": 1, "ftag": 1},
        {"div": "E0", "match_date": "2025-03-01", "home_team": "A", "away_team": "B", "fthg": 0, "ftag": 1},
    ]
    h2h = FixtureService._h2h("A", "B", rows)
    assert (h2h.total_meetings, h2h.home_team_wins, h2h.draws, h2h.away_team_wins) == (3, 1, 1, 1)
    assert (h2h.home_goals_total, h2h.away_goals_total) == (3, 2)
    assert h2h.last_matches[0].winner == "away" and h2h.summary.startswith("Since 2025")
    assert FixtureService._h2h("A", "C", []).total_meetings == 0
