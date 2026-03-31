"""
Core Configuration — Pydantic BaseSettings
All environment variables for the Bravola AI Engine.

File: backend/shared/config.py
"""

from typing import List, Optional
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for all AI Engine configuration."""

    # ── App ────────────────────────────────────────────────
    PROJECT_NAME: str = "Bravola AI Engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    MODEL_VERSION: str = "v2"  # Bumped: reflects engine overhaul

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://bravola_user:bravola_pass@localhost:5432/bravola_db"
    DATABASE_SYNC_URL: str = "postgresql://bravola_user:bravola_pass@localhost:5432/bravola_db"
    DATABASE_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Feast Feature Store ────────────────────────────────
    FEAST_REPO_PATH: Optional[str] = None

    # ── MLflow ─────────────────────────────────────────────
    MLFLOW_TRACKING_URI: Optional[str] = None

    # ── Celery ─────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Ollama (LLM Reasoning) ─────────────────────────
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: int = 60          # Separate from connect timeout
    OLLAMA_TEMPERATURE_JSON: float = 0.1     # For structured JSON extraction
    OLLAMA_TEMPERATURE_REASONING: float = 0.7 # For heuristic enhancement
    OLLAMA_TEMPERATURE_CHAT: float = 0.8     # For merchant chat responses

    # ── Feedback Engine ────────────────────────────────────
    LEARNING_RATE: float = 0.05
    RETRAIN_THRESHOLD: int = 20
    UCB1_C: float = 1.414  # Exploration constant for UCB1 MAB (sqrt(2))

    # ── Strategy Engine ────────────────────────────────────
    MAX_STRATEGIES: int = 5               # Kept for backward compat
    MAX_STRATEGIES_PER_TRACK: int = 5     # Max items per strategy track
    TOTAL_STRATEGY_CANDIDATES: int = 20   # Max rules evaluated before trimming

    # Strategy scoring weights (tuned by Feedback Engine)
    W_RULE: float = 0.5
    W_MODEL: float = 0.3
    W_PENALTY: float = 0.2

    # ── ML Artifacts ───────────────────────────────────────
    ML_ARTIFACTS_PATH: Path = Path(__file__).resolve().parents[1] / "ml_artifacts"

    # ── CORS ───────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # ── Model refresh ──────────────────────────────────────
    MODEL_POLL_INTERVAL_SECONDS: int = 60

    # ── Security ───────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-min-32-chars"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
