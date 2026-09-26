from starlette.testclient import TestClient
from apps.api.app.main import app

ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}  # matches ADMIN_TOKEN set in conftest.py

client = TestClient(app)

def test_healthcheck():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_get_fixtures_endpoint():
    response = client.get("/api/v1/fixtures?bankroll=25000&upcoming_only=true")
    assert response.status_code == 200
    fixtures = response.json()
    assert len(fixtures) >= 5
    for f in fixtures:
        assert f.get("is_upcoming") is True
        assert f.get("kickoff_timestamp") is not None
        assert f.get("match_status") == "UPCOMING"
    first = fixtures[0]
    assert "prediction" in first
    assert "sportybet_odds" in first
    assert "bet9ja_odds" in first

def test_refresh_fixtures_endpoint():
    response = client.post("/api/v1/fixtures/refresh?bankroll=15000", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    fixtures = response.json()
    assert len(fixtures) >= 5
    for f in fixtures:
        assert f["is_upcoming"] is True

def test_data_status_endpoint():
    response = client.get("/api/v1/data/status")
    assert response.status_code == 200
    status = response.json()
    assert status["historical_matches"] > 1000
    assert status["fixtures_in_snapshot"] == 30

def test_bankroll_allocate_endpoint():
    # Pick a value bet from fixtures
    res = client.get("/api/v1/fixtures")
    val_bets = [vb for f in res.json() for vb in f["prediction"]["value_bets"]]
    assert len(val_bets) >= 2

    payload = {
        "bankroll_ngn": 50000.0,
        "risk_level": "conservative",
        "selected_ev_bets": val_bets[:2]
    }
    response = client.post("/api/v1/bankroll/allocate", json=payload)
    assert response.status_code == 200
    alloc = response.json()
    assert alloc["bankroll_ngn"] == 50000.0
    assert alloc["total_staked_ngn"] > 0
    assert alloc["remaining_bankroll_ngn"] < 50000.0
    assert len(alloc["allocations"]) == 2

def test_smart_accumulator_build_endpoint():
    payload = {
        "target_odds": 2.2,
        "risk_level": "conservative",
        "bankroll_ngn": 10000.0,
        "max_legs": 3,
        "strategy": "straight_win"
    }
    response = client.post("/api/v1/accumulators/build", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_odds"] >= 1.5
    assert len(data["legs"]) >= 2
    assert data["sportybet_code"] is None and data["bet9ja_code"] is None
    assert data["is_upcoming_verified"] is True
    assert data["match_search_list"] is not None
    assert len(data["match_search_list"]) > 10

def test_track_record_and_challenge_endpoints():
    r1 = client.get("/api/v1/track-record")
    assert r1.status_code == 200
    stats = r1.json()
    assert {"win_rate_pct", "roi_pct", "entries"} <= stats.keys()
    assert client.post("/api/v1/admin/settle?match=x&prediction=y&odds=2&stake_ngn=1&result=won").status_code in (404, 405)

    assert client.get("/api/v1/challenge/ladder").status_code == 404

def test_admin_endpoints_require_the_admin_token():
    for path in ("/api/v1/jobs/run", "/api/v1/fixtures/refresh"):
        assert client.post(path).status_code == 401
        assert client.post(path, headers={"X-Admin-Token": "wrong"}).status_code == 401

def test_cors_only_allows_the_web_app():
    allowed = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    other = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers