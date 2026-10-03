import sqlite3

from apps.api.app.data import db
from apps.api.app.data import football_data_org as fdorg

OUR_NAMES = ["Man City", "Man United", "Nott'm Forest", "Brighton", "Leeds", "Newcastle", "Inter", "Milan", "Ath Madrid"]


def _team(team_id, name, short):
    return {"id": team_id, "name": name, "shortName": short}


def test_team_matching_uses_short_names_containment_and_overrides():
    teams = [
        _team(1, "Manchester City FC", "Man City"),
        _team(2, "Manchester United FC", "Man United"),
        _team(3, "Nottingham Forest FC", "Nottingham"),
        _team(4, "Brighton & Hove Albion FC", "Brighton Hove"),
        _team(5, "Leeds United FC", "Leeds United"),
        _team(6, "FC Internazionale Milano", "Inter"),
        _team(7, "AC Milan", "Milan"),
        _team(8, "Club Atlético de Madrid", "Atleti"),
        _team(9, "Unknown Town FC", "Unknown"),
    ]
    mapping, unmatched = fdorg.match_teams(teams, OUR_NAMES)
    assert mapping == {1: "Man City", 2: "Man United", 3: "Nott'm Forest", 4: "Brighton", 5: "Leeds",
                       6: "Inter", 7: "Milan", 8: "Ath Madrid"}
    assert unmatched == ["Unknown Town FC"]


def test_normalise_strips_accents_and_club_suffixes():
    assert fdorg.normalise("Deportivo Alavés") == "deportivo alaves"
    assert fdorg.normalise("1. FC Heidenheim 1846") == "heidenheim"


def test_parse_matches_keeps_scheduled_mapped_games_with_uk_dates():
    payload = {"matches": [
        {"status": "TIMED", "utcDate": "2026-10-10T23:30:00Z",
         "homeTeam": _team(1, "Manchester City FC", "Man City"), "awayTeam": _team(5, "Leeds United FC", "Leeds United")},
        {"status": "FINISHED", "utcDate": "2026-09-01T14:00:00Z",
         "homeTeam": _team(2, "Manchester United FC", "Man United"), "awayTeam": _team(4, "Brighton & Hove Albion FC", "Brighton Hove")},
        {"status": "SCHEDULED", "utcDate": "2026-10-11T14:00:00Z",
         "homeTeam": _team(9, "Unknown Town FC", "Unknown"), "awayTeam": _team(5, "Leeds United FC", "Leeds United")},
    ]}
    rows, unmatched = fdorg.parse_matches(payload, "E0", OUR_NAMES)
    assert rows == [{
        "div": "E0", "match_date": "2026-10-11",  # 23:30 UTC is 00:30 the next day in the UK (BST)
        "kickoff_utc": "2026-10-10T23:30:00+00:00", "home_team": "Man City", "away_team": "Leeds",
        "source": "football-data.org",
    }]
    assert unmatched == ["Unknown Town FC"]


def _fixture(home, away, date="2026-10-10"):
    return {"div": "E0", "match_date": date, "kickoff_utc": f"{date}T14:00:00+00:00", "home_team": home, "away_team": away}


def test_primary_source_wins_and_secondary_only_fills_gaps(tmp_path):
    with db.connect(tmp_path / "f.db") as conn:
        db.replace_fixtures(conn, [_fixture("A", "B"), _fixture("C", "D")], source=fdorg.SOURCE)
        db.replace_fixtures(conn, [{**_fixture("A", "B", "2026-10-11"), "avg_h": 2.0, "avg_d": 3.3, "avg_a": 3.5}])
        rows = {(r["home_team"], r["source"]) for r in conn.execute("SELECT * FROM fixtures")}
        assert rows == {("A", "football-data.co.uk"), ("C", "football-data.org")}

        # A later football-data.org refresh does not re-add a match the primary source already lists
        assert db.replace_fixtures(conn, [_fixture("A", "B"), _fixture("C", "D"), _fixture("E", "F")],
                                   source=fdorg.SOURCE) == 2
        assert conn.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0] == 3


def test_old_databases_gain_the_source_column(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE fixtures (div TEXT, match_date TEXT, kickoff_utc TEXT, home_team TEXT, away_team TEXT)")
    old.execute("INSERT INTO fixtures VALUES ('E0', '2026-10-10', '2026-10-10T14:00:00+00:00', 'A', 'B')")
    old.commit()
    old.close()
    with db.connect(path) as conn:
        assert conn.execute("SELECT source FROM fixtures").fetchone()[0] == "football-data.co.uk"


def test_extract_crests_maps_clubs_to_our_names_and_adds_the_emblem():
    payload = {
        "competition": {"emblem": "https://crests.example/PL.png"},
        "matches": [
            {"status": "TIMED", "utcDate": "2026-10-10T14:00:00Z",
             "homeTeam": {**_team(1, "Manchester City FC", "Man City"), "crest": "https://crests.example/65.png"},
             "awayTeam": {**_team(5, "Leeds United FC", "Leeds United"), "crest": None}},
            {"status": "SCHEDULED", "utcDate": "2026-10-11T14:00:00Z",
             "homeTeam": {**_team(9, "Unknown Town FC", "Unknown"), "crest": "https://crests.example/9.png"},
             "awayTeam": {**_team(5, "Leeds United FC", "Leeds United"), "crest": None}},
        ],
    }
    assert fdorg.extract_crests(payload, "E0", OUR_NAMES) == [
        {"kind": "team", "key": "Man City", "url": "https://crests.example/65.png"},  # no crest for Leeds, none for the unplaceable club
        {"kind": "league", "key": "E0", "url": "https://crests.example/PL.png"},
    ]


def test_crests_round_trip_and_newer_urls_replace_older(tmp_path):
    with db.connect(tmp_path / "c.db") as conn:
        assert db.upsert_crests(conn, [
            {"kind": "team", "key": "Man City", "url": "old"},
            {"kind": "league", "key": "E0", "url": "https://crests.example/PL.png"},
            {"kind": "team", "key": "Leeds", "url": None},  # no URL: skipped
        ]) == 2
        db.upsert_crests(conn, [{"kind": "team", "key": "Man City", "url": "new"}])
        assert db.load_crests(conn) == {"team": {"Man City": "new"}, "league": {"E0": "https://crests.example/PL.png"}}
