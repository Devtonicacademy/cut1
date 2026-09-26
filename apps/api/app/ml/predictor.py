"""
Loads the trained match model and turns live features into win/draw/loss
probabilities plus plain-English reasons for the prediction.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np

from apps.api.app.data import db
from apps.api.app.ml.features import FEATURE_SETS, has_market

VARIANT_LABELS = {
    "with_market": "football data + bookmaker consensus",
    "football_only": "football data only",
}

MODEL_DIR = db.REPO_ROOT / "data" / "models"
MODEL_PATH = Path(os.getenv("LIVELYBORG_MODEL_PATH") or MODEL_DIR / "match_model.joblib")
REPORT_PATH = MODEL_DIR / "report.json"


class MatchPredictor:
    def __init__(self, path: Path = MODEL_PATH):
        self.path = path
        self._mtime: Optional[float] = None
        self._bundle: Optional[Dict] = None
        self.reload_if_changed()

    def reload_if_changed(self) -> None:
        mtime = self.path.stat().st_mtime if self.path.exists() else None
        if mtime != self._mtime:
            self._bundle = joblib.load(self.path) if mtime else None
            self._mtime = mtime

    @property
    def available(self) -> bool:
        # A bundle trained on a different feature layout is ignored until the model is retrained
        return self._bundle is not None and self._bundle.get("feature_sets") == FEATURE_SETS

    @property
    def report(self) -> Dict:
        return self._bundle["report"] if self._bundle else {}

    @property
    def value_policy(self) -> Dict:
        return self.report.get("value_policy", {"enabled": False})

    def predict(self, features: Dict) -> Tuple[Tuple[float, float, float], str]:
        """Returns (home, draw, away) probabilities and the variant used."""
        variant = "with_market" if has_market(features) else "football_only"
        names = self._bundle["feature_sets"][variant]
        row = np.array([[np.nan if features.get(k) is None else float(features[k]) for k in names]])
        p = self._bundle["models"][variant].predict_proba(row)[0]
        return (float(p[0]), float(p[1]), float(p[2])), variant

    def describe(self, variant: str) -> str:
        info = self.report.get("variants", {}).get(variant, {})
        return (f"Trained {info.get('algorithm', 'ML')} model on {VARIANT_LABELS[variant]} "
                f"({info.get('matches_used', 0):,} matches)")


def key_factors(f: Dict, home: str, away: str, limit: int = 4) -> List[str]:
    """The facts behind a prediction, strongest first, in plain English."""
    factors: List[Tuple[float, str]] = []

    def pick(diff: float) -> Tuple[str, str]:
        return (home, away) if diff > 0 else (away, home)

    elo = f.get("elo_diff")
    if elo is not None and abs(elo) >= 40:
        better, _ = pick(elo)
        factors.append((abs(elo) / 40, f"{better} are the stronger side on long-term rating (Elo gap {abs(elo):.0f})"))

    hf, af = f.get("home_form_pts"), f.get("away_form_pts")
    if hf is not None and af is not None and abs(hf - af) >= 0.4:
        better, worse = pick(hf - af)
        hi, lo = max(hf, af), min(hf, af)
        factors.append((abs(hf - af) / 0.4, f"{better} in better recent form ({hi:.1f} vs {lo:.1f} points per game)"))

    hs, as_ = f.get("home_sot_for"), f.get("away_sot_for")
    if hs is not None and as_ is not None and abs(hs - as_) >= 1.2:
        better, _ = pick(hs - as_)
        factors.append((abs(hs - as_) / 1.2, f"{better} creating more chances ({max(hs, as_):.1f} vs {min(hs, as_):.1f} shots on target per game)"))

    ht, at = f.get("home_table_pct"), f.get("away_table_pct")
    if ht is not None and at is not None and (f.get("season_games") or 0) >= 3 and abs(ht - at) >= 0.3:
        better, _ = pick(at - ht)  # lower percentile = higher in the table
        factors.append((abs(ht - at) / 0.3, f"{better} sit clearly higher in the league table"))

    hr, ar = f.get("home_rest_days"), f.get("away_rest_days")
    if hr is not None and ar is not None and abs(hr - ar) >= 3 and min(hr, ar) <= 4:
        rested, tired = pick(hr - ar)
        factors.append((1.0, f"{rested} are fresher ({max(hr, ar):.0f} days' rest vs {min(hr, ar):.0f} for {tired})"))

    n, ppg = f.get("h2h_n") or 0, f.get("h2h_ppg_home")
    if n >= 3 and ppg is not None and (ppg >= 2.0 or ppg <= 0.7):
        who = home if ppg >= 2.0 else away
        factors.append((0.8, f"{who} have the upper hand in recent meetings ({n} games)"))

    mh, ma = f.get("mkt_p_home"), f.get("mkt_p_away")
    if mh is not None and ma is not None and max(mh, ma) >= 0.45:
        fav, p = (home, mh) if mh >= ma else (away, ma)
        factors.append((1.2, f"Bookmakers also make {fav} favourites ({p:.0%})"))

    if not factors:
        factors.append((0.0, "No strong edge in rating, form or schedule; treat this as an open game"))
    return [text for _, text in sorted(factors, key=lambda x: -x[0])[:limit]]
