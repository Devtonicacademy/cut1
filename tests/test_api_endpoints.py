from starlette.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "SportyBet" in data["supported_bookmakers"]
    assert "Bet9ja" in data["supported_bookmakers"]

def test_get_fixtures_endpoint():
    response = client.get("/api/v1/fixtures?bankroll=25000")
    assert response.status_code == 200
    fixtures = response.json()
    assert len(fixtures) >= 5
    first = fixtures[0]
    assert "prediction" in first
    assert "sportybet_odds" in first
    assert "bet9ja_odds" in first

def test_bankroll_allocate_endpoint():
    # Pick a value bet from fixtures
    res = client.get("/api/v1/fixtures")
    first_fixture = res.json()[0]
    val_bets = first_fixture["prediction"]["value_bets"]

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
        "max_legs": 3
    }
    response = client.post("/api/v1/accumulators/build", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_odds"] >= 1.5
    assert len(data["legs"]) >= 2
    assert data["sportybet_code"].startswith("SB-")
    assert data["bet9ja_code"].startswith("B9-")

def test_track_record_and_challenge_endpoints():
    r1 = client.get("/api/v1/track-record")
    assert r1.status_code == 200
    stats = r1.json()
    assert stats["win_rate_pct"] > 0
    assert len(stats["entries"]) >= 5

    r2 = client.get("/api/v1/challenge/ladder")
    assert r2.status_code == 200
    challenge = r2.json()
    assert challenge["target_amount_ngn"] == 50000.0
