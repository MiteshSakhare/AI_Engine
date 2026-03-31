"""
Performance Classifier — Upgraded v2.

Labels: success | neutral | failure

Improvements:
  - Cluster-aware baselines: pass cluster_id to get peer-calibrated thresholds
    instead of universal hardcoded values.
  - 5-signal voting: added list_growth_rate as a 5th signal.
  - Stricter thresholds: success requires 4/5 signals (was 3/4).

File: backend/engines/feedback/classifier.py
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from engines.feedback.schemas import CampaignMetrics

logger = logging.getLogger("bravola.feedback.classifier")


# ── Cluster-calibrated baselines ─────────────────────────
# Keyed by cluster_id prefix (vertical). Falls back to "general".
# These align with the peer cluster medians in clustering.py.

_CLUSTER_BASELINES: Dict[str, Dict[str, float]] = {
    "beauty": {
        "open_rate": 0.25, "click_rate": 0.05, "conversion_rate": 0.014,
        "unsubscribe_rate": 0.004, "revenue_attributed": 150.0, "list_growth_rate": 0.01,
    },
    "apparel": {
        "open_rate": 0.22, "click_rate": 0.04, "conversion_rate": 0.012,
        "unsubscribe_rate": 0.004, "revenue_attributed": 120.0, "list_growth_rate": 0.01,
    },
    "food": {
        "open_rate": 0.28, "click_rate": 0.06, "conversion_rate": 0.018,
        "unsubscribe_rate": 0.003, "revenue_attributed": 180.0, "list_growth_rate": 0.015,
    },
    "electronics": {
        "open_rate": 0.19, "click_rate": 0.035, "conversion_rate": 0.009,
        "unsubscribe_rate": 0.005, "revenue_attributed": 200.0, "list_growth_rate": 0.008,
    },
    "health_wellness": {
        "open_rate": 0.26, "click_rate": 0.052, "conversion_rate": 0.015,
        "unsubscribe_rate": 0.004, "revenue_attributed": 140.0, "list_growth_rate": 0.012,
    },
    "general": {
        "open_rate": 0.20, "click_rate": 0.03, "conversion_rate": 0.010,
        "unsubscribe_rate": 0.005, "revenue_attributed": 100.0, "list_growth_rate": 0.008,
    },
}

_DEFAULT_BASELINE = _CLUSTER_BASELINES["general"]


def _get_baseline(cluster_id: Optional[str]) -> Dict[str, float]:
    """Return the best matching baseline for a cluster_id."""
    if not cluster_id:
        return _DEFAULT_BASELINE
    cluster_lower = cluster_id.lower()
    for vertical, baseline in _CLUSTER_BASELINES.items():
        if cluster_lower.startswith(vertical):
            return baseline
    return _DEFAULT_BASELINE


def classify_performance(
    metrics: CampaignMetrics,
    baseline: Optional[Dict[str, float]] = None,
    cluster_id: Optional[str] = None,
) -> str:
    """
    Classify campaign performance as success, neutral, or failure.

    Priority order:
    1. Hard failure signals (unsubscribes, zero engagement)
    2. 5-signal voting for success/neutral

    Args:
        metrics:    Measured campaign metrics.
        baseline:   Optional explicit baseline (overrides cluster_id lookup).
        cluster_id: Peer cluster identifier for adaptive baselines.
    """
    if baseline is None:
        baseline = _get_baseline(cluster_id)

    # ── Hard Failure Signals ────────────────────────────
    if metrics.unsubscribe_rate > baseline["unsubscribe_rate"] * 3:
        logger.info("Performance: failure (high unsubscribe %.4f > threshold %.4f)",
                    metrics.unsubscribe_rate, baseline["unsubscribe_rate"] * 3)
        return "failure"

    if metrics.conversion_rate == 0 and metrics.click_rate > 0.005:
        logger.info("Performance: failure (clicks but no conversions)")
        return "failure"

    if metrics.open_rate == 0 and metrics.click_rate == 0:
        logger.info("Performance: failure (zero engagement)")
        return "failure"

    # ── 5-Signal Success Voting ─────────────────────────
    success_count = 0

    if metrics.revenue_attributed > baseline["revenue_attributed"]:
        success_count += 1
    if metrics.open_rate > baseline["open_rate"]:
        success_count += 1
    if metrics.click_rate > baseline["click_rate"]:
        success_count += 1
    if metrics.conversion_rate > baseline["conversion_rate"]:
        success_count += 1
    # Signal 5: list growth (proxy for campaign virality / word-of-mouth)
    if metrics.list_growth_rate > baseline["list_growth_rate"]:
        success_count += 1

    if success_count >= 4:
        logger.info("Performance: success (%d/5 signals positive)", success_count)
        return "success"

    if success_count >= 2:
        logger.info("Performance: neutral (%d/5 signals positive)", success_count)
        return "neutral"

    logger.info("Performance: failure (%d/5 signals positive)", success_count)
    return "failure"
