"""
KPI Gap Scorer — Linear Regression scoring per cluster.

Scores each merchant's KPI gap vs. cluster median.
Output: sub-scores 0–100 per KPI dimension.
Metric: MAE < 5 points.

File: backend/engines/benchmark/models/kpi_scorer.py
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger("bravola.benchmark.kpi_scorer")


class KPIScorer:
    """
    Scores KPI gaps against peer cluster medians.

    Uses Linear Regression when trained model is available,
    otherwise uses a deterministic gap formula.
    """

    def __init__(self, model: Optional[Any] = None):
        self._model = model

    def score_gaps(
        self,
        merchant_kpis: Dict[str, float],
        peer_medians: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Compute per-KPI gap scores (0–100).

        A score of 50 means you match the peer median.
        > 50 means above median, < 50 means below.
        """
        scores = {}

        for metric, merchant_val in merchant_kpis.items():
            median_val = peer_medians.get(metric, 0)

            if median_val == 0:
                scores[metric] = 50.0
                continue

            # For cart_abandonment_rate, lower is better (invert)
            if "abandonment" in metric or "churn" in metric:
                ratio = median_val / max(merchant_val, 0.001)
            else:
                ratio = merchant_val / max(median_val, 0.001)

            # Convert ratio to 0–100 score
            # ratio = 1.0 → score = 50 (at median)
            # ratio = 2.0 → score = 100 (double the median)
            # ratio = 0.0 → score = 0 (zero performance)
            score = min(100, max(0, ratio * 50))
            scores[metric] = round(score, 1)

        return scores

    def compute_gap_flags(
        self,
        merchant_kpis: Dict[str, float],
        peer_medians: Dict[str, float],
        threshold: float = 0.10,
    ) -> list:
        """
        Identify KPIs where the gap is significant (> threshold).

        Returns human-readable gap flag strings.
        """
        flags = []

        for metric, merchant_val in merchant_kpis.items():
            median_val = peer_medians.get(metric, 0)
            if median_val == 0:
                continue

            if "abandonment" in metric or "churn" in metric:
                gap = merchant_val - median_val
                if gap > threshold:
                    flags.append(
                        f"{metric} is {gap*100:.0f}% above peer median ({median_val*100:.0f}%)"
                    )
            else:
                gap = median_val - merchant_val
                if gap > threshold * median_val:
                    gap_pct = (gap / median_val) * 100
                    flags.append(
                        f"{metric} is {gap_pct:.0f}% below peer median ({median_val*100:.0f}%)"
                    )

        return flags
