"""
Benchmark Engine — Service (orchestrator) v2.

Upgrades:
  - Uses scipy Beta CDF for a statistically-grounded peer percentile
  - Calls generate_health_summary() for an Ollama-powered narrative
  - Passes missing_metrics from health_score computation to response
  - Fixed datetime.utcnow() → datetime.now(timezone.utc)

File: backend/engines/benchmark/service.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from engines.benchmark.schemas import (
    BenchmarkRequest, BenchmarkResponse, FunnelScores,
)
from engines.benchmark.features import kpi_to_dict, kpi_to_array
from engines.benchmark.models.clustering import PeerClustering
from engines.benchmark.models.kpi_scorer import KPIScorer
from engines.benchmark.health_score import compute_health_score
from engines.benchmark.explainer import generate_gap_flags, generate_health_summary
from shared.config import settings
from shared.model_registry import model_registry

logger = logging.getLogger("bravola.benchmark.service")


class BenchmarkService:
    """Orchestrates the Benchmark Engine pipeline."""

    def __init__(self) -> None:
        cluster_model = model_registry.load_model("benchmark.cluster")
        kpi_model     = model_registry.load_model("benchmark.kpi_scorer")

        self.clustering = PeerClustering(model=cluster_model)
        self.kpi_scorer = KPIScorer(model=kpi_model)

    async def report(self, request: BenchmarkRequest) -> BenchmarkResponse:
        """
        Full benchmark pipeline:
        1. Assign peer cluster
        2. Fetch cluster medians + std devs
        3. Compute health score (Winsorized Z-score, null-safe)
        4. Generate gap flags
        5. Compute peer percentile (Beta CDF)
        6. Generate Ollama health narrative
        7. Return structured response
        """

        logger.info("Running benchmark for merchant %s", request.merchant_id)

        merchant_kpis = kpi_to_dict(request.kpi_metrics)
        kpi_array     = kpi_to_array(request.kpi_metrics)

        # ── 1. Peer cluster ──────────────────────────────
        cluster_id = self.clustering.assign_cluster(
            features=kpi_array,
            vertical=request.context.vertical,
            maturity_score=request.context.maturity_score,
            region=request.context.region,
        )

        # ── 2. Cluster medians + std devs ────────────────
        peer_medians = self.clustering.get_cluster_medians(cluster_id)
        peer_stds    = self.clustering.get_cluster_std_devs(cluster_id)

        # ── 3. Health score + funnel ─────────────────────
        scores = compute_health_score(merchant_kpis, peer_medians, peer_stds)
        missing_metrics: list[str] = scores.get("missing_metrics", [])

        # ── 4. Gap flags ─────────────────────────────────
        gap_flags = await generate_gap_flags(merchant_kpis, peer_medians)

        # ── 5. Peer percentile (Beta CDF) ────────────────
        peer_percentile = self._estimate_percentile_beta(scores["health_score"])

        # ── 6. Health narrative (Ollama) ─────────────────
        funnel_dict = {
            "acquisition": scores["acquisition_score"],
            "conversion":  scores["conversion_score"],
            "retention":   scores["retention_score"],
        }
        health_summary = await generate_health_summary(
            gap_flags=gap_flags,
            health_score=scores["health_score"],
            peer_cluster_id=cluster_id,
            funnel_scores=funnel_dict,
            missing_metrics=missing_metrics,
        )

        # ── 7. Response ──────────────────────────────────
        return BenchmarkResponse(
            merchant_id=request.merchant_id,
            health_score=scores["health_score"],
            funnel_scores=FunnelScores(
                acquisition=scores["acquisition_score"],
                conversion=scores["conversion_score"],
                retention=scores["retention_score"],
            ),
            peer_percentile=peer_percentile,
            percentile_method="sigmoid_z_beta",
            peer_cluster_id=cluster_id,
            gap_flags=gap_flags,
            missing_metrics=missing_metrics,
            health_summary=health_summary,
            kpi_snapshot=merchant_kpis,
            model_version=f"benchmark-{settings.MODEL_VERSION}",
            generated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _estimate_percentile_beta(health_score: int) -> int:
        """
        Estimate peer percentile using a Beta CDF.

        A Beta(2, 2) distribution models the expected distribution of
        health scores in a peer group — slightly bell-shaped, centred at 50.
        This gives a more accurate percentile than a simple linear mapping,
        especially at the tails (very low or very high health scores).

        Returns an integer in [1, 99].
        """
        try:
            from scipy.stats import beta  # type: ignore[import]
            percentile = beta.cdf(health_score / 100.0, a=2, b=2) * 100
            return max(1, min(99, int(round(percentile))))
        except ImportError:
            # scipy not installed: graceful linear fallback
            logger.debug("scipy unavailable; using linear percentile fallback")
            return _linear_percentile_fallback(health_score)


def _linear_percentile_fallback(health_score: int) -> int:
    """Simple linear mapping when scipy is unavailable."""
    if health_score >= 80:
        return min(95, health_score + 5)
    elif health_score >= 50:
        return health_score - 5
    return max(5, health_score - 10)


# Singleton
benchmark_service = BenchmarkService()
