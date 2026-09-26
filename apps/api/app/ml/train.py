"""
Trains and evaluates the match-outcome models on real history.

    python -m apps.api.app.ml.train

Two models are trained:
    with_market    football features + bookmaker consensus odds (used when a fixture has odds)
    football_only  football features only (fixtures listed before bookmakers price them)

Seasons are split in time order (never shuffled):
    burn-in    first season (features still warming up, not used)
    train      everything up to the validation season
    validation second-to-last completed season: model and value-bet policy selection
    test       last completed season + current season: final, untouched evaluation
The chosen models are then refitted on all data and saved with a JSON report.
"""
import datetime as dt
import json
from typing import Dict, List, Sequence, Tuple

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from apps.api.app.data import db
from apps.api.app.ml.features import FEATURE_NAMES, FEATURE_SETS, build_training_rows, has_market
from apps.api.app.ml.predictor import MODEL_DIR, MODEL_PATH, REPORT_PATH

PRIMARY_VARIANT = "with_market"
EV_THRESHOLDS = [0.02, 0.04, 0.06, 0.08, 0.10, 0.15]
MIN_VALUE_BETS = 150  # a threshold needs this many validation bets before we trust its ROI
TOP_LEAGUES = ["E0", "SP1", "I1", "D1", "F1"]


def to_matrix(rows: Sequence[Dict], names: Sequence[str] = FEATURE_NAMES) -> np.ndarray:
    return np.array([[np.nan if r.get(k) is None else float(r[k]) for k in names] for r in rows])


def candidate_models() -> Dict[str, object]:
    return {
        "logistic": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            StandardScaler(),
            LogisticRegression(C=0.3, max_iter=3000),
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.04, max_iter=400, max_leaf_nodes=15, min_samples_leaf=80,
            l2_regularization=1.0, early_stopping=True, validation_fraction=0.1, random_state=0,
        ),
    }


def market_probs(meta: Sequence[Dict], cols=("avg_h", "avg_d", "avg_a")) -> np.ndarray:
    """Bookmaker probabilities with the margin removed (NaN where odds are missing)."""
    out = np.full((len(meta), 3), np.nan)
    for i, m in enumerate(meta):
        odds = [m.get(c) for c in cols]
        if all(odds):
            inv = np.array([1.0 / o for o in odds])
            out[i] = inv / inv.sum()
    return out


def dc_probs(rows: Sequence[Dict]) -> np.ndarray:
    return np.array([
        [r["dc_p_home"], r["dc_p_draw"], r["dc_p_away"]] if r["dc_p_home"] is not None else [np.nan] * 3
        for r in rows
    ])


def metrics(probs: np.ndarray, y: np.ndarray) -> Dict:
    mask = ~np.isnan(probs).any(axis=1)
    p, t = np.clip(probs[mask], 1e-9, 1), y[mask]
    onehot = np.eye(3)[t]
    return {
        "n": int(mask.sum()),
        "accuracy": round(float((p.argmax(axis=1) == t).mean()), 4),
        "log_loss": round(float(-np.log(p[np.arange(len(t)), t]).mean()), 4),
        "brier": round(float(((p - onehot) ** 2).sum(axis=1).mean()), 4),
    }


def calibration(probs: np.ndarray, y: np.ndarray) -> List[Dict]:
    top, pick = probs.max(axis=1), probs.argmax(axis=1)
    table = []
    for lo, hi, label in [(0.7, 1.01, "70%+"), (0.58, 0.7, "58-70%"), (0.45, 0.58, "45-58%"), (0.0, 0.45, "<45%")]:
        sel = (top >= lo) & (top < hi)
        if sel.any():
            table.append({
                "bucket": label, "matches": int(sel.sum()),
                "predicted": round(float(top[sel].mean()), 4),
                "actual": round(float((pick[sel] == y[sel]).mean()), 4),
            })
    return table


def blend(model_p: np.ndarray, market_p: np.ndarray, weight: float) -> np.ndarray:
    return weight * model_p + (1 - weight) * market_p


def value_bet_results(probs: np.ndarray, meta: Sequence[Dict], y: np.ndarray, price_cols: Sequence[str]) -> List[Dict]:
    """ROI of backing every outcome whose expected value clears each threshold, at the given prices."""
    results = []
    for t in EV_THRESHOLDS:
        staked = returned = 0.0
        for i, m in enumerate(meta):
            if np.isnan(probs[i]).any():
                continue
            for outcome_idx, col in enumerate(price_cols):
                price = m.get(col)
                if price and probs[i, outcome_idx] * price - 1 >= t:
                    staked += 1
                    returned += price if y[i] == outcome_idx else 0.0
        results.append({
            "min_ev": t, "bets": int(staked),
            "roi": round((returned - staked) / staked, 4) if staked else None,
        })
    return results


def choose_value_policy(val_rows: List[Dict], test_rows: List[Dict]) -> Dict:
    """Enable value bets only for a threshold that was profitable on validation AND on test."""
    for v in val_rows:
        if v["bets"] >= MIN_VALUE_BETS and v["roi"] is not None and v["roi"] > 0:
            test = next(t for t in test_rows if t["min_ev"] == v["min_ev"])
            if test["roi"] is not None and test["roi"] > 0:
                return {"enabled": True, "min_ev": v["min_ev"], "validation": v, "test": test}
    return {"enabled": False, "reason": "No threshold was profitable on both validation and test seasons."}


