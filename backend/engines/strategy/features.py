"""
Strategy Engine — Feature extraction.

Builds a flat KPI dict matching all 19 metrics required by the 29 rules.

File: backend/engines/strategy/features.py
"""

import logging
from typing import Dict, Any

from engines.strategy.schemas import BenchmarkOutput

logger = logging.getLogger("bravola.strategy.features")


def extract_kpi_metrics(benchmark_output: BenchmarkOutput) -> Dict[str, Any]:
    """
    Build a flat KPI dict from benchmark output for rule evaluation.

    In production, this would query Feast for real-time merchant metrics.
    Here we derive approximate values from funnel scores.
    """
    funnel = benchmark_output.funnel_scores

    acquisition_score = funnel.get("acquisition", 50)
    conversion_score = funnel.get("conversion", 50)
    retention_score = funnel.get("retention", 50)

    # Map funnel scores to approximate metric values
    kpis: Dict[str, Any] = {
        # Revenue metrics
        "repeat_customer_rate": retention_score / 100 * 0.40,
        "top_product_margin": 0.50,
        "discount_usage_rate": 0.20,
        "inventory_overstock_flag": False,
        "revenue_per_recipient": conversion_score / 100 * 0.40,
        "aov_mom_change": 0.0,
        "revenue_yoy_change": 0.0,
        "ltv_yoy_change": 0.0,

        # Engagement metrics
        "click_rate_avg": acquisition_score / 100 * 0.02,
        "website_cvr": conversion_score / 100 * 0.03,
        "unsubscribe_rate": 0.005,
        "monthly_churn_rate": max(0, 1.0 - retention_score / 100) * 0.20,
        "reengagement_rate": retention_score / 100 * 0.20,
        "engagement_rate": acquisition_score / 100 * 0.30,

        # Audience growth metrics
        "opt_in_rate": acquisition_score / 100 * 0.08,
        "attributed_revenue_pct": conversion_score / 100 * 0.50,
        "vip_pct_of_list": retention_score / 100 * 0.08,

        # Email engagement metrics
        "open_rate_avg": acquisition_score / 100 * 0.50,
        "deliverability_rate": 0.95,
    }

    return kpis
