"""
Learning-to-Rank (LTR) Model — Pairwise ranking.

Re-ranks triggered strategies by predicted revenue lift.
Training data: historical (merchant_features, strategy_chosen, revenue_outcome) tuples.
Metric: NDCG@3 > 0.70.

File: backend/engines/strategy/models/ranker.py
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("bravola.strategy.ranker")


class StrategyRanker:
    """
    Learning-to-Rank model for strategy re-ranking.

    In Phase 1 (0–50 merchants): returns default lift scores.
    In Phase 2+: uses trained pairwise ranking model.
    """

    def __init__(self, model: Optional[Any] = None):
        self._model = model

    def predict_lift_scores(
        self,
        rule_ids: List[str],
        merchant_features: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Predict revenue lift score (0–1) for each candidate strategy.

        Returns dict of {rule_id: lift_score}.
        """
        if self._model is not None:
            return self._predict_with_model(rule_ids, merchant_features)
        return self._default_scores(rule_ids)

    def _predict_with_model(
        self,
        rule_ids: List[str],
        merchant_features: Dict[str, float],
    ) -> Dict[str, float]:
        """Use trained LTR model."""
        try:

            scores = {}
            for rule_id in rule_ids:
                # In production: build feature vector from (merchant_features + rule_features)
                # and predict pairwise lift score
                scores[rule_id] = 0.5  # Placeholder
            return scores
        except Exception as exc:
            logger.warning("LTR model inference failed: %s", exc)
            return self._default_scores(rule_ids)

    def _default_scores(self, rule_ids: List[str]) -> Dict[str, float]:
        """Default lift scores based on rule type heuristics."""
        defaults = {
            "REV-01": 0.91,  # Win-back → high lift
            "REV-02": 0.65,  # Upsell → moderate
            "REV-03": 0.88,  # Cart recovery → high
            "REV-04": 0.55,  # LTV boost → moderate
            "REV-05": 0.50,  # Email optimisation
            "ENG-01": 0.60,  # Re-engagement
            "ENG-02": 0.35,  # Sunset → low lift
            "ENG-03": 0.78,  # Conversion boost
            "AUD-01": 0.85,  # Welcome series → high
            "AUD-02": 0.45,  # Referral
            "AUD-03": 0.72,  # Post-purchase nurture
        }
        return {rid: defaults.get(rid, 0.50) for rid in rule_ids}
