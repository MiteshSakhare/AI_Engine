"""
Discovery Engine — Feature extraction.

Fetches feature vector from Feast online store
or uses the feature_vector from the request if provided.

File: backend/engines/discovery/features.py
"""

import logging
from typing import Dict, Any, Optional, List

from engines.discovery.schemas import FeatureVector
from shared.feature_store import feature_store_client

logger = logging.getLogger("bravola.discovery.features")

# Canonical feature order for model input
FEATURE_NAMES: List[str] = [
    "avg_order_value",
    "aov_variance",
    "repeat_rate",
    "purchase_frequency_variance",
    "days_to_second_purchase",
    "product_concentration",
    "catalog_size",
    "email_engagement_score",
    "total_customer_count",
    "revenue_last_90d",
    "revenue_last_30d",
]


def get_feature_vector(
    merchant_id: str,
    request_features: Optional[FeatureVector] = None,
) -> Dict[str, Any]:
    """
    Return a dict of features for model inference.

    Priority:
    1. Feast online store (if available)
    2. feature_vector from the API request
    3. Zeros fallback
    """

    # Try Feast first
    feast_features = feature_store_client.get_features(merchant_id)
    if feast_features:
        logger.info("Using Feast features for merchant %s", merchant_id)
        return feast_features

    # Fall back to request payload
    if request_features:
        logger.info("Using request feature_vector for merchant %s", merchant_id)
        return request_features.model_dump()

    # Ultimate fallback
    logger.warning("No features available for merchant %s — using zeros", merchant_id)
    return {name: 0 for name in FEATURE_NAMES}


def features_to_array(features: Dict[str, Any]) -> List[float]:
    """Convert feature dict to ordered float array for model input."""
    return [float(features.get(name, 0)) for name in FEATURE_NAMES]
