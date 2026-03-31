"""
Benchmark Engine — FastAPI router.

POST /engine/v1/benchmark/report

File: backend/engines/benchmark/router.py
"""

import logging

from fastapi import APIRouter, HTTPException

from engines.benchmark.schemas import BenchmarkRequest, BenchmarkResponse
from engines.benchmark.service import benchmark_service

logger = logging.getLogger("bravola.benchmark.router")

router = APIRouter()


@router.post(
    "/benchmark/report",
    response_model=BenchmarkResponse,
    summary="Benchmark merchant vs peer group",
    description=(
        "Runs weekly per merchant. Compares KPIs against a peer group cluster "
        "and returns health score, funnel scores, gap flags, and peer percentile."
    ),
)
async def benchmark_report(request: BenchmarkRequest) -> BenchmarkResponse:
    """
    Run the Benchmark Engine pipeline:
    1. Assign merchant to peer cluster (K-Means)
    2. Fetch peer cluster medians
    3. Compute KPI gaps
    4. Compute health_score via weighted formula
    5. Identify gap_flags
    6. Compute peer_percentile
    7. Return structured report
    """
    try:
        result = await benchmark_service.report(request)
        logger.info(
            "Benchmark complete for %s: health=%d cluster=%s",
            request.merchant_id,
            result.health_score,
            result.peer_cluster_id,
        )
        return result
    except Exception as exc:
        logger.exception("Benchmark engine failed for merchant %s", request.merchant_id)
        raise HTTPException(status_code=503, detail=f"Benchmark engine error: {exc}")
