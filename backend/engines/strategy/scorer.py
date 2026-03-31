"""
Strategy Scorer — Hybrid scoring with category weights v2.

strategy_score = (global_weight × W_rule)
               + (model_lift_score × W_model)
               - (confidence_penalty × W_penalty)

Upgrades v2:
  - Data-driven MVP lift estimate: replaces hardcoded 0.5 for all rules.
    In MVP mode (no ranker model), lift is computed from rule weights:
      lift = 0.3 + (global_weight * 0.5) + (normalised_weight * 0.2)
    This ensures differentiation even without a trained model.
  - Budget-aware scoring: low budget penalises audience_growth rules,
    high budget boosts revenue rules.
  - Multi-key sort: ties broken by base_weight > rule_id (deterministic).

File: backend/engines/strategy/scorer.py
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from engines.strategy.rules.rules_registry import RuleDefinition
from shared.config import settings

logger = logging.getLogger("bravola.strategy.scorer")


def compute_strategy_scores(
    triggered_rules: List[RuleDefinition],
    model_lift_scores: Optional[dict] = None,
    confidence_scores: Optional[dict] = None,
    budget_tier: str = "mid",
) -> List[Tuple[RuleDefinition, float, float, float, float]]:
    """
    Compute strategy_score for each triggered rule.

    Returns list of (rule, rule_weighted_score, model_lift, penalty, final_score)
    sorted by final_score descending, then base_weight descending as tie-breaker.
    """
    w_rule    = settings.W_RULE
    w_model   = settings.W_MODEL
    w_penalty = settings.W_PENALTY

    scored: List[Tuple[RuleDefinition, float, float, float, float]] = []

    for rule in triggered_rules:
        rule_weighted = rule.global_weight

        # ── Model lift ───────────────────────────────────
        if model_lift_scores and rule.rule_id in model_lift_scores:
            model_lift = model_lift_scores[rule.rule_id]
        else:
            # Data-driven MVP lift: derived from rule weight signals
            # Ensures every rule has a unique, meaningful lift score
            model_lift = min(0.95, 0.30 + (rule.global_weight * 0.50) + (rule.normalised_weight * 0.20))

        # ── Confidence penalty ───────────────────────────
        confidence = 0.85
        if confidence_scores and rule.rule_id in confidence_scores:
            confidence = confidence_scores[rule.rule_id]
        penalty = max(0, (1.0 - confidence) * 0.5)

        # ── Raw strategy score ───────────────────────────
        strategy_score = (
            (rule_weighted * w_rule)
            + (model_lift * w_model)
            - (penalty * w_penalty)
        )

        # ── Budget-aware adjustments ─────────────────────
        if budget_tier == "low":
            if rule.category == "audience_growth":
                # High-effort growth campaigns are harder on tight budgets
                strategy_score *= 0.75
            elif rule.category in ("revenue", "email_engagement"):
                # Email-centric wins are budget-friendly
                strategy_score *= 1.05

        elif budget_tier == "high":
            if rule.category == "revenue":
                # Full budget unlocks aggressive revenue campaigns
                strategy_score *= 1.10
            elif rule.category == "audience_growth":
                strategy_score *= 1.05

        scored.append((rule, rule_weighted, model_lift, penalty, round(strategy_score, 4)))

    # Primary: final_score DESC | Secondary: base_weight DESC | Tertiary: rule_id ASC
    scored.sort(key=lambda x: (-x[4], -x[0].base_weight, x[0].rule_id))

    return scored
