"""
SHAP-based + Ollama-enhanced reasoning text generator for Discovery Engine.

Extracts top SHAP features driving the persona prediction
and formats into human-readable reasoning string.
Optionally enhances reasoning via Ollama LLM.

File: backend/engines/discovery/explainer.py
"""

import logging
from typing import Dict, Any, Optional

from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.discovery.explainer")

# Human-friendly feature labels
FEATURE_LABELS = {
    "avg_order_value": "average order value",
    "repeat_rate": "repeat purchase rate",
    "days_to_second_purchase": "days to second purchase",
    "product_concentration": "product concentration",
    "email_engagement_score": "email engagement score",
    "total_customer_count": "total customer count",
    "revenue_last_90d": "90-day revenue",
    "revenue_last_30d": "30-day revenue",
}


async def generate_reasoning(
    persona: str,
    vertical: str,
    maturity_score: int,
    initial_focus: str,
    features: Dict[str, Any],
    shap_values: Optional[Dict[str, float]] = None,
) -> str:
    """
    Generate human-readable reasoning text.

    If SHAP values are available, uses top-2 features.
    Then enhances via Ollama if available.
    """
    # Build heuristic reasoning first
    if shap_values:
        base_reasoning = _shap_reasoning(persona, maturity_score, shap_values)
    else:
        base_reasoning = _heuristic_reasoning(persona, vertical, maturity_score, initial_focus, features)

    # Enhance with Ollama
    enhanced = await ollama_client.enhance_reasoning(
        engine_name="Discovery Engine",
        heuristic_reasoning=base_reasoning,
        context={
            "persona": persona,
            "vertical": vertical,
            "maturity_score": maturity_score,
            "initial_focus": initial_focus,
            "repeat_rate": features.get("repeat_rate", 0),
            "revenue_90d": features.get("revenue_last_90d", 0),
        },
    )
    return enhanced


def _shap_reasoning(
    persona: str,
    maturity_score: int,
    shap_values: Dict[str, float],
) -> str:
    """Build reasoning from top-2 SHAP features."""
    sorted_features = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
    top_features = [sorted_features[i] for i in range(min(2, len(sorted_features)))]

    parts = []
    for feat_name, importance in top_features:
        label = FEATURE_LABELS.get(feat_name, feat_name)
        direction = "strong" if importance > 0 else "low"
        parts.append(f"{direction} {label}")

    features_text = " and ".join(parts)
    return (
        f"{features_text.capitalize()} drove the '{persona}' classification. "
        f"Maturity score of {maturity_score} reflects the store's current growth stage."
    )


def _heuristic_reasoning(
    persona: str,
    vertical: str,
    maturity_score: int,
    initial_focus: str,
    features: Dict[str, Any],
) -> str:
    """Build reasoning from raw feature values."""
    repeat_rate = features.get("repeat_rate", 0)
    revenue_90d = features.get("revenue_last_90d", 0)

    parts = []

    rr_pct = round(repeat_rate * 100, 1) if repeat_rate < 1 else round(repeat_rate, 1)
    if repeat_rate > 0.20:
        parts.append(f"High repeat rate ({rr_pct}%)")
    elif repeat_rate > 0.10:
        parts.append(f"Moderate repeat rate ({rr_pct}%)")
    else:
        parts.append(f"Low repeat rate ({rr_pct}%)")

    if revenue_90d > 100_000:
        parts.append(f"strong 90-day revenue (${revenue_90d:,.0f})")
    elif revenue_90d > 10_000:
        parts.append(f"moderate 90-day revenue (${revenue_90d:,.0f})")

    signals = " and ".join(parts)

    focus_explanation = {
        "acquisition": "opportunity to grow the customer base",
        "retention": "clear retention opportunity",
        "engagement": "potential to deepen customer engagement",
    }.get(initial_focus, "balanced growth opportunity")

    return (
        f"{signals} signals a {persona} customer base in the {vertical} vertical. "
        f"Maturity score of {maturity_score} reflects "
        f"{'an established' if maturity_score >= 60 else 'a developing'} store "
        f"with {focus_explanation}."
    )
