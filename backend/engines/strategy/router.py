"""
Strategy Engine — FastAPI router.

POST /engine/v1/strategy/generate

File: backend/engines/strategy/router.py
"""

import logging

from fastapi import APIRouter, HTTPException

from engines.strategy.schemas import StrategyRequest, StrategyResponse
from engines.strategy.service import strategy_service

logger = logging.getLogger("bravola.strategy.router")

router = APIRouter()


@router.post(
    "/strategy/generate",
    response_model=StrategyResponse,
    summary="Generate ranked marketing strategies",
    description=(
        "The core 'Growth Marketer's Brain'. Combines domain expertise "
        "(Excel rule frameworks) with ML ranking to produce prioritised, "
        "actionable strategies."
    ),
)
async def strategy_generate(request: StrategyRequest) -> StrategyResponse:
    """
    Run the Strategy Engine pipeline:
    1. Load active rules
    2. Evaluate conditions against features & gaps
    3. Filter duplicates of active Klaviyo flows
    4. Compute strategy_score per candidate
    5. Run LTR model for model_lift_score
    6. Sort by score → assign priority_rank
    7. Generate reasoning text per strategy
    8. Return top N strategies
    """
    try:
        result = await strategy_service.generate(request)
        logger.info(
            "Strategy generation complete for %s: %d strategies",
            request.merchant_id,
            result.total_triggered,
        )
        return result
    except Exception as exc:
        logger.exception("Strategy engine failed for merchant %s", request.merchant_id)
        raise HTTPException(status_code=503, detail=f"Strategy engine error: {exc}")
