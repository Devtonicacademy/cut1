"""
Test setup: points the app at a throwaway SQLite database filled with a deterministic,
synthetic league history and upcoming fixtures, so tests never hit the network or the
real data in ./data.
"""
import datetime as dt
import os
import tempfile

import numpy as np

_TMP_DIR = tempfile.mkdtemp(prefix="livelyborg-test-")
os.environ["LIVELYBORG_DB_PATH"] = os.path.join(_TMP_DIR, "test.db")
os.environ["LIVELYBORG_MODEL_PATH"] = os.path.join(_TMP_DIR, "match_model.joblib")
os.environ["LIVELYBORG_OFFLINE"] = "1"
os.environ["LIVELYBORG_AUTO_REFRESH"] = "0"
os.environ["GEMINI_API_KEY"] = ""  # never call Gemini from tests (load_dotenv won't override this)
os.environ["ADMIN_TOKEN"] = "test-admin-token"

import joblib  # noqa: E402  (everything below must follow the env setup above)

from apps.api.app.data import db  # noqa: E402
from apps.api.app.ml.features import FEATURE_SETS, build_training_rows, season_of  # noqa: E402
from apps.api.app.ml.train import candidate_models, to_matrix  # noqa: E402
from apps.api.app.services.dixon_coles import DixonColesEngine  # noqa: E402

TEST_DIVS = ["E0", "SP1", "I1", "D1", "F1", "N1"]
TEAMS_PER_DIV = 10
HOME_GOALS, AWAY_GOALS = 1.5, 1.15


def _market_odds(prob: float, margin: float) -> float:
    return round(1.0 / (prob * margin), 2)


def _odds_columns(engine, attack, defence, home, away) -> dict:
    """Bookmaker-style odds from the true scoring rates (5% margin on average, 2% at best price)."""
    p = engine.calculate_match_probabilities(
        attack[home], defence[away], attack[away], defence[home], 1.0, HOME_GOALS, AWAY_GOALS
    )
    probs = {"h": p["prob_home_win"], "d": p["prob_draw"], "a": p["prob_away_win"],
             "o25": p["prob_over_2_5"], "u25": p["prob_under_2_5"]}
    row = {}
    for k, prob in probs.items():
        row[f"avg_{k}"] = _market_odds(prob, 1.05)
        row[f"max_{k}"] = _market_odds(prob, 1.02)
    return row


def _seed_database() -> None:
    rng = np.random.default_rng(42)
    engine = DixonColesEngine()
    today = dt.date.today()
    now = dt.datetime.now(dt.timezone.utc)
    matches, fixtures = [], []

    for div in TEST_DIVS:
        teams = [f"{div} Team {i}" for i in range(TEAMS_PER_DIV)]
        attack = {t: float(np.exp(rng.normal(0, 0.25))) for t in teams}
        defence = {t: float(np.exp(rng.normal(0, 0.2))) for t in teams}

        for days_ago in range(600, 0, -7):
            day = today - dt.timedelta(days=days_ago)
            match_date, season = day.isoformat(), season_of(day)
            order = [str(t) for t in rng.permutation(teams)]
            for i in range(0, TEAMS_PER_DIV, 2):
                home, away = order[i], order[i + 1]
                lam = HOME_GOALS * attack[home] * defence[away]
                mu = AWAY_GOALS * attack[away] * defence[home]
                matches.append({
                    "div": div, "season": season, "match_date": match_date, "kickoff_utc": None,
                    "home_team": home, "away_team": away,
                    "fthg": int(rng.poisson(lam)), "ftag": int(rng.poisson(mu)),
                    "hst": int(rng.poisson(lam * 3.3)), "ast": int(rng.poisson(mu * 3.3)),
                    **_odds_columns(engine, attack, defence, home, away),
                })

        order = [str(t) for t in rng.permutation(teams)]
        for i in range(0, TEAMS_PER_DIV, 2):
            home, away = order[i], order[i + 1]
            kickoff = now + dt.timedelta(days=1 + i // 4, hours=2)
            fixtures.append({"div": div, "match_date": kickoff.date().isoformat(), "kickoff_utc": kickoff.isoformat(),
                             "home_team": home, "away_team": away,
                             **_odds_columns(engine, attack, defence, home, away)})

    kickoff = now + dt.timedelta(days=2, hours=3)
    fixtures.append({"div": "CL", "match_date": kickoff.date().isoformat(), "kickoff_utc": kickoff.isoformat(),
                     "home_team": "E0 Team 0", "away_team": "N1 Team 0", "home_div": "E0", "away_div": "N1"})

    fixtures.append({"div": "FRI", "match_date": kickoff.date().isoformat(), "kickoff_utc": kickoff.isoformat(),
                     "home_team": "Strongland", "away_team": "Weakland"})
    national = []
    for i in range(30):  # Strongland beats Weakland every time, plus enough games for both to count as rated
        day = (today - dt.timedelta(days=400 - 10 * i)).isoformat()
        national.append({"match_date": day, "home_team": "Strongland", "away_team": "Weakland", "fthg": 3, "ftag": 0,
                         "tournament": "Friendly", "neutral": 0})

    with db.connect() as conn:
        db.upsert_matches(conn, matches)
        db.upsert_national_matches(conn, national)
        db.replace_fixtures(conn, fixtures)
    _save_test_model(matches)


def _save_test_model(matches) -> None:
    """A small model trained on the synthetic history, with value bets switched on so that path is exercised."""
    rows, labels, _ = build_training_rows(matches)
    models = {v: candidate_models()["logistic"].fit(to_matrix(rows, names), labels) for v, names in FEATURE_SETS.items()}
    report = {
        "primary_variant": "with_market",
        "variants": {v: {"algorithm": "logistic", "matches_used": len(rows)} for v in FEATURE_SETS},
        "value_policy": {"enabled": True, "min_ev": 0.02, "blend_weight": 0.5},
    }
    joblib.dump({"feature_sets": FEATURE_SETS, "models": models, "report": report},
                os.environ["LIVELYBORG_MODEL_PATH"])


_seed_database()