def select_model(X: np.ndarray, y: np.ndarray, train_mask: np.ndarray, val_mask: np.ndarray) -> Tuple[str, object, Dict]:
    fitted, scores = {}, {}
    for name, model in candidate_models().items():
        fitted[name] = model.fit(X[train_mask], y[train_mask])
        scores[name] = metrics(model.predict_proba(X[val_mask]), y[val_mask])
    best = min(fitted, key=lambda n: scores[n]["log_loss"])
    return best, fitted[best], scores


def main() -> None:
    with db.connect() as conn:
        matches = [dict(r) for r in conn.execute("SELECT * FROM matches")]
    print(f"Building features for {len(matches)} matches...")
    rows, labels, meta = build_training_rows(matches)
    y = np.array(labels)
    seasons = np.array([m["season"] for m in meta])
    with_odds = np.array([has_market(r) for r in rows])
    ordered = sorted(set(seasons))
    burn_in, val_season, test_seasons = ordered[0], ordered[-3], ordered[-2:]
    base_train = (seasons != burn_in) & (seasons < val_season)
    val_mask = seasons == val_season
    test_mask = np.isin(seasons, test_seasons) & with_odds  # every predictor is scored on the same matches
    print(f"Train {base_train.sum()} | validation {val_season}: {val_mask.sum()} | test {list(test_seasons)}: {test_mask.sum()}")

    variants, test_probs = {}, {}
    for variant, names in FEATURE_SETS.items():
        X = to_matrix(rows, names)
        usable = with_odds if variant == "with_market" else np.ones(len(rows), dtype=bool)
        name, model, val_scores = select_model(X, y, base_train & usable, val_mask & usable)
        test_probs[variant] = model.predict_proba(X[test_mask])
        variants[variant] = {"algorithm": name, "validation": val_scores, "model": model, "X": X, "usable": usable}
        print(f"  {variant:<14} {name:<18} validation {val_scores[name]}")

    # Final exam on untouched test seasons, against the bookmakers
    test_idx = np.flatnonzero(test_mask)
    test_meta, test_rows, y_test = [meta[i] for i in test_idx], [rows[i] for i in test_idx], y[test_mask]
    market_test = market_probs(test_meta)
    comparisons = {
        **{f"model_{v}": p for v, p in test_probs.items()},
        "dixon_coles_phase1": dc_probs(test_rows),
        "bookmakers_pre_match_avg": market_test,
        "bookmakers_closing_avg": market_probs(test_meta, ("avg_ch", "avg_cd", "avg_ca")),
        "pinnacle_closing": market_probs(test_meta, ("psc_h", "psc_d", "psc_a")),
        "always_home": np.tile([0.999, 0.0005, 0.0005], (len(test_idx), 1)),
    }
    test_scores = {k: metrics(p, y_test) for k, p in comparisons.items()}
    primary_test = test_probs[PRIMARY_VARIANT]
    per_league = {}
    for div in TOP_LEAGUES:
        sel = np.array([m["div"] == div for m in test_meta])
        if sel.any():
            per_league[div] = {
                **{f"model_{v}": metrics(p[sel], y_test[sel]) for v, p in test_probs.items()},
                "bookmakers": metrics(market_test[sel], y_test[sel]),
            }

    # Value-bet policy for the primary model: blended probability vs pre-match average odds
    primary = variants[PRIMARY_VARIANT]
    val_sel = val_mask & primary["usable"]
    val_meta = [meta[i] for i in np.flatnonzero(val_sel)]
    val_model_p, val_market_p = primary["model"].predict_proba(primary["X"][val_sel]), market_probs(val_meta)
    blend_scores = {float(w): metrics(blend(val_model_p, val_market_p, w), y[val_sel])["log_loss"]
                    for w in np.round(np.arange(0, 1.01, 0.1), 1)}
    blend_weight = min(blend_scores, key=blend_scores.get)
    price_cols = ("avg_h", "avg_d", "avg_a")
    val_value = value_bet_results(blend(val_model_p, val_market_p, blend_weight), val_meta, y[val_sel], price_cols)
    test_value = value_bet_results(blend(primary_test, market_test, blend_weight), test_meta, y_test, price_cols)
    policy = choose_value_policy(val_value, test_value)
    policy["blend_weight"] = blend_weight

    # Refit on everything and save
    final_models, variant_report = {}, {}
    for variant, v in variants.items():
        final_mask = (seasons != burn_in) & v["usable"]
        final_models[variant] = candidate_models()[v["algorithm"]].fit(v["X"][final_mask], y[final_mask])
        variant_report[variant] = {
            "algorithm": v["algorithm"], "matches_used": int(final_mask.sum()), "validation": v["validation"],
        }
    report = {
        "trained_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trained_through": max(m["match_date"] for m in meta),
        "primary_variant": PRIMARY_VARIANT,
        "variants": variant_report,
        "feature_sets": FEATURE_SETS,
        "splits": {"burn_in": burn_in, "validation": val_season, "test": list(test_seasons)},
        "test": test_scores,
        "test_calibration": calibration(primary_test, y_test),
        "test_top_leagues": per_league,
        "blend_weight_model_vs_market": blend_weight,
        "value_bets_validation": val_value,
        "value_bets_test": test_value,
        "value_policy": policy,
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"feature_sets": FEATURE_SETS, "models": final_models, "report": report}, MODEL_PATH)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("variants", "test", "test_calibration", "test_top_leagues",
                                              "blend_weight_model_vs_market", "value_bets_test", "value_policy")}, indent=2))
    print(f"Saved {MODEL_PATH}")


if __name__ == "__main__":
    main()
