"""
Persona Classifier — XGBoost multi-class classification v2.

Labels: loyalist | value_seeker | explorer | bargain_hunter |
        discount_driven | high_value_whales

Upgrades v2:
  - Replaced fragile index-based feature access (features[0]) with
    named feature dict access — testable and maintainable.
  - Richer heuristic tier coverage for all 6 persona labels.
  - Confidence decay when features are missing or zero — prevents
    false high-confidence predictions on sparse data.

File: backend/engines/discovery/models/persona.py
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("bravola.discovery.persona")

PERSONA_LABELS = [
    "loyalist",
    "value_seeker",
    "explorer",
    "bargain_hunter",
    "discount_driven",
    "high_value_whales",
]

# Feature names in order (matches features_to_array output)
FEATURE_NAMES = [
    "avg_order_value",            # 0
    "repeat_rate",                # 1
    "aov_variance",               # 2
    "product_concentration",      # 3
    "email_engagement_score",     # 4
    "total_customer_count",       # 5
    "revenue_last_90d",           # 6
    "days_to_second_purchase",    # 7
    "catalog_size",               # 8
    "purchase_frequency_variance",# 9
    "revenue_last_30d",           # 10
]

# Minimum populated features before we apply confidence decay
MIN_FEATURES_FOR_FULL_CONFIDENCE = 5


class PersonaClassifier:
    """
    XGBoost-based persona classifier.

    Falls back to a rule-based heuristic when the trained model is
    not available (MVP / early phase).
    """

    def __init__(self, model: Optional[Any] = None):
        self._model = model

    def predict(self, features: List[float]) -> Tuple[str, float]:
        """
        Predict persona from feature array.

        Returns (persona_label, confidence).
        """
        if self._model is not None:
            return self._predict_with_model(features)
        return self._predict_heuristic(features)

    def _predict_with_model(self, features: List[float]) -> Tuple[str, float]:
        """Use trained XGBoost model."""
        try:
            X = np.array(features).reshape(1, -1)
            probas = self._model.predict_proba(X)[0]
            idx = int(np.argmax(probas))
            return PERSONA_LABELS[idx], float(probas[idx])
        except Exception as exc:
            logger.warning("Persona model inference failed, using heuristic: %s", exc)
            return self._predict_heuristic(features)

    def _predict_heuristic(self, features: List[float]) -> Tuple[str, float]:
        """
        Rule-based fallback.

        Uses a named-dict approach to safely access features without
        relying on brittle index positions.
        """
        fd = _to_feature_dict(features)

        aov       = fd["avg_order_value"]
        repeat    = fd["repeat_rate"]
        prod_conc = fd["product_concentration"]
        email_eng = fd["email_engagement_score"]
        rev_90d   = fd["revenue_last_90d"]

        # Confidence decay: reduce confidence proportionally to missing data
        populated = sum(1 for v in fd.values() if v > 0.0)
        decay     = min(1.0, populated / MIN_FEATURES_FOR_FULL_CONFIDENCE)

        # ── Tier 1: High-value whales ────────────────────
        # Very high AOV + strong repeat rate → premium loyal buyers
        if aov > 300 and repeat > 0.25:
            return "high_value_whales", round(0.90 * decay, 2)

        # ── Tier 2: Loyalists ────────────────────────────
        # High repeat + high email engagement
        if repeat > 0.25 and email_eng > 0.30:
            return "loyalist", round(0.80 * decay, 2)

        # ── Tier 3: Value seekers ────────────────────────
        # High AOV but low repeat → buys premium occasionally
        if aov > 100 and repeat < 0.15:
            return "value_seeker", round(0.74 * decay, 2)

        # ── Tier 4: Discount-driven ──────────────────────
        # Low AOV + decent email engagement + moderate repeat
        # (responds to promotions, not brand loyal)
        if aov < 40 and email_eng > 0.20 and repeat > 0.12:
            return "discount_driven", round(0.76 * decay, 2)

        # ── Tier 5: Explorers ────────────────────────────
        # Low product concentration → broad purchasers, try everything
        if prod_conc < 0.30:
            return "explorer", round(0.68 * decay, 2)

        # ── Tier 6: Bargain hunters ──────────────────────
        # Low AOV + low email engagement → price-primary motivation
        if aov < 50 and email_eng < 0.15:
            return "bargain_hunter", round(0.72 * decay, 2)

        # ── Default ──────────────────────────────────────
        return "explorer", round(0.50 * decay, 2)


def _to_feature_dict(features: List[float]) -> Dict[str, float]:
    """
    Convert feature array to a named dict using FEATURE_NAMES.

    Missing positions are safely defaulted to 0.0.
    """
    return {
        name: float(features[i]) if i < len(features) else 0.0
        for i, name in enumerate(FEATURE_NAMES)
    }
