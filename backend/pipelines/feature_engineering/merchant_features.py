"""
Merchant Feature Engineering Pipeline.

PostgreSQL → feature computation → Feast / in-memory store.

File: backend/pipelines/feature_engineering/merchant_features.py
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("bravola.pipelines.merchant_features")


def compute_merchant_features(
    orders: List[Dict[str, Any]],
    customers: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Compute merchant-level features from raw transactional data.

    Input: raw orders, customers, products from PostgreSQL.
    Output: feature dict ready for Feast materialisation.
    """

    if not orders:
        return _empty_features()

    # ── Revenue features ─────────────────────────────
    total_revenue = sum(o.get("total_amount", 0) for o in orders)
    order_count = len(orders)
    avg_order_value = total_revenue / max(order_count, 1)

    # 90-day and 30-day revenue (simplified — production uses proper date filtering)
    revenue_last_90d = total_revenue * 0.75  # Simplified
    revenue_last_30d = total_revenue * 0.30

    # ── Customer features ────────────────────────────
    total_customer_count = len(customers)
    customers_with_orders = set(o.get("customer_id") for o in orders if o.get("customer_id"))
    repeat_customers = set()

    customer_order_counts: Dict[str, int] = {}
    for o in orders:
        cid = o.get("customer_id")
        if cid:
            customer_order_counts[cid] = customer_order_counts.get(cid, 0) + 1
            if customer_order_counts[cid] > 1:
                repeat_customers.add(cid)

    repeat_rate = len(repeat_customers) / max(len(customers_with_orders), 1)

    # ── Product features ─────────────────────────────
    product_count = len(products)
    if product_count > 0:
        # Product concentration: how much of revenue comes from top 3 products
        product_revenue: Dict[str, float] = {}
        for o in orders:
            pid = o.get("product_id", "unknown")
            product_revenue[pid] = product_revenue.get(pid, 0) + o.get("total_amount", 0)

        sorted_products = sorted(product_revenue.values(), reverse=True)
        top_3_revenue = sum(sorted_products[:3])
        product_concentration = top_3_revenue / max(total_revenue, 1)
    else:
        product_concentration = 0.5

    # ── Engagement features ──────────────────────────
    # Simplified — in production, these come from Klaviyo API or engagement tables
    email_engagement_score = 0.25  # Default median

    # ── Days to second purchase ──────────────────────
    days_to_second_purchase = 30.0  # Simplified default

    return {
        "avg_order_value": round(avg_order_value, 2),
        "repeat_rate": round(repeat_rate, 4),
        "days_to_second_purchase": round(days_to_second_purchase, 1),
        "product_concentration": round(product_concentration, 4),
        "email_engagement_score": round(email_engagement_score, 4),
        "total_customer_count": total_customer_count,
        "revenue_last_90d": round(revenue_last_90d, 2),
        "revenue_last_30d": round(revenue_last_30d, 2),
    }


def _empty_features() -> Dict[str, float]:
    """Return empty feature dict for new merchants."""
    return {
        "avg_order_value": 0.0,
        "repeat_rate": 0.0,
        "days_to_second_purchase": 0.0,
        "product_concentration": 0.0,
        "email_engagement_score": 0.0,
        "total_customer_count": 0,
        "revenue_last_90d": 0.0,
        "revenue_last_30d": 0.0,
    }
