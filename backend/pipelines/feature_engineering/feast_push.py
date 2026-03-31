"""
Feast Push — Materialise computed features to the online store.

File: backend/pipelines/feature_engineering/feast_push.py
"""

import logging
from typing import Dict, Any

from shared.config import settings

logger = logging.getLogger("bravola.pipelines.feast_push")


def push_features_to_feast(
    merchant_id: str,
    features: Dict[str, Any],
) -> bool:
    """
    Push computed features to Feast online store.

    Returns True if push succeeded.
    """
    if not settings.FEAST_REPO_PATH:
        logger.info("Feast not configured — features stored in-memory only")
        return False

    try:
        from feast import FeatureStore
        import pandas as pd
        from datetime import datetime

        store = FeatureStore(repo_path=settings.FEAST_REPO_PATH)

        df = pd.DataFrame([{
            "merchant_id": merchant_id,
            "event_timestamp": datetime.utcnow(),
            **features,
        }])

        store.push("merchant_features_push_source", df)
        logger.info("Features pushed to Feast for merchant %s", merchant_id)
        return True

    except Exception as exc:
        logger.warning("Feast push failed for merchant %s: %s", merchant_id, exc)
        return False
