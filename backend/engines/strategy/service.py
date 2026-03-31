"""
Strategy Engine — Service (orchestrator) v2.

Major upgrades:
  - Fixed critical category routing bug: was matching "Email" in category
    string, but actual value is "email_engagement" — strategies were
    misfiled. Now uses exact category enum values.
  - Dynamic Crisis Response track: auto-generated when merchant has 3+
    critical gap flags (health score < 40 OR 3+ gap_flags).
  - Ollama personalizer: single batch call to rewrite all descriptions
    with merchant persona + vertical context.
  - UCB1 integration: uses feedback engine's exploration scores as a
    secondary ranking signal when available.
  - Ollama strategy_narrative: executive summary of the recommendation set.
  - Fixed datetime.utcnow() deprecation.
  - Budget scoring moved to scorer.py for clean separation of concerns.

File: backend/engines/strategy/service.py
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from engines.strategy.schemas import (
    StrategyRequest, StrategyResponse, StrategyItem, StrategyTracks,
)
from engines.strategy.features import extract_kpi_metrics
from engines.strategy.rules.engine import RuleEngine
from engines.strategy.models.ranker import StrategyRanker
from engines.strategy.scorer import compute_strategy_scores
from engines.strategy.explainer import generate_strategy_reasoning
from engines.strategy.personalizer import personalize_strategy_items
from shared.config import settings
from shared.model_registry import model_registry
from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.strategy.service")

# Crisis response triggers
CRISIS_GAP_THRESHOLD    = 3    # Number of gap flags to trigger crisis track
CRISIS_HEALTH_THRESHOLD = 40   # Health score below this → crisis track
MAX_ITEMS_PER_TRACK     = 5

# Category → track routing (FIXED: use exact category enum values)
_CATEGORY_TRACK_MAP = {
    "revenue":             "quick_wins",
    "email_engagement":    "quick_wins",
    "audience_growth":     "core_growth",
    "audience_engagement": "retention_rescue",
}


class StrategyService:
    """Orchestrates the Strategy Engine pipeline."""

    def __init__(self) -> None:
        ranker_model = model_registry.load_model("strategy.ranker")
        self.rule_engine = RuleEngine()
        self.ranker      = StrategyRanker(model=ranker_model)

    async def generate(self, request: StrategyRequest) -> StrategyResponse:
        """
        Full strategy pipeline:
        1. Extract KPI metrics
        2. Evaluate all rules
        3. Filter active flow duplicates
        4. Compute lift scores (LTR ranker or data-driven MVP lift)
        5. Score and rank strategies (budget-aware)
        6. De-duplicate campaigns
        7. Build strategy tracks (including dynamic Crisis Response)
        8. Personalise descriptions via Ollama (single batch call)
        9. Generate Ollama strategy_narrative
        10. Return structured response
        """

        logger.info("Generating strategies for merchant %s", request.merchant_id)

        # ── 1. KPI metrics ───────────────────────────────
        kpi_metrics = extract_kpi_metrics(request.benchmark_output)

        # ── 2. Evaluate all rules ────────────────────────
        triggered = self.rule_engine.evaluate(
            kpi_metrics=kpi_metrics,
            gap_flags=request.benchmark_output.gap_flags,
            discovery={
                "persona":       request.discovery_output.persona,
                "maturity_score": request.discovery_output.maturity_score,
                "vertical":      request.discovery_output.vertical,
            },
            active_flow_ids=request.constraints.active_flow_ids,
        )
        total_triggered = len(triggered)

        # ── 3. Filter duplicates ─────────────────────────
        filtered = self.rule_engine.filter_duplicates(
            triggered,
            request.constraints.active_flow_ids,
        )

        if not filtered:
            logger.info("No strategies triggered for merchant %s", request.merchant_id)
            return StrategyResponse(
                merchant_id=request.merchant_id,
                strategy_batch_id=str(uuid.uuid4()),
                tracks=StrategyTracks(),
                strategy_narrative="No specific strategy recommendations at this time. "
                                   "Ensure your KPI data is up to date for accurate recommendations.",
                total_triggered=0,
                tracks_populated=0,
                model_version=f"strategy-{settings.MODEL_VERSION}",
                generated_at=datetime.now(timezone.utc),
            )

        # ── 4. LTR lift scores ───────────────────────────
        rule_ids    = [r.rule_id for r in filtered]
        lift_scores = self.ranker.predict_lift_scores(rule_ids, kpi_metrics)

        # ── 5. Score and rank ────────────────────────────
        scored = compute_strategy_scores(
            triggered_rules=filtered,
            model_lift_scores=lift_scores,
            budget_tier=request.constraints.budget_tier,
        )

        # ── 6. De-duplicate campaigns ────────────────────
        seen_campaigns: set[str] = set()

        # ── 7. Build tracks ──────────────────────────────
        tracks    = StrategyTracks()
        is_crisis = (
            request.benchmark_output.health_score < CRISIS_HEALTH_THRESHOLD
            or len(request.benchmark_output.gap_flags) >= CRISIS_GAP_THRESHOLD
        )
        all_items: list[StrategyItem] = []

        for rank, (rule, rule_weighted, model_lift, penalty, score) in enumerate(scored, 1):
            if rank > TOTAL_STRATEGY_CANDIDATES:
                break

            # De-duplicate campaigns
            unique_campaigns = []
            for c in rule.campaigns:
                if c.lower() not in seen_campaigns:
                    unique_campaigns.append(c)
                    seen_campaigns.add(c.lower())

            reasoning = await generate_strategy_reasoning(
                rule=rule,
                gap_flags=request.benchmark_output.gap_flags,
                peer_cluster_id=request.benchmark_output.peer_cluster_id,
                kpi_metrics=kpi_metrics,
            )

            item = StrategyItem(
                rule_id=rule.rule_id,
                category=rule.category,
                description=rule.description,
                campaigns=unique_campaigns or rule.campaigns[:1],
                flows=rule.flows,
                qualifying_questions=rule.qualifying_questions,
                priority_rank=rank,
                confidence_score=float(f"{1.0 - penalty:.2f}"),
                reasoning=reasoning,
                rule_weighted_score=float(f"{rule_weighted:.4f}"),
                model_lift_score=float(f"{model_lift:.3f}"),
                confidence_penalty=float(f"{penalty:.3f}"),
                strategy_score=score,
                creative_notes=rule.creative_notes,
                ollama_personalized=False,
            )
            all_items.append(item)

            # ── Track routing (FIXED: exact category enum values) ────
            track_name = _CATEGORY_TRACK_MAP.get(rule.category, "retention_rescue")

            # Crisis track: route top items from weakest funnel area
            if is_crisis:
                funnel = request.benchmark_output.funnel_scores or {}
                weakest = min(funnel, key=funnel.get) if funnel else "acquisition"
                crisis_cats = {
                    "acquisition": ["audience_growth", "email_engagement"],
                    "conversion":  ["revenue", "audience_engagement"],
                    "retention":   ["revenue", "audience_engagement"],
                }.get(weakest, [])

                if rule.category in crisis_cats and len(tracks.crisis_response) < MAX_ITEMS_PER_TRACK:
                    tracks.crisis_response.append(item)
                    continue  # Don't double-file in regular tracks

            # Regular track routing
            if track_name == "quick_wins" and len(tracks.quick_wins) < MAX_ITEMS_PER_TRACK:
                tracks.quick_wins.append(item)
            elif track_name == "core_growth" and len(tracks.core_growth) < MAX_ITEMS_PER_TRACK:
                tracks.core_growth.append(item)
            elif track_name == "retention_rescue" and len(tracks.retention_rescue) < MAX_ITEMS_PER_TRACK:
                tracks.retention_rescue.append(item)

        # ── 8. Personalise descriptions (single Ollama batch) ────────
        all_items_flat = (
            tracks.quick_wins
            + tracks.core_growth
            + tracks.retention_rescue
            + tracks.crisis_response
        )
        personalised = await personalize_strategy_items(
            items=all_items_flat,
            persona=request.discovery_output.persona,
            vertical=request.discovery_output.vertical,
            maturity_score=request.discovery_output.maturity_score,
            budget_tier=request.constraints.budget_tier,
        )

        # Reassign personalised items back to tracks
        tracks = _reassign_personalised_items(personalised, tracks)

        # ── 9. Strategy narrative ────────────────────────
        strategy_narrative = await self._generate_narrative(
            request, tracks, is_crisis, total_triggered,
        )

        # ── 10. Count populated tracks ───────────────────
        tracks_populated = sum([
            1 for t in [
                tracks.quick_wins, tracks.core_growth,
                tracks.retention_rescue, tracks.crisis_response,
            ] if t
        ])

        logger.info(
            "Strategies generated for %s: QW=%d CG=%d RR=%d CR=%d narrative=%s",
            request.merchant_id,
            len(tracks.quick_wins), len(tracks.core_growth),
            len(tracks.retention_rescue), len(tracks.crisis_response),
            "yes" if strategy_narrative else "no",
        )

        return StrategyResponse(
            merchant_id=request.merchant_id,
            strategy_batch_id=str(uuid.uuid4()),
            tracks=tracks,
            strategy_narrative=strategy_narrative,
            total_triggered=total_triggered,
            tracks_populated=tracks_populated,
            model_version=f"strategy-{settings.MODEL_VERSION}",
            generated_at=datetime.now(timezone.utc),
        )

    async def _generate_narrative(
        self,
        request: StrategyRequest,
        tracks: StrategyTracks,
        is_crisis: bool,
        total_triggered: int,
    ) -> str:
        """Generate Ollama executive summary of the strategy recommendation set."""
        track_summary = (
            f"Quick wins: {len(tracks.quick_wins)}, "
            f"Core growth: {len(tracks.core_growth)}, "
            f"Retention rescue: {len(tracks.retention_rescue)}"
        )
        if tracks.crisis_response:
            track_summary += f", Crisis response: {len(tracks.crisis_response)}"

        heuristic = (
            f"{'⚠️ Crisis mode: ' if is_crisis else ''}"
            f"{total_triggered} strategies evaluated for a {request.discovery_output.vertical} "
            f"merchant with a '{request.discovery_output.persona}' customer base. "
            f"Health score: {request.benchmark_output.health_score}/100. "
            f"Strategy tracks: {track_summary}. "
            f"Primary focus: {request.discovery_output.initial_focus}."
        )

        enhanced = await ollama_client.enhance_reasoning(
            engine_name="Strategy Engine",
            heuristic_reasoning=heuristic,
            context={
                "persona":       request.discovery_output.persona,
                "vertical":      request.discovery_output.vertical,
                "health_score":  request.benchmark_output.health_score,
                "is_crisis":     is_crisis,
                "total_tracks":  4 if tracks.crisis_response else 3,
            },
        )
        return enhanced or heuristic


def _reassign_personalised_items(
    personalised: list[StrategyItem],
    original_tracks: StrategyTracks,
) -> StrategyTracks:
    """Map personalised items back to their original tracks by rule_id."""
    id_map = {item.rule_id: item for item in personalised}

    def remap(items: list[StrategyItem]) -> list[StrategyItem]:
        return [id_map.get(i.rule_id, i) for i in items]

    return StrategyTracks(
        quick_wins=remap(original_tracks.quick_wins),
        core_growth=remap(original_tracks.core_growth),
        retention_rescue=remap(original_tracks.retention_rescue),
        crisis_response=remap(original_tracks.crisis_response),
    )


# Config constant
TOTAL_STRATEGY_CANDIDATES = getattr(settings, "TOTAL_STRATEGY_CANDIDATES", 20)

# Singleton
strategy_service = StrategyService()
