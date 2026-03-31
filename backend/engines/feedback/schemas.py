"""
Feedback Engine — Pydantic Request/Response schemas v2.

Upgrades:
  - CampaignMetrics: added list_growth_rate (5th signal)
  - FeedbackRequest: added merchant_context for cluster-aware classification
  - WeightUpdate: added ucb1_score, exploration_bonus, total_rule_plays
  - FeedbackResponse: added feedback_summary (Ollama insight)
  - Fixed datetime.utcnow() deprecation

POST /engine/v1/feedback/process

File: backend/engines/feedback/schemas.py
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

class CampaignMetrics(BaseModel):
    """Measured campaign performance metrics."""

    revenue_attributed: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    conversion_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    list_growth_rate: float = 0.0    # NEW: 5th signal for success voting

    model_config = ENGINE_CONFIG


class HumanFeedback(BaseModel):
    """Merchant's human feedback on a strategy."""

    action: str = "none"          # approved | rejected | modified
    modified_strategy_id: Optional[str] = None
    comment: Optional[str] = None

    model_config = ENGINE_CONFIG


class MerchantContext(BaseModel):
    """Optional merchant context for adaptive baseline selection."""

    cluster_id: Optional[str] = None     # e.g. "beauty-mid-us"
    vertical: Optional[str] = None
    maturity_score: Optional[int] = None

    model_config = ENGINE_CONFIG


class FeedbackRequest(BaseModel):
    """POST /engine/v1/feedback/process — Request body."""

    merchant_id: str
    strategy_id_code: str
    triggered_rule_id: str
    campaign_metrics: CampaignMetrics
    human_feedback: Optional[HumanFeedback] = None
    merchant_context: Optional[MerchantContext] = None   # NEW: for adaptive baselines

    model_config = ENGINE_CONFIG


# ── Response ─────────────────────────────────────────────

class WeightUpdate(BaseModel):
    """Record of a rule weight adjustment with UCB1 metadata."""

    rule_id: str
    old_weight: float
    new_weight: float
    adjustment: float
    ucb1_score: Optional[float] = None          # NEW: UCB1 composite score
    exploration_bonus: Optional[float] = None   # NEW: UCB1 exploration term
    total_rule_plays: int = 0                   # NEW: how often this rule was recommended

    model_config = ENGINE_CONFIG


class FeedbackResponse(BaseModel):
    """Structured feedback processing result."""

    merchant_id: str
    strategy_id_code: str
    performance_label: str         # success | neutral | failure
    weight_updates: List[WeightUpdate]
    retrain_triggered: bool
    feedback_event_count: int
    feedback_summary: str = ""     # NEW: brief Ollama-generated insight on outcome
    model_version: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ENGINE_CONFIG
