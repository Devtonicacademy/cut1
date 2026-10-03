import pytest
from starlette.testclient import TestClient

from apps.api.app import auth
from apps.api.app.data import db
from apps.api.app.main import app
from apps.api.app.tracking import reports

ADMIN_EMAIL = "devtonicllc@gmail.com"


@pytest.fixture(autouse=True)
def fake_google(monkeypatch):
    """Replaces the network call to Google: credentials look like 'ok:<email>' or are rejected."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.delenv("ADMIN_EMAILS", raising=False)

    def verify(credential):
        if not credential.startswith("ok:"):
            raise ValueError("bad token")
        return {"email": credential[3:], "email_verified": True, "name": "Test User", "picture": "https://pic.example/u.png"}

    monkeypatch.setattr(auth, "verify_google_credential", verify)


def _signed_in(email):
    client = TestClient(app)
    res = client.post("/api/v1/auth/google", json={"credential": f"ok:{email}"})
    assert res.status_code == 200
    return client, res


def test_config_exposes_the_public_client_id_only(monkeypatch):
    client = TestClient(app)
    assert client.get("/api/v1/auth/config").json() == {"google_client_id": "test-client-id.apps.googleusercontent.com"}
    monkeypatch.delenv("GOOGLE_CLIENT_ID")
    assert client.get("/api/v1/auth/config").json() == {"google_client_id": None}


def test_sign_in_sets_a_locked_down_cookie_and_logout_ends_the_session():
    client, res = _signed_in("someone@example.com")
    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie
    assert res.json()["user"] == {
        "email": "someone@example.com", "name": "Test User", "picture": "https://pic.example/u.png", "role": "user"}
    assert client.get("/api/v1/auth/me").json()["user"]["email"] == "someone@example.com"

    stolen = client.cookies.get(auth.COOKIE_NAME)
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").json() == {"user": None}
    replay = TestClient(app)
    replay.cookies.set(auth.COOKIE_NAME, stolen)
    assert replay.get("/api/v1/auth/me").json() == {"user": None}  # the old cookie no longer works


def test_the_session_token_is_stored_only_as_a_hash():
    client, _ = _signed_in("hash-check@example.com")
    token = client.cookies.get(auth.COOKIE_NAME)
    with db.connect() as conn:
        stored = [r["token_hash"] for r in conn.execute("SELECT token_hash FROM sessions")]
    assert token not in stored and auth._hash(token) in stored


def test_bad_or_unverified_credentials_are_refused(monkeypatch):
    client = TestClient(app)
    res = client.post("/api/v1/auth/google", json={"credential": "forged"})
    assert res.status_code == 401 and "set-cookie" not in res.headers

    # The real verifier rejects an email Google has not verified, and refuses to run unconfigured.
    monkeypatch.undo()  # drop the fake verifier for this part
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "x")
    import google.oauth2.id_token as gid
    monkeypatch.setattr(gid, "verify_oauth2_token", lambda *a, **k: {
        "iss": "https://accounts.google.com", "email": ADMIN_EMAIL, "email_verified": False})
    with pytest.raises(ValueError, match="not verified"):
        auth.verify_google_credential("anything")
    monkeypatch.delenv("GOOGLE_CLIENT_ID")
    with pytest.raises(ValueError, match="not configured"):
        auth.verify_google_credential("anything")


def test_only_the_admin_email_gets_the_admin_role_and_reports():
    anonymous = TestClient(app)
    assert anonymous.get("/api/v1/admin/reports/predictions").status_code == 401

    user, _ = _signed_in("fan@example.com")
    assert user.get("/api/v1/auth/me").json()["user"]["role"] == "user"
    assert user.get("/api/v1/admin/reports/predictions").status_code == 403

    admin, res = _signed_in(ADMIN_EMAIL)
    assert res.json()["user"]["role"] == "admin"
    report = admin.get("/api/v1/admin/reports/predictions")
    assert report.status_code == 200
    assert set(report.json()) == {"generated_at", "summary", "calibration", "leagues", "matches"}


def test_admin_emails_come_from_the_environment_and_ignore_case(monkeypatch):
    assert auth.role_for("DevtonicLLC@Gmail.com") == "admin"
    monkeypatch.setenv("ADMIN_EMAILS", "boss@example.com, Second@Example.com")
    assert auth.role_for("second@example.com") == "admin"
    assert auth.role_for(ADMIN_EMAIL) == "user"  # the default applies only when the variable is unset


def test_saving_fixtures_is_private_to_each_user():
    alice, _ = _signed_in("alice@example.com")
    bob, _ = _signed_in("bob@example.com")
    fixture = alice.get("/api/v1/fixtures").json()[0]

    assert TestClient(app).get("/api/v1/me/saved").status_code == 401
    assert TestClient(app).post("/api/v1/me/saved", json={"fixture_id": fixture["id"]}).status_code == 401

    saved = alice.post("/api/v1/me/saved", json={"fixture_id": fixture["id"]}).json()
    assert [s["fixture_id"] for s in saved] == [fixture["id"]]
    assert saved[0]["home_team"] == fixture["home_team"]["name"] and saved[0]["status"] == "upcoming"
    assert alice.post("/api/v1/me/saved", json={"fixture_id": fixture["id"]}).json() == saved  # saving twice is harmless
    assert bob.get("/api/v1/me/saved").json() == []

    assert alice.post("/api/v1/me/saved", json={"fixture_id": "no-such-fixture"}).status_code == 404
    assert alice.delete(f"/api/v1/me/saved/{fixture['id']}").json() == []
    assert alice.get("/api/v1/me/saved").json() == []


def test_a_saved_fixture_shows_its_result_once_the_match_is_graded():
    client, _ = _signed_in("watcher@example.com")
    fixture = client.get("/api/v1/fixtures").json()[0]
    client.post("/api/v1/me/saved", json={"fixture_id": fixture["id"]})
    with db.connect() as conn:  # pretend the ledger graded it: home win 2-1
        conn.execute(
            """INSERT INTO predictions (fixture_id, div, match_date, kickoff_utc, home_team, away_team, created_at, model,
               p_home, p_draw, p_away, pick, pick_prob, prev_hash, hash, fthg, ftag, correct, graded_at)
               VALUES (?, 'E0', '2026-01-01', '2026-01-01T15:00:00+00:00', 'A', 'B', 'x', 'm', .5, .3, .2, '1', .5, 'p', 'h', 2, 1, 1, 'x')""",
            (fixture["id"],))
    try:
        item = client.get("/api/v1/me/saved").json()[0]
        assert (item["status"], item["home_goals"], item["away_goals"], item["actual"], item["pick_correct"]) == ("finished", 2, 1, "1", True)
        assert (item["pick"], item["p_home"]) == ("1", 0.5)  # the locked prediction, not the current one
    finally:
        with db.connect() as conn:
            conn.execute("DELETE FROM predictions WHERE fixture_id = ?", (fixture["id"],))


def _ledger_row(conn, n, pick, probs, score, graded=True):
    hg, ag = score if score else (None, None)
    conn.execute(
        """INSERT INTO predictions (fixture_id, div, match_date, kickoff_utc, home_team, away_team, created_at, model,
           p_home, p_draw, p_away, pick, pick_prob, prev_hash, hash, fthg, ftag, correct, graded_at)
           VALUES (?, 'E0', ?, ?, ?, ?, 'x', 'm', ?, ?, ?, ?, ?, 'p', 'h', ?, ?, ?, ?)""",
        (f"f{n}", f"2026-02-0{n}", f"2026-02-0{n}T15:00:00+00:00", f"Home{n}", f"Away{n}", *probs, pick, max(probs),
         hg, ag, None if hg is None else int(("1" if hg > ag else "X" if hg == ag else "2") == pick), "x" if graded else None))


def test_report_compares_predictions_with_results(tmp_path):
    with db.connect(tmp_path / "r.db") as conn:
        _ledger_row(conn, 1, "1", (0.6, 0.25, 0.15), (2, 0))   # right
        _ledger_row(conn, 2, "1", (0.5, 0.3, 0.2), (0, 1))     # wrong: away win
        _ledger_row(conn, 3, "2", (0.2, 0.2, 0.6), (1, 1))     # wrong: draw
        _ledger_row(conn, 4, "1", (0.7, 0.2, 0.1), None, graded=False)   # not played yet
        _ledger_row(conn, 5, "1", (0.4, 0.3, 0.3), None, graded=True)    # voided: no result
        report = reports.build_report(conn)

    s = report.summary
    assert (s.locked, s.graded, s.pending, s.voided, s.correct) == (5, 3, 1, 1, 1)
    assert s.accuracy_pct == 33.3 and s.avg_confidence_pct == 56.7
    # Brier per match: home win 2-0 -> .4^2+.25^2+.15^2 = .245; away win 0-1 -> .5^2+.3^2+.8^2 = .98; draw 1-1 -> .2^2+.8^2+.6^2 = 1.04
    assert s.brier == pytest.approx((0.245 + 0.98 + 1.04) / 3, abs=1e-4)
    assert s.baseline_brier == pytest.approx(0.6667, abs=1e-3)  # one of each outcome: predicting 1/3 each
    assert s.log_loss == pytest.approx(-(__import__("math").log(0.6) + __import__("math").log(0.2) + __import__("math").log(0.2)) / 3, abs=1e-3)

    by_id = {m.id: m for m in report.matches}
    assert (by_id["f1"].status, by_id["f1"].actual, by_id["f1"].correct) == ("graded", "1", True)
    assert (by_id["f3"].actual, by_id["f3"].correct, by_id["f3"].home_goals) == ("X", False, 1)
    assert (by_id["f4"].status, by_id["f4"].correct) == ("pending", None)
    assert by_id["f5"].status == "void"
    assert [m.id for m in report.matches] == ["f5", "f4", "f3", "f2", "f1"]  # newest first
    assert report.leagues[0].league == "English Premier League" and report.leagues[0].graded == 3
    assert sum(b.count for b in report.calibration) == 3
    top_bin = next(b for b in report.calibration if b.label == "60-70%")
    assert (top_bin.count, top_bin.avg_predicted_pct, top_bin.actual_pct) == (2, 60.0, 50.0)


def test_report_is_empty_but_valid_with_no_predictions(tmp_path):
    with db.connect(tmp_path / "e.db") as conn:
        report = reports.build_report(conn)
    assert report.summary.locked == 0 and report.summary.accuracy_pct == 0.0 and report.matches == []
