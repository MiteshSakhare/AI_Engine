"""
Benchmark Engine — Explainer v2.

Generates gap flags and an Ollama-powered health narrative.

Upgrades v2:
  - Fixed silent skip when peer_median == 0 (now reports "unavailable")
  - Added generate_health_summary() — full Ollama narrative paragraph
    describing the merchant's cluster standing and top 3 gaps.

File: backend/engines/benchmark/explainer.py
"""

from __future__ import annotations

import logging
from typing import Dict, List

from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.benchmark.explainer")


async def generate_gap_flags(
    merchant_kpis: Dict[str, float],
    peer_medians: Dict[str, float],
    threshold_pct: float = 10.0,
) -> List[str]:
    """
    Identify KPIs where the merchant deviates significantly from the peer median.

    Returns human-readable flag strings.
    """
    flags: List[str] = []

    for metric, merchant_val in merchant_kpis.items():
        median_val = peer_medians.get(metric)

        # v2 fix: was silently skipping metrics with median=0
        if median_val is None:
            flags.append(f"{_format_metric(metric)}: peer benchmark unavailable")
            continue
        if median_val == 0:
            # Can't compute % gap; report absolute difference if meaningful
            if merchant_val > 0.001:
                flags.append(
                    f"{_format_metric(metric)} is non-zero ({merchant_val:.3f}) "
                    f"but peer median is 0 — review data quality"
                )
            continue

        is_negative = "abandonment" in metric or "churn" in metric or "bounce" in metric

        if is_negative:
            # Higher is worse for negative metrics
            diff = merchant_val - median_val
            if diff > 0.01:
                pct = round(diff / median_val * 100, 1)
                flags.append(
                    f"{_format_metric(metric)} is {pct}% above peer median "
                    f"({_fmt(median_val, metric)})"
                )
        else:
            # Lower is worse for positive metrics
            diff = median_val - merchant_val
            if diff > 0 and (diff / median_val * 100) > threshold_pct:
                pct = round(diff / median_val * 100, 1)
                flags.append(
                    f"{_format_metric(metric)} is {pct}% below peer median "
                    f"({_fmt(median_val, metric)})"
                )

    return flags


async def generate_health_summary(
    gap_flags: List[str],
    health_score: int,
    peer_cluster_id: str,
    funnel_scores: Dict[str, int],
    missing_metrics: List[str] | None = None,
) -> str:
    """
    Generate an Ollama-powered narrative summary of the benchmark analysis.

    Falls back to a deterministic summary when Ollama is unavailable.
    """
    # Build deterministic base
    funnel_text = ", ".join(
        f"{k.capitalize()}: {v}/100" for k, v in funnel_scores.items()
    )
    base = (
        f"Health score: {health_score}/100 (vs {peer_cluster_id} peers). "
        f"Funnel breakdown — {funnel_text}. "
    )

    if gap_flags:
        base += f"Top gaps: {'; '.join(gap_flags[:3])}. "
    else:
        base += "No critical gaps identified vs peer group. "

    if missing_metrics:
        base += (
            f"Note: {len(missing_metrics)} metric(s) had no data submitted "
            f"({', '.join(missing_metrics[:3])}) and were scored as neutral."
        )

    # Enrich with Ollama
    enhanced = await ollama_client.enhance_reasoning(
        engine_name="Benchmark Engine",
        heuristic_reasoning=base,
        context={
            "health_score": health_score,
            "peer_cluster": peer_cluster_id,
            "gap_count": len(gap_flags),
            "weakest_funnel": min(funnel_scores, key=funnel_scores.get) if funnel_scores else "unknown",
        },
    )
    return enhanced


def _fmt(val: float, metric: str) -> str:
    """Format peer median value for display."""
    if val < 1.0 and ("rate" in metric or "pct" in metric or "cvr" in metric):
        return f"{round(val * 100, 1)}%"
    if val >= 100:
        return f"${val:,.0f}" if "ltv" in metric or "revenue" in metric else f"{val:.0f}"
    return f"{val:.2f}"


def _format_metric(name: str) -> str:
    """Convert snake_case metric name to human-readable label."""
    return name.replace("_", " ").replace("avg", "average").replace("cvr", "CVR").title()
