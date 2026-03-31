"""
Feedback Engine — FastAPI router.

POST /engine/v1/feedback/process

File: backend/engines/feedback/router.py
"""

import logging

from fastapi import APIRouter, HTTPException

from engines.feedback.schemas import FeedbackRequest, FeedbackResponse
from engines.feedback.service import feedback_service

logger = logging.getLogger("bravola.feedback.router")

router = APIRouter()


@router.post(
    "/feedback/process",
    response_model=FeedbackResponse,
    summary="Process campaign feedback and adjust model weights",
    description=(
        "The learning loop. Ingests campaign performance data and human feedback, "
        "classifies outcomes, adjusts rule weights, and triggers model retraining "
        "when threshold is reached."
    ),
)
async def feedback_process(request: FeedbackRequest) -> FeedbackResponse:
    """
    Run the Feedback Engine pipeline:
    1. Classify campaign performance (success | neutral | failure)
    2. Apply human feedback override
    3. Update rule weight via learning_rate
    4. Check retrain threshold → dispatch Celery task if needed
    5. Return structured response
    """
    try:
        result = await feedback_service.process(request)
        logger.info(
            "Feedback processed for %s: label=%s retrain=%s",
            request.merchant_id,
            result.performance_label,
            result.retrain_triggered,
        )
        return result
    except Exception as exc:
        logger.exception("Feedback engine failed for merchant %s", request.merchant_id)
        raise HTTPException(status_code=503, detail=f"Feedback engine error: {exc}")
