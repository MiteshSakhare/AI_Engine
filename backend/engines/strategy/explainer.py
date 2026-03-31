"""
Strategy Engine — Explainer.

Per-strategy reasoning text enhanced with Ollama LLM.

File: backend/engines/strategy/explainer.py
"""

from typing import List, Dict, Any

from engines.strategy.rules.rules_registry import RuleDefinition
from shared.ollama_client import ollama_client


async def generate_strategy_reasoning(
    rule: RuleDefinition,
    gap_flags: List[str],
    peer_cluster_id: str,
    kpi_metrics: Dict[str, float] | None = None,
) -> str:
    """Generate human-readable reasoning for a single strategy, enhanced with Ollama."""
    base = _build_heuristic_reasoning(rule, gap_flags, peer_cluster_id, kpi_metrics)

    enhanced = await ollama_client.enhance_reasoning(
        engine_name="Strategy Engine",
        heuristic_reasoning=base,
        context={
            "rule_id": rule.rule_id,
            "category": rule.category,
            "metric": rule.metric,
            "campaigns": rule.campaigns[:3],
            "peer_cluster": peer_cluster_id,
        },
    )
    return enhanced


def _build_heuristic_reasoning(
    rule: RuleDefinition,
    gap_flags: List[str],
    peer_cluster_id: str,
    kpi_metrics: Dict[str, float] | None = None,
) -> str:
    """Build the base reasoning text from rule data."""
    parts = []

    # Describe the trigger condition
    value = kpi_metrics.get(rule.metric, 0) if kpi_metrics else 0
    readable_metric = rule.metric.replace("_", " ")

    if rule.threshold_operator == "lt":
        parts.append(
            f"Your {readable_metric} ({_format_value(value, rule.metric)}) "
            f"is below the threshold ({_format_value(rule.threshold_value, rule.metric)})."
        )
    elif rule.threshold_operator == "gt":
        parts.append(
            f"Your {readable_metric} ({_format_value(value, rule.metric)}) "
            f"is above the threshold ({_format_value(rule.threshold_value, rule.metric)})."
        )
    elif rule.threshold_operator == "eq":
        parts.append(f"{rule.description}.")

    # Find matching gap flag
    for flag in gap_flags:
        if rule.metric.replace("_", " ") in flag.lower():
            parts.append(f"Benchmark gap: {flag}.")
            break

    # Campaigns and flows
    if rule.campaigns:
        parts.append(f"Recommended campaigns: {', '.join(rule.campaigns[:3])}.")
    if rule.flows:
        parts.append(f"Recommended flows: {', '.join(rule.flows[:3])}.")

    # Peer context
    parts.append(
        f"Similar strategies in the {peer_cluster_id} peer group "
        f"have shown positive results."
    )

    return " ".join(parts)


def _format_value(value: Any, metric: str) -> str:
    """Format a metric value for display."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        if abs(value) < 1 and ("rate" in metric or "pct" in metric or "cvr" in metric):
            return f"{value * 100:.1f}%"
        if abs(value) > 1000:
            return f"${value:,.0f}"
        if abs(value) > 1:
            return f"{value:.1f}"
        return f"{value:.2f}"
    return str(value)
