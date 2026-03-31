"""
Strategy Engine — Pydantic Request/Response schemas v2.

Upgrades:
  - StrategyTracks: added crisis_response track (4th dynamic track)
  - StrategyResponse: added strategy_narrative, total_triggered, tracks_populated
  - StrategyItem: added ollama_personalized flag for traceability
  - Fixed datetime.utcnow() deprecation

POST /engine/v1/strategy/generate

File: backend/engines/strategy/schemas.py
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict

from pydantic import BaseModel, Field, ConfigDict


ENGINE_CONFIG = ConfigDict(
    from_attributes=True,
    protected_namespaces=(),
    extra="forbid",
)


# ── Sub-models ────────────────────────────────────────────

class DiscoveryOutput(BaseModel):
    persona: str = "explorer"
    vertical: str = "other"
    maturity_score: int = 50
    initial_focus: str = "engagement"
    model_config = ENGINE_CONFIG


class BenchmarkOutput(BaseModel):
    health_score: int = 50
    gap_flags: List[str] = []
    funnel_scores: Dict[str, int] = {}
    peer_cluster_id: str = "general-mid-us"
    model_config = ENGINE_CONFIG


class Constraints(BaseModel):
    available_channels: List[str] = ["email"]
    active_flow_ids: List[str] = []
    budget_tier: str = "mid"   # low | mid | high
    model_config = ENGINE_CONFIG


# ── Request ──────────────────────────────────────────────

class StrategyRequest(BaseModel):
    merchant_id: str
    discovery_output: DiscoveryOutput
    benchmark_output: BenchmarkOutput
    constraints: Constraints = Constraints()
    model_config = ENGINE_CONFIG


# ── Strategy item ────────────────────────────────────────

class StrategyItem(BaseModel):
    rule_id: str
    category: str
    description: str
    campaigns: List[str]
    flows: List[str]
    qualifying_questions: List[str]
    priority_rank: int
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    rule_weighted_score: float
    model_lift_score: float
    confidence_penalty: float
    strategy_score: float
    creative_notes: Optional[str] = None
    ollama_personalized: bool = False   # NEW: True when description was rewritten by Ollama
    model_config = ENGINE_CONFIG


# ── Response ─────────────────────────────────────────────

class StrategyTracks(BaseModel):
    quick_wins: List[StrategyItem] = []          # Revenue + Email Engagement
    core_growth: List[StrategyItem] = []         # Audience Growth
    retention_rescue: List[StrategyItem] = []    # Audience Engagement
    crisis_response: List[StrategyItem] = []     # NEW: triggered when 3+ critical gaps


class StrategyResponse(BaseModel):
    merchant_id: str
    strategy_batch_id: str
    tracks: StrategyTracks
    strategy_narrative: str = ""     # NEW: Ollama executive summary
    total_triggered: int = 0         # NEW: total rules that fired
    tracks_populated: int = 0        # NEW: number of non-empty tracks
    model_version: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    model_config = ENGINE_CONFIG
