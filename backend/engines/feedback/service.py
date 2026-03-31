"""
Feedback Engine — Service (orchestrator) v2.

Upgrades:
  - Passes cluster_id from merchant_context to classify_performance()
  - Retrieves UCB1 score + exploration_bonus from update_weight()
  - Includes ucb1/exploration data in WeightUpdate response objects
  - Generates a brief Ollama feedback_summary for merchant-facing insights
  - Fixed datetime.utcnow() deprecation

File: backend/engines/feedback/service.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from engines.feedback.schemas import (
    FeedbackRequest, FeedbackResponse, WeightUpdate,
)
from engines.feedback.classifier import classify_performance
from engines.feedback.weight_updater import update_weight, get_ucb1_score, _plays
from engines.feedback.retrain_trigger import (
    increment_event_count,
    should_retrain,
    dispatch_retrain,
)
from shared.config import settings
from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.feedback.service")


class FeedbackService:
    """Orchestrates the Feedback Engine pipeline."""

    async def process(self, request: FeedbackRequest) -> FeedbackResponse:
        """
        Full feedback pipeline:
        1. Classify campaign performance (cluster-aware baselines)
        2. Apply human feedback override
        3. Update rule weight (UCB1)
        4. Check retrain threshold
        5. Generate Ollama feedback summary
        6. Return structured response
        """

        logger.info(
            "Processing feedback for merchant %s, strategy %s",
            request.merchant_id,
            request.strategy_id_code,
        )

        # ── 1. Classify performance ──────────────────────
        cluster_id = (
            request.merchant_context.cluster_id
            if request.merchant_context else None
        )
        performance_label = classify_performance(
            request.campaign_metrics,
            cluster_id=cluster_id,
        )

        # ── 2. Human feedback override ───────────────────
        if request.human_feedback:
            performance_label = self._apply_human_feedback(
                performance_label,
                request.human_feedback.action,
            )

        # ── 3. Update rule weight (UCB1) ─────────────────
        old_weight, new_weight, adjustment, ucb1_score, exploration_bonus = update_weight(
            rule_id=request.triggered_rule_id,
            performance_label=performance_label,
        )

        total_plays = _plays.get(request.triggered_rule_id, 0)

        weight_updates = [
            WeightUpdate(
                rule_id=request.triggered_rule_id,
                old_weight=float(f"{old_weight:.3f}"),
                new_weight=float(f"{new_weight:.3f}"),
                adjustment=float(f"{adjustment:.4f}"),
                ucb1_score=float(f"{ucb1_score:.4f}"),
                exploration_bonus=float(f"{exploration_bonus:.4f}"),
                total_rule_plays=total_plays,
            )
        ]

        # ── 4. Retrain check ─────────────────────────────
        event_count = increment_event_count("strategy")
        retrain_triggered = False

        if should_retrain("strategy"):
            retrain_triggered = dispatch_retrain("strategy")

        # ── 5. Feedback summary (Ollama) ─────────────────
        feedback_summary = await self._generate_feedback_summary(
            rule_id=request.triggered_rule_id,
            strategy_code=request.strategy_id_code,
            performance_label=performance_label,
            old_weight=old_weight,
            new_weight=new_weight,
            ucb1_score=ucb1_score,
        )

        logger.info(
            "Feedback processed: strategy=%s label=%s weight=%.3f→%.3f "
            "ucb1=%.4f events=%d retrain=%s",
            request.strategy_id_code,
            performance_label,
            old_weight,
            new_weight,
            ucb1_score,
            event_count,
            retrain_triggered,
        )

        return FeedbackResponse(
            merchant_id=request.merchant_id,
            strategy_id_code=request.strategy_id_code,
            performance_label=performance_label,
            weight_updates=weight_updates,
            retrain_triggered=retrain_triggered,
            feedback_event_count=event_count,
            feedback_summary=feedback_summary,
            model_version=f"feedback-{settings.MODEL_VERSION}",
            generated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _apply_human_feedback(auto_label: str, human_action: str) -> str:
        """
        Human feedback overrides the automated classification.

        approved  → success
        rejected  → failure
        modified  → neutral (partial success; strategy needed adjustment)
        """
        overrides = {
            "approved": "success",
            "rejected": "failure",
            "modified": "neutral",
        }
        return overrides.get(human_action, auto_label)

    @staticmethod
    async def _generate_feedback_summary(
        rule_id: str,
        strategy_code: str,
        performance_label: str,
        old_weight: float,
        new_weight: float,
        ucb1_score: float,
    ) -> str:
        """Generate a brief Ollama insight on the feedback outcome."""
        label_descriptions = {
            "success": "exceeded expectations",
            "neutral": "performed within expectations but didn't stand out",
            "failure": "underperformed — the strategy did not hit its targets",
        }
        heuristic = (
            f"Strategy {strategy_code} (rule {rule_id}) {label_descriptions.get(performance_label, performance_label)}. "
            f"Weight adjusted from {old_weight:.2f} to {new_weight:.2f}. "
            f"UCB1 exploration score: {ucb1_score:.3f} — "
            f"{'high exploration potential' if ucb1_score > 1.5 else 'exploitation-focused recommendation'}."
        )
        enhanced = await ollama_client.enhance_reasoning(
            engine_name="Feedback Engine",
            heuristic_reasoning=heuristic,
            context={
                "rule_id": rule_id,
                "performance": performance_label,
                "weight_delta": round(new_weight - old_weight, 3),
                "ucb1_score": round(ucb1_score, 3),
            },
        )
        return enhanced or heuristic


# Singleton
feedback_service = FeedbackService()
