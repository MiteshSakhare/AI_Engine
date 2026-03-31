"""
Shared Pydantic base schemas used across all engines.

Every engine response includes:
- The decision / prediction
- A confidence score
- A human-readable reasoning string
- The model version that produced it

File: backend/shared/schemas.py
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


ENGINE_CONFIG = ConfigDict(
    from_attributes=True,
    protected_namespaces=(),
    extra="forbid",
)


class EngineResponseBase(BaseModel):
    """
    Base schema that every engine response extends.
    Ensures machine-readable, auditable outputs.
    """

    merchant_id: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ENGINE_CONFIG


class ErrorResponse(BaseModel):
    """Structured error payload returned on failure."""

    detail: str
    engine: Optional[str] = None
    message: Optional[str] = None

    model_config = ENGINE_CONFIG
