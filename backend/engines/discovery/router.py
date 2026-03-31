"""
Discovery Engine — FastAPI router.

POST /engine/v1/discovery/profile

File: backend/engines/discovery/router.py
"""

import logging

from fastapi import APIRouter, HTTPException

from engines.discovery.schemas import DiscoveryRequest, DiscoveryResponse
from engines.discovery.service import discovery_service

logger = logging.getLogger("bravola.discovery.router")

router = APIRouter()


@router.post(
    "/discovery/profile",
    response_model=DiscoveryResponse,
    summary="Profile a merchant — persona, vertical, maturity",
    description=(
        "Runs once per merchant at onboarding completion. "
        "Returns structured merchant profile used by all downstream engines."
    ),
)
async def discovery_profile(request: DiscoveryRequest) -> DiscoveryResponse:
    """
    Run the Discovery Engine pipeline:
    1. Load features (Feast or request body)
    2. Run Persona classifier (XGBoost)
    3. Run Maturity scorer (Logistic Regression)
    4. Run Vertical classifier (Random Forest)
    5. Determine initial_focus
    6. Generate reasoning text (SHAP)
    7. Return structured response
    """
    try:
        result = await discovery_service.profile(request)
        logger.info(
            "Discovery complete for %s: persona=%s vertical=%s maturity=%d",
            request.merchant_id,
            result.persona,
            result.vertical,
            result.maturity_score,
        )
        return result
    except Exception as exc:
        logger.exception("Discovery engine failed for merchant %s", request.merchant_id)
        raise HTTPException(status_code=503, detail=f"Discovery engine error: {exc}")
