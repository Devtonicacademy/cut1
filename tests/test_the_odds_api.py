import datetime as dt

from apps.api.app.data import db
from apps.api.app.data import the_odds_api as odds


def _event(home, away, kickoff, prices):
    books = [{"key": f"b{i}", "markets": [{"key": "h2h", "outcomes": [
        {"name": home, "price": h}, {"name": "Draw", "price": d}, {"name": away, "price": a}]}]}
        for i, (h, d, a) in enumerate(prices)]
    return {"home_team": home, "away_team": away, "commence_time": kickoff, "bookmakers": books}


def _fixture(home, away, kickoff):
    return {"div": "E0", "home_team": home, "away_team": away, "kickoff_utc": kickoff, "avg_h": None}


KICKOFF = "2026-10-03T14:00:00+00:00"
PRICES = [(1.5, 4.0, 6.0), (1.6, 4.2, 5.8), (1.55, 3.8, 6.2)]


def test_average_needs_enough_bookmakers():
    ev = _event("Arsenal", "Chelsea", "2026-10-03T14:00:00Z", PRICES)
    got = odds.average_h2h(ev)
    assert got["bookmakers"] == 3 and got["avg_h"] == 1.55 and got["max_a"] == 6.2
    ev["bookmakers"] = ev["bookmakers"][:2]
    assert odds.average_h2h(ev) == {}


def test_events_are_matched_to_our_team_names_and_kickoff():
    fixtures = [_fixture("Man City", "Wolves", KICKOFF), _fixture("Arsenal", "Chelsea", KICKOFF)]
    events = [_event("Manchester City", "Wolverhampton Wanderers", "2026-10-03T14:00:00Z", PRICES),
              _event("Arsenal", "Chelsea", "2026-10-09T14:00:00Z", PRICES)]  # a different game by date
    rows, _ = odds.parse_events(events, "E0", fixtures)
    assert [(r["home_team"], r["away_team"]) for r in rows] == [("Man City", "Wolves")]


def test_overlay_fills_only_fixtures_without_their_own_odds():
    with db.connect() as conn:
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).isoformat()
        base = ("E0", future[:10], future, "Overlay FC", "Other FC")
        conn.execute("INSERT INTO fixtures (div, match_date, kickoff_utc, home_team, away_team) VALUES (?,?,?,?,?)", base)
        conn.execute("INSERT INTO fixtures (div, match_date, kickoff_utc, home_team, away_team, avg_h, avg_d, avg_a)"
                     " VALUES ('E0', ?, ?, 'Priced FC', 'Own FC', 2.0, 3.0, 4.0)", (future[:10], future))
        rows = [{"div": "E0", "home_team": t, "away_team": a, "kickoff_utc": future, "avg_h": 9.0, "avg_d": 9.0,
                 "avg_a": 9.0, "max_h": 9.5, "max_d": 9.5, "max_a": 9.5, "bookmakers": 3}
                for t, a in (("Overlay FC", "Other FC"), ("Priced FC", "Own FC"))]
        db.replace_odds_overlay(conn, rows, ["E0"], dt.datetime.now(dt.timezone.utc).isoformat())
        loaded = {r["home_team"]: r for r in db.load_fixtures_after(conn, "2000-01-01")}
        assert loaded["Overlay FC"]["avg_h"] == 9.0 and loaded["Priced FC"]["avg_h"] == 2.0
        conn.execute("DELETE FROM fixtures WHERE home_team IN ('Overlay FC', 'Priced FC')")
        conn.execute("DELETE FROM odds_overlay")
