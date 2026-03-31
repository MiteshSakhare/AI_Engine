"""
Retrain Trigger — Threshold check → Celery task dispatch.

Tracks feedback event count per engine.
When count >= RETRAIN_THRESHOLD → dispatch retraining task.

File: backend/engines/feedback/retrain_trigger.py
"""

import logging
from typing import Dict

from shared.config import settings

logger = logging.getLogger("bravola.feedback.retrain_trigger")

# Track feedback events per engine/model
_event_counts: Dict[str, int] = {}


def increment_event_count(engine_name: str) -> int:
    """Increment event count for an engine and return new count."""
    _event_counts[engine_name] = _event_counts.get(engine_name, 0) + 1
    return _event_counts[engine_name]


def should_retrain(engine_name: str) -> bool:
    """Check if retrain threshold has been reached."""
    count = _event_counts.get(engine_name, 0)
    return count >= settings.RETRAIN_THRESHOLD


def dispatch_retrain(engine_name: str) -> bool:
    """
    Dispatch a Celery retraining task.

    Returns True if dispatched successfully.
    """
    try:
        from pipelines.retraining.tasks import retrain_model

        retrain_model.delay(engine_name)
        logger.info("Retrain task dispatched for %s", engine_name)

        # Reset counter
        _event_counts[engine_name] = 0
        return True
    except Exception as exc:
        logger.warning(
            "Failed to dispatch retrain task for %s: %s (Celery unavailable?)",
            engine_name,
            exc,
        )
        return False


def get_event_count(engine_name: str) -> int:
    """Get current event count for an engine."""
    return _event_counts.get(engine_name, 0)


def reset_counts() -> None:
    """Reset all counters (for testing)."""
    _event_counts.clear()
