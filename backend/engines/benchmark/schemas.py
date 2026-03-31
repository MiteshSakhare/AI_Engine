"""
Benchmark Engine — Pydantic Request/Response schemas.

POST /engine/v1/benchmark/report

File: backend/engines/benchmark/schemas.py
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


ENGINE_CONFIG = ConfigDict(
    from_attributes=True,
    protected_namespaces=(),
    extra="forbid",
)


# ── Request ──────────────────────────────────────────

class KPIMetrics(BaseModel):
    """Merchant KPI metrics for benchmarking."""

    repeat_purchase_rate: float = 0.0
    open_rate_avg: float = 0.0
    click_rate_avg: float = 0.0
    conversion_rate_avg: float = 0.0
    revenue_per_email: float = 0.0
    customer_ltv: float = 0.0
    cart_abandonment_rate: float = 0.0
    new_customer_rate: float = 0.0
    refund_rate: float = 0.0
    social_engagement_score: float = 0.0
    customer_acquisition_cost: float = 0.0
    referral_rate: float = 0.0
    onsite_time_avg: float = 0.0
    bounce_rate_avg: float = 0.0
    product_review_rate: float = 0.0
    spam_complaint_rate: float = 0.0
    click_to_open_rate: float = 0.0
    sms_optin_rate: float = 0.0
    opt_in_rate: float = 0.0          # list growth / email sign-up rate

    model_config = ENGINE_CONFIG


class BenchmarkContext(BaseModel):
    """Discovery output context for peer grouping."""

    vertical: str = "other"
    maturity_score: int = 50
    region: str = "US"

    model_config = ENGINE_CONFIG


class BenchmarkRequest(BaseModel):
    """POST /engine/v1/benchmark/report — Request body."""

    merchant_id: str
    kpi_metrics: KPIMetrics
    context: BenchmarkContext

    model_config = ENGINE_CONFIG


# ── Response ─────────────────────────────────────────

class FunnelScores(BaseModel):
    """Sub-scores for each funnel stage."""

    acquisition: int = Field(ge=0, le=100)
    conversion: int = Field(ge=0, le=100)
    retention: int = Field(ge=0, le=100)

    model_config = ENGINE_CONFIG


class BenchmarkResponse(BaseModel):
    """Structured benchmark report returned to Node.js team."""

    merchant_id: str
    health_score: int = Field(ge=0, le=100)
    funnel_scores: FunnelScores
    peer_percentile: int = Field(ge=0, le=100)
    percentile_method: str = "sigmoid_z_beta"  # documents how percentile was derived
    peer_cluster_id: str
    gap_flags: List[str]
    missing_metrics: List[str] = []            # metrics substituted with peer mean
    health_summary: str = ""                   # Ollama-generated narrative
    kpi_snapshot: Dict[str, float]
    model_version: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ENGINE_CONFIG
