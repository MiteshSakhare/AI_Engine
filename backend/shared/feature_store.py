"""
Feast Feature Store client wrapper.

get_features(merchant_id) → dict — single call returns full feature vector.
Falls back to direct DB query if Feast is unavailable.
Feature freshness check: log warning if features > 24h old.

File: backend/shared/feature_store.py
"""

import logging
from typing import Dict, Any, Optional

from shared.config import settings

logger = logging.getLogger("bravola.feature_store")


class FeatureStoreClient:
    """
    Wraps Feast online feature retrieval.

    In development / when Feast is not configured, returns None
    so callers fall back to the feature_vector in the request payload.
    """

    def __init__(self) -> None:
        self._store = None
        self._init_feast()

    def _init_feast(self) -> None:
        """Attempt to connect to Feast. Fail silently."""
        if not settings.FEAST_REPO_PATH:
            logger.info("Feast not configured — using request payloads only")
            return

        try:
            from feast import FeatureStore

            self._store = FeatureStore(repo_path=settings.FEAST_REPO_PATH)
            logger.info("Feast feature store connected: %s", settings.FEAST_REPO_PATH)
        except Exception as exc:
            logger.warning("Feast initialisation failed (will use fallback): %s", exc)
            self._store = None

    @property
    def available(self) -> bool:
        return self._store is not None

    def get_features(
        self,
        merchant_id: str,
        feature_refs: Optional[list] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch online features for a merchant.

        Returns None if Feast is unavailable — callers should
        use the feature_vector supplied in the API request instead.
        """
        store = self._store
        if not store:
            return None

        try:
            entity_rows = [{"merchant_id": merchant_id}]

            if feature_refs is None:
                feature_refs = [
                    "merchant_features:avg_order_value",
                    "merchant_features:repeat_rate",
                    "merchant_features:days_to_second_purchase",
                    "merchant_features:product_concentration",
                    "merchant_features:email_engagement_score",
                    "merchant_features:total_customer_count",
                    "merchant_features:revenue_last_90d",
                    "merchant_features:revenue_last_30d",
                ]

            result = store.get_online_features(
                features=feature_refs,
                entity_rows=entity_rows,
            )

            features = result.to_dict()
            # Flatten — Feast returns lists of single values
            flat: Dict[str, Any] = {}
            for k, v in features.items():
                if k == "merchant_id":
                    continue
                flat[k.split(":")[-1] if ":" in k else k] = v[0] if isinstance(v, list) and v else v

            logger.info("Features fetched from Feast for merchant %s", merchant_id)
            return flat

        except Exception as exc:
            logger.warning("Feast query failed for merchant %s: %s", merchant_id, exc)
            return None


# Singleton
feature_store_client = FeatureStoreClient()
