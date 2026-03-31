"""
Discovery Engine — Pydantic Request/Response schemas v2.

Upgrades:
  - DiscoveryResponse: added target_audience, price_point_tier,
    key_value_proposition, growth_signals, dominant_channel,
    churn_risk_level — the full merchant profile.
  - OnboardingResponses: added price_hint, audience_hint, primary_challenge.
  - Fixed datetime.utcnow() deprecation.

POST /engine/v1/discovery/profile

File: backend/engines/discovery/schemas.py
"""

from datetime import datetime, timezone
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


ENGINE_CONFIG = ConfigDict(
    from_attributes=True,
    protected_namespaces=(),
    extra="forbid",
)


# ── Request ──────────────────────────────────────────────

class FeatureVector(BaseModel):
    """Merchant feature vector — all numeric KPIs."""

    avg_order_value: float = 0.0
    aov_variance: float = 0.0
    repeat_rate: float = 0.0
    purchase_frequency_variance: float = 0.0
    days_to_second_purchase: float = 0.0
    product_concentration: float = 0.0
    catalog_size: int = 0
    email_engagement_score: float = 0.0
    total_customer_count: int = 0
    revenue_last_90d: float = 0.0
    revenue_last_30d: float = 0.0

    model_config = ENGINE_CONFIG


class OnboardingResponses(BaseModel):
    """Merchant's Lola chatbot qualifying answers — expanded v2."""

    vertical_hint: Optional[str] = None
    goal_hint: Optional[str] = None
    price_hint: Optional[str] = None      # NEW: "budget" | "mid" | "premium" | "luxury"
    audience_hint: Optional[str] = None   # NEW: e.g. "women 25-40 skincare enthusiasts"
    primary_challenge: Optional[str] = None  # NEW: free-text merchant challenge

    model_config = ENGINE_CONFIG


class DiscoveryRequest(BaseModel):
    """POST /engine/v1/discovery/profile — Request body."""

    merchant_id: str
    feature_vector: Optional[FeatureVector] = None
    onboarding_responses: Optional[OnboardingResponses] = None

    model_config = ENGINE_CONFIG


# ── Response ─────────────────────────────────────────────

class DiscoveryResponse(BaseModel):
    """
    Full merchant profile — everything about any merchant.

    Core fields (always populated):
      persona, vertical, maturity_score, initial_focus, confidence_score

    Deep profile fields (populated when Ollama is available or
    onboarding_responses are rich):
      target_audience, price_point_tier, key_value_proposition,
      growth_signals, dominant_channel, churn_risk_level
    """

    merchant_id: str
    persona: str
    vertical: str
    seasonality: str = "neutral"
    catalog_complexity: str = "low"
    maturity_score: int = Field(ge=0, le=100)
    initial_focus: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str

    # ── Deep Profile ───────────────────────────────────
    target_audience: str = ""           # e.g. "Women 25-45 interested in skincare"
    price_point_tier: str = "mid"       # budget | mid | premium | luxury
    key_value_proposition: str = ""     # e.g. "Clean, sustainable formulations"
    growth_signals: List[str] = []      # e.g. ["Rising repeat rate", "Growing list"]
    dominant_channel: str = "email"     # email | social | both | paid
    churn_risk_level: str = "medium"    # low | medium | high

    model_version: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ENGINE_CONFIG
