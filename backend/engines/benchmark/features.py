"""
Benchmark Engine — Feature extraction.

File: backend/engines/benchmark/features.py
"""

import logging
from typing import Dict, List

from .schemas import KPIMetrics

logger = logging.getLogger("bravola.benchmark.features")

KPI_NAMES: List[str] = [
    "repeat_purchase_rate",
    "open_rate_avg",
    "click_rate_avg",
    "conversion_rate_avg",
    "revenue_per_email",
    "customer_ltv",
    "cart_abandonment_rate",
    "new_customer_rate",
    "refund_rate",
    "social_engagement_score",
    "customer_acquisition_cost",
    "referral_rate",
    "onsite_time_avg",
    "bounce_rate_avg",
    "product_review_rate",
    "spam_complaint_rate",
    "click_to_open_rate",
    "sms_optin_rate",
    "opt_in_rate",
]


def kpi_to_dict(kpi: KPIMetrics) -> Dict[str, float]:
    """Convert KPI metrics to dict."""
    return kpi.model_dump()


def kpi_to_array(kpi: KPIMetrics) -> List[float]:
    """Convert KPI metrics to ordered array for clustering."""
    d = kpi.model_dump()
    return [float(d.get(name, 0)) for name in KPI_NAMES]
