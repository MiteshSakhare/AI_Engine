"""
Deterministic Health Score Formula — Upgraded v2.

health_score = (0.30 × acquisition_score)
             + (0.30 × conversion_score)
             + (0.40 × retention_score)

Each sub-score uses:
  1. Winsorization — clamps merchant_val to ±2σ of the peer cluster
     before Z-score calculation, preventing extreme outliers from
     skewing results.
  2. Null/Missing safety — a missing metric (None or absent) substitutes
     the peer_mean, producing a neutral Z-score of 0 → score of 50.
     This is semantically correct: "we don't know" ≠ "worst performer".

File: backend/engines/benchmark/health_score.py
"""

from __future__ import annotations

import math
from typing import Dict, Optional


# ── Funnel Stage Weights ────────────────────────────────
ACQUISITION_WEIGHT = 0.30
CONVERSION_WEIGHT  = 0.30
RETENTION_WEIGHT   = 0.40

# ── Winsorization Cap (±N std devs from the peer mean) ──
WINSOR_CAP_SIGMA = 2.0


# ── Public API ──────────────────────────────────────────

def compute_health_score(
    merchant_kpis: Dict[str, Optional[float]],
    peer_medians:  Dict[str, float],
    peer_stds:     Dict[str, float],
) -> dict:
    """
    Compute health_score and funnel sub-scores using Winsorized
    Z-scores mapped onto a Sigmoid 0–100 scale.

    Returns dict with:
    - health_score        (int, 0–100)
    - acquisition_score   (int, 0–100)
    - conversion_score    (int, 0–100)
    - retention_score     (int, 0–100)
    - missing_metrics     (list[str]) — metrics that had no value and
                          were substituted with the peer mean
    """

    missing: list[str] = []

    acquisition = _compute_acquisition_score(merchant_kpis, peer_medians, peer_stds, missing)
    conversion  = _compute_conversion_score( merchant_kpis, peer_medians, peer_stds, missing)
    retention   = _compute_retention_score(  merchant_kpis, peer_medians, peer_stds, missing)

    health = (
        ACQUISITION_WEIGHT * acquisition
        + CONVERSION_WEIGHT * conversion
        + RETENTION_WEIGHT  * retention
    )

    return {
        "health_score":      _clamp(int(round(health))),
        "acquisition_score": _clamp(int(round(acquisition))),
        "conversion_score":  _clamp(int(round(conversion))),
        "retention_score":   _clamp(int(round(retention))),
        "missing_metrics":   missing,
    }


# ── Sub-score Builders ──────────────────────────────────

def _compute_acquisition_score(
    kpis: Dict[str, Optional[float]],
    medians: Dict[str, float],
    stds: Dict[str, float],
    missing: list,
) -> float:
    scores = [
        _safe_z(kpis, medians, stds, "new_customer_rate",  missing),
        _safe_z(kpis, medians, stds, "open_rate_avg",      missing),
        _safe_z(kpis, medians, stds, "click_rate_avg",     missing),
        _safe_z(kpis, medians, stds, "opt_in_rate",        missing),  # NEW: list growth
    ]
    return sum(scores) / len(scores) if scores else 50.0


def _compute_conversion_score(
    kpis: Dict[str, Optional[float]],
    medians: Dict[str, float],
    stds: Dict[str, float],
    missing: list,
) -> float:
    scores = [
        _safe_z(kpis, medians, stds, "conversion_rate_avg", missing),
        _safe_z(kpis, medians, stds, "revenue_per_email",   missing),
    ]
    return sum(scores) / len(scores) if scores else 50.0


def _compute_retention_score(
    kpis: Dict[str, Optional[float]],
    medians: Dict[str, float],
    stds: Dict[str, float],
    missing: list,
) -> float:
    scores = [
        _safe_z(kpis, medians, stds, "repeat_purchase_rate", missing),
        _safe_z(kpis, medians, stds, "customer_ltv",         missing),
    ]

    # Cart abandonment: lower is better → invert the comparison
    # We treat (peer_abandonment - merchant_abandonment) as the "positive" direction
    m_abandon = _get_safe_val(kpis, "cart_abandonment_rate", medians, missing)
    p_abandon  = medians.get("cart_abandonment_rate", 0.60)
    std_abandon = stds.get("cart_abandonment_rate",   0.10)
    # Winsorise then invert sign so a lower abandonment → positive Z
    m_clamped = _winsorise(m_abandon, p_abandon, std_abandon)
    scores.append(_z_score(p_abandon, m_clamped, std_abandon))  # swapped order = inverted

    return sum(scores) / len(scores) if scores else 50.0


# ── Helpers ─────────────────────────────────────────────

def _safe_z(
    kpis: Dict[str, Optional[float]],
    medians: Dict[str, float],
    stds: Dict[str, float],
    metric: str,
    missing: list,
) -> float:
    """
    Get a Winsorized Z-score for `metric`.

    If the metric is absent/None in `kpis`, substitute the peer_mean
    (neutral contribution of 50) and record it in `missing`.
    """
    peer_mean = medians.get(metric, 0.0)
    std_dev   = stds.get(metric, 0.0)
    raw_val   = _get_safe_val(kpis, metric, medians, missing)
    clamped   = _winsorise(raw_val, peer_mean, std_dev)
    return _z_score(clamped, peer_mean, std_dev)


def _get_safe_val(
    kpis: Dict[str, Optional[float]],
    metric: str,
    medians: Dict[str, float],
    missing: list,
) -> float:
    """
    Return the metric value from `kpis`, substituting peer_mean when
    the value is missing (None or key absent).
    """
    val = kpis.get(metric)          # Returns None if absent
    if val is None or math.isnan(float(val if val is not None else 0)):
        missing.append(metric)
        return medians.get(metric, 0.0)   # Neutral substitution
    return float(val)


def _winsorise(val: float, mean: float, std_dev: float) -> float:
    """
    Clip `val` to [mean ± CAP_SIGMA * std_dev].

    Prevents a single extreme outlier from producing a Z-score so
    large it saturates the Sigmoid to 0 or 100.
    """
    if std_dev <= 0:
        return val
    lo = mean - WINSOR_CAP_SIGMA * std_dev
    hi = mean + WINSOR_CAP_SIGMA * std_dev
    return max(lo, min(hi, val))


def _z_score(val: float, peer_mean: float, std_dev: float) -> float:
    """
    Standardise `val` and map to 0–100 via Sigmoid.

    Sigmoid properties:
      peer_mean  → Z=0  → score 50
      +1 σ       → Z=+1 → score ~73
      -1 σ       → Z=-1 → score ~27
    """
    if std_dev <= 0:
        return 50.0
    z = (val - peer_mean) / std_dev
    return 100.0 / (1.0 + math.exp(-z))


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))
