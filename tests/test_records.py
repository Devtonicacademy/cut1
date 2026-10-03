import datetime as dt

import httpx
import pytest
from starlette.testclient import TestClient

from apps.api.app.data import db, ingest
from apps.api.app.data import football_data_org as fdorg
from apps.api.app.main import app
from apps.api.app.tracking import matches

NOW = dt.datetime(2026, 10, 3, 16, 0, tzinfo=dt.timezone.utc)


def _row(conn, n, minutes_ago, *, score=None, graded=False, div="E0", home=None, away=None, pick="1", probs=(0.55, 0.25, 0.20)):
    kickoff = NOW - dt.timedelta(minutes=minutes_ago)
    hg, ag = score if score else (None, None)
    correct = None if hg is None else int(("1" if hg > ag else "X" if hg == ag else "2") == pick)
    conn.execute(
        """INSERT INTO predictions (fixture_id, div, match_date, kickoff_utc, home_team, away_team, created_at, model,
           p_home, p_draw, p_away, pick, pick_prob, prev_hash, hash, fthg, ftag, correct, graded_at)
           VALUES (?, ?, ?, ?, ?, ?, 'x', 'm', ?, ?, ?, ?, ?, 'p', 'h', ?, ?, ?, ?)""",
        (f"f{n}", div, kickoff.date().isoformat(), kickoff.isoformat(), home or f"Home{n}", away or f"Away{n}",
         *probs, pick, max(probs), hg, ag, correct, "x" if graded else None))


def _live(conn, n, status, goals, updated_minutes_ago=1, minute=None):
    db.upsert_live_scores(conn, [{
        "fixture_id": f"f{n}", "status": status, "home_goals": goals[0] if goals else None,
        "away_goals": goals[1] if goals else None, "minute": minute,
        "updated_at": (NOW - dt.timedelta(minutes=updated_minutes_ago)).isoformat()}])


def test_matches_are_split_into_ongoing_and_past(tmp_path):
    with db.connect(tmp_path / "m.db") as conn:
        _row(conn, 1, 400, score=(2, 1), graded=True)                 # played, graded, prediction right
        _row(conn, 2, 300, score=(0, 1), graded=True)                 # played, graded, prediction wrong
        _row(conn, 3, 600, graded=True)                               # void: left out
        _row(conn, 4, 60)                                             # in play, no live feed
        _row(conn, 5, 30)                                             # in play, fresh live score
        _row(conn, 6, 45)                                             # in play, live score gone stale
        _row(conn, 7, 240)                                            # played long ago, not graded yet
        _row(conn, 8, -90)                                            # not started: belongs in the fixtures list
        _row(conn, 9, 100)                                            # feed says full time, not graded yet
        _live(conn, 5, "IN_PLAY", (1, 0), updated_minutes_ago=1, minute=31)
        _live(conn, 6, "IN_PLAY", (2, 2), updated_minutes_ago=25)
        _live(conn, 9, "FINISHED", (3, 1), updated_minutes_ago=3)
        result = matches.build(conn, NOW)

    assert [m.id for m in result.ongoing] == ["f4", "f6", "f5"]  # earliest kickoff first
    by_id = {m.id: m for m in result.ongoing}
    assert by_id["f4"].minutes_since_kickoff == 60 and by_id["f4"].live_status is None and by_id["f4"].home_goals is None
    assert (by_id["f5"].live_status, by_id["f5"].home_goals, by_id["f5"].away_goals, by_id["f5"].minute) == ("IN_PLAY", 1, 0, 31)
    assert by_id["f6"].home_goals is None and by_id["f6"].live_status is None  # a 25-minute-old score is not shown

    past = {m.id: m for m in result.past}
    assert set(past) == {"f1", "f2", "f7", "f9"}                  # not f3 (void), not f8 (upcoming), nothing ongoing
    assert [m.id for m in result.past] == ["f9", "f7", "f2", "f1"]  # newest first
    assert (past["f1"].status, past["f1"].actual, past["f1"].correct, past["f1"].provisional) == ("graded", "1", True, False)
    assert (past["f2"].actual, past["f2"].correct) == ("2", False)
    assert (past["f7"].status, past["f7"].home_goals, past["f7"].provisional) == ("awaiting", None, False)
    assert (past["f9"].status, past["f9"].home_goals, past["f9"].away_goals, past["f9"].provisional, past["f9"].correct) == ("awaiting", 3, 1, True, None)
    assert (result.summary.graded, result.summary.correct, result.summary.accuracy_pct) == (2, 1, 50.0)
    # the locked prediction is what is shown
    assert (past["f1"].p_home, past["f1"].pick, past["f1"].league) == (0.55, "1", "English Premier League")


