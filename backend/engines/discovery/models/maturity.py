"""
Maturity Scorer — Logistic Regression (calibrated to 0–100) v2.

Calibrated probability × 100 → maturity_score.
Metric: MAE < 8 points.

Upgrades v2:
  - Input validation: all inputs clamped to non-negative values
    before scoring (prevents negative revenue or customer counts
    from corrupting results).
  - 5th component: email_engagement_score adds up to 10 bonus points,
    reflecting how operationally mature the merchant's marketing is.
  - Uses named-dict feature access (no brittle index chains).

File: backend/engines/discovery/models/maturity.py
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np

logger = logging.getLogger("bravola.discovery.maturity")

FEATURE_NAMES = [
    "avg_order_value",             # 0
    "repeat_rate",                 # 1
    "aov_variance",                # 2
    "product_concentration",       # 3
    "email_engagement_score",      # 4
    "total_customer_count",        # 5
    "revenue_last_90d",            # 6
    "days_to_second_purchase",     # 7
    "catalog_size",                # 8
    "purchase_frequency_variance", # 9
    "revenue_last_30d",            # 10
]


class MaturityScorer:
    """
    Logistic Regression-based maturity scorer.

    Falls back to a deterministic formula when the trained model
    is not available.
    """

    def __init__(self, model: Optional[Any] = None):
        self._model = model

    def predict(self, features: List[float]) -> int:
        """Predict maturity score (0–100) from feature array."""
        if self._model is not None:
            return self._predict_with_model(features)
        return self._predict_heuristic(features)

    def _predict_with_model(self, features: List[float]) -> int:
        """Use trained Logistic Regression model."""
        try:
            X = np.array(features).reshape(1, -1)
            proba = self._model.predict_proba(X)[0]
            score = float(proba[-1]) * 100
            return max(0, min(100, int(round(score))))
        except Exception as exc:
            logger.warning("Maturity model inference failed, using heuristic: %s", exc)
            return self._predict_heuristic(features)

    def _predict_heuristic(self, features: List[float]) -> int:
        """
        Deterministic 5-component maturity formula.

        Components and max points:
          Revenue (90d)       → 0–30 pts
          Customer base       → 0–25 pts
          Repeat rate         → 0–25 pts
          AOV                 → 0–10 pts   (reduced from 20 to make room for email)
          Email engagement    → 0–10 pts   (NEW)
                         Total: 0–100 pts
        """
        fd = _to_feature_dict(features)

        # Input validation — clamp all to non-negative
        revenue_90d  = max(0.0, fd["revenue_last_90d"])
        customers    = max(0.0, float(fd["total_customer_count"]))
        repeat_rate  = max(0.0, min(1.0, fd["repeat_rate"]))
        aov          = max(0.0, fd["avg_order_value"])
        email_eng    = max(0.0, min(1.0, fd["email_engagement_score"]))

        score = 0.0

        # ── Component 1: Revenue (0–30 pts) ─────────────
        if revenue_90d > 500_000:
            score += 30.0
        elif revenue_90d > 100_000:
            score += 20.0 + (revenue_90d - 100_000) / 400_000 * 10.0
        elif revenue_90d > 10_000:
            score += 5.0 + (revenue_90d - 10_000) / 90_000 * 15.0
        else:
            score += min(5.0, revenue_90d / 2_000.0)

        # ── Component 2: Customer base (0–25 pts) ────────
        if customers > 10_000:
            score += 25.0
        elif customers > 1_000:
            score += 10.0 + (customers - 1_000) / 9_000 * 15.0
        elif customers > 100:
            score += 3.0 + (customers - 100) / 900 * 7.0
        else:
            score += min(3.0, customers / 33.3)

        # ── Component 3: Repeat rate (0–25 pts) ──────────
        score += min(25.0, repeat_rate * 100.0)

        # ── Component 4: AOV (0–10 pts) ──────────────────
        if aov > 200:
            score += 10.0
        elif aov > 50:
            score += 4.0 + (aov - 50) / 150 * 6.0
        else:
            score += min(4.0, aov / 12.5)

        # ── Component 5: Email engagement (0–10 pts) ─────
        # email_engagement_score is already 0.0–1.0
        score += min(10.0, email_eng * 10.0)

        return max(0, min(100, int(round(score))))


def _to_feature_dict(features: List[float]) -> dict:
    """Convert feature array to named dict with safe defaults."""
    return {
        name: float(features[i]) if i < len(features) else 0.0
        for i, name in enumerate(FEATURE_NAMES)
    }
