"""
Vertical Classifier — Random Forest multi-class.

Labels: beauty | apparel | food | home | pet | sports | other
Uses onboarding_vertical_hint as a strong prior feature.
Metric: Top-1 accuracy > 0.80

File: backend/engines/discovery/models/vertical.py
"""

import logging
import numpy as np
from typing import Tuple, Optional, Any, List

logger = logging.getLogger("bravola.discovery.vertical")

VERTICAL_LABELS = ["beauty", "apparel", "food", "home", "pet", "sports", "other"]


class VerticalClassifier:
    """
    Random Forest-based vertical classifier.

    Falls back to onboarding hint or heuristic when trained
    model is not available.
    """

    def __init__(self, model: Optional[Any] = None):
        self._model = model

    def predict(
        self,
        features: List[float],
        vertical_hint: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Predict vertical from features + optional onboarding hint.

        Returns (vertical_label, confidence).
        """
        # If we have a strong onboarding hint, use it (high confidence)
        if vertical_hint:
            hint_lower = vertical_hint.lower().strip()
            for label in VERTICAL_LABELS:
                if label in hint_lower or hint_lower in label:
                    return label, 0.92
            # Partial match
            if any(kw in hint_lower for kw in ["cloth", "fashion", "wear"]):
                return "apparel", 0.85
            if any(kw in hint_lower for kw in ["cosmetic", "skin", "makeup"]):
                return "beauty", 0.85
            if any(kw in hint_lower for kw in ["kitchen", "decor", "furniture"]):
                return "home", 0.85
            if any(kw in hint_lower for kw in ["dog", "cat", "animal"]):
                return "pet", 0.85
            if any(kw in hint_lower for kw in ["fitness", "gym", "outdoor"]):
                return "sports", 0.85
            if any(kw in hint_lower for kw in ["snack", "beverage", "organic"]):
                return "food", 0.85

        # Try trained model
        if self._model is not None:
            return self._predict_with_model(features)

        return "other", 0.50

    def _predict_with_model(self, features: List[float]) -> Tuple[str, float]:
        """Use trained Random Forest model."""
        try:
            model = self._model
            if not model:
                return "other", 0.40
            X = np.array(features).reshape(1, -1)
            probas = model.predict_proba(X)[0]
            idx = int(np.argmax(probas))
            return VERTICAL_LABELS[idx], float(probas[idx])
        except Exception as exc:
            logger.warning("Model inference failed: %s", exc)
            return "other", 0.40