def test_a_graded_result_beats_the_live_feed_and_crests_are_attached(tmp_path):
    with db.connect(tmp_path / "g.db") as conn:
        _row(conn, 1, 150, score=(0, 0), graded=True, home="Man City", away="Leeds", pick="1")
        _live(conn, 1, "FINISHED", (4, 4))                            # stale feed disagrees; the official result wins
        db.upsert_crests(conn, [{"kind": "team", "key": "Man City", "url": "https://c.example/65.png"},
                                {"kind": "league", "key": "E0", "url": "https://c.example/PL.png"}])
        past = matches.build(conn, NOW).past[0]
    assert (past.home_goals, past.away_goals, past.actual, past.correct, past.provisional) == (0, 0, "X", False, False)
    assert (past.home_crest, past.away_crest, past.league_crest) == ("https://c.example/65.png", None, "https://c.example/PL.png")


def test_past_list_is_limited_but_the_summary_counts_everything(tmp_path):
    with db.connect(tmp_path / "l.db") as conn:
        for n in range(1, 6):
            _row(conn, n, 200 + n * 10, score=(1, 0), graded=True)
        result = matches.build(conn, NOW, past_limit=2)
    assert len(result.past) == 2 and result.summary.graded == 5 and result.summary.accuracy_pct == 100.0


SHORT = {"Manchester City FC": "Man City", "Leeds United FC": "Leeds United", "Manchester United FC": "Man United",
         "Newcastle United FC": "Newcastle", "Brighton & Hove Albion FC": "Brighton Hove", "Unknown Town FC": "Unknown"}


def _fd_team(team_id, name):
    return {"id": team_id, "name": name, "shortName": SHORT.get(name, name)}


def test_parse_live_scores_maps_names_and_keeps_only_matches_under_way_or_finished():
    payload = {"matches": [
        {"status": "IN_PLAY", "utcDate": "2026-10-03T15:00:00Z", "minute": 63,
         "homeTeam": _fd_team(1, "Manchester City FC"), "awayTeam": _fd_team(5, "Leeds United FC"),
         "score": {"fullTime": {"home": 2, "away": 1}, "halfTime": {"home": 1, "away": 0}}},
        {"status": "PAUSED", "utcDate": "2026-10-03T15:00:00Z",
         "homeTeam": _fd_team(2, "Manchester United FC"), "awayTeam": _fd_team(3, "Newcastle United FC"),
         "score": {"fullTime": {"home": None, "away": None}, "halfTime": {"home": 0, "away": 0}}},
        {"status": "FINISHED", "utcDate": "2026-10-03T12:30:00Z", "minute": "90",
         "homeTeam": _fd_team(4, "Brighton & Hove Albion FC"), "awayTeam": _fd_team(1, "Manchester City FC"),
         "score": {"fullTime": {"home": 1, "away": 3}}},
        {"status": "TIMED", "utcDate": "2026-10-03T19:00:00Z",
         "homeTeam": _fd_team(5, "Leeds United FC"), "awayTeam": _fd_team(2, "Manchester United FC"), "score": {}},
        {"status": "IN_PLAY", "utcDate": "2026-10-03T15:00:00Z",
         "homeTeam": _fd_team(9, "Unknown Town FC"), "awayTeam": _fd_team(5, "Leeds United FC"), "score": {}},
    ]}
    rows = fdorg.parse_live_scores(payload, ["Man City", "Man United", "Newcastle", "Brighton", "Leeds"])
    assert [(r["home_team"], r["away_team"], r["status"], r["home_goals"], r["away_goals"], r["minute"]) for r in rows] == [
        ("Man City", "Leeds", "IN_PLAY", 2, 1, 63),
        ("Man United", "Newcastle", "PAUSED", 0, 0, None),      # half-time score stands in until full time has one
        ("Brighton", "Man City", "FINISHED", 1, 3, 90),
    ]
    assert rows[0]["kickoff_utc"] == "2026-10-03T15:00:00+00:00"


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("rate limited", request=httpx.Request("GET", "x"), response=httpx.Response(self.status_code))

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, responses, calls):
        self._responses, self._calls = responses, calls

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, headers=None):
        self._calls.append((url, headers))
        code = url.split("/competitions/")[1].split("/")[0]
        return self._responses[code]


@pytest.fixture
def live_env(tmp_path, monkeypatch):
    monkeypatch.setenv("LIVELYBORG_DB_PATH", str(tmp_path / "live.db"))
    monkeypatch.delenv("LIVELYBORG_OFFLINE", raising=False)
    monkeypatch.setenv("FOOTBALL_DATA_KEY", "secret")
    monkeypatch.setattr(ingest, "FD_ORG_PAUSE_SECONDS", 0)
    calls = []

    def use(responses):
        monkeypatch.setattr(ingest, "_client", lambda: _FakeClient(responses, calls))
        return calls
    return use


def test_live_polling_asks_only_for_competitions_with_a_match_in_play(live_env):
    with db.connect() as conn:
        _row(conn, 1, 50, home="Man City", away="Leeds", div="E0")     # Premier League, in play
        _row(conn, 2, 40, home="Barcelona", away="Sevilla", div="SP1") # La Liga, in play
        _row(conn, 3, 400, div="I1")                                   # Serie A, long over: not asked about
        _row(conn, 4, 20, div="D1", score=(1, 0), graded=True)         # Bundesliga, already graded: not asked about
    pl = {"matches": [{"status": "IN_PLAY", "utcDate": (NOW - dt.timedelta(minutes=50)).isoformat().replace("+00:00", "Z"), "minute": 50,
                       "homeTeam": _fd_team(1, "Manchester City FC"), "awayTeam": _fd_team(5, "Leeds United FC"),
                       "score": {"fullTime": {"home": 1, "away": 0}}}]}
    calls = live_env({"PL": _FakeResponse(pl), "PD": _FakeResponse({}, status=429)})   # La Liga is rate limited
    result = ingest.ingest_live_scores(NOW)

    assert sorted(u.split("/competitions/")[1].split("/")[0] for u, _ in calls) == ["PD", "PL"]
    assert all(h == {"X-Auth-Token": "secret"} for _, h in calls)
    assert result["polled"] == 2 and result["updated"] == 1 and len(result["errors"]) == 1 and result["errors"][0].startswith("PD")
    with db.connect() as conn:
        stored = db.load_live_scores(conn)
    assert list(stored) == ["f1"] and (stored["f1"]["home_goals"], stored["f1"]["minute"], stored["f1"]["status"]) == (1, 50, "IN_PLAY")


def test_live_polling_costs_nothing_when_nothing_is_on_or_it_is_not_configured(live_env, monkeypatch):
    calls = live_env({})
    with db.connect() as conn:
        _row(conn, 1, 400)                                              # over long ago
    assert ingest.ingest_live_scores(NOW) == {"polled": 0} and calls == []

    with db.connect() as conn:
        _row(conn, 2, 30)
    monkeypatch.delenv("FOOTBALL_DATA_KEY")
    assert "skipped" in ingest.ingest_live_scores(NOW) and calls == []
    monkeypatch.setenv("FOOTBALL_DATA_KEY", "k")
    monkeypatch.setenv("LIVELYBORG_OFFLINE", "1")
    assert ingest.ingest_live_scores(NOW) == {"skipped": "offline mode"} and calls == []


def test_the_matches_endpoint_is_public_and_shaped_as_documented():
    res = TestClient(app).get("/api/v1/track-record/matches?limit=5")   # no sign-in needed, like the ledger itself
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"generated_at", "summary", "ongoing", "past"}
    assert set(body["summary"]) == {"graded", "correct", "accuracy_pct"}
    assert len(body["past"]) <= 5
    assert TestClient(app).get("/api/v1/track-record/matches?limit=0").status_code == 422
