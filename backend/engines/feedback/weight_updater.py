"""
Rule Weight Updater — UCB1 Multi-Armed Bandit v2.

Replaces simple proportional weight adjustment with Upper Confidence
Bound (UCB1) algorithm, balancing:
  - Exploitation: uses proven high-converting strategies
  - Exploration:  tries under-explored strategies periodically

UCB1 Formula:
  score = (cumulative_reward / plays) + C * sqrt(ln(total_plays) / plays)

Where C is the exploration constant (sqrt(2) ≈ 1.414 by default,
configurable via UCB1_C in settings).

State is maintained in-memory. In production, wire to a PostgreSQL
`rule_weights` table via Alembic migration (see stretch goals in plan).

File: backend/engines/feedback/weight_updater.py
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Optional, Tuple

from shared.config import settings

logger = logging.getLogger("bravola.feedback.weight_updater")


# ── In-memory state ──────────────────────────────────────
# NOTE: In production these should persist in PostgreSQL.

_weight_store:  Dict[str, float] = {}  # rule_id → current weight (0.10–1.0)
_plays:         Dict[str, int]   = {}  # rule_id → times recommended
_rewards:       Dict[str, float] = {}  # rule_id → cumulative reward signal


# ── Public API ───────────────────────────────────────────

def get_current_weight(rule_id: str, default: float = 0.5) -> float:
    """Get current weight for a rule."""
    return _weight_store.get(rule_id, default)


def record_play(rule_id: str) -> None:
    """
    Call this when a strategy rule is RECOMMENDED to a merchant.
    Increments the play counter used by UCB1 exploration term.
    """
    _plays[rule_id] = _plays.get(rule_id, 0) + 1


def update_weight(
    rule_id: str,
    performance_label: str,
    current_weight: Optional[float] = None,
) -> Tuple[float, float, float, float, float]:
    """
    Update rule weight using UCB1 reward signal.

    Steps:
    1. Map performance_label → reward signal (0.0, 0.5, or 1.0)
    2. Accumulate reward in _rewards
    3. Proportionally adjust base weight for immediate ranking use
    4. Compute UCB1 score for exploratory recommendations

    Returns:
        (old_weight, new_weight, adjustment, ucb1_score, exploration_bonus)
    """
    lr = settings.LEARNING_RATE
    c  = getattr(settings, "UCB1_C", 1.414)   # exploration constant

    if current_weight is None:
        current_weight = get_current_weight(rule_id)

    old_weight = current_weight

    # ── 1. Map label → reward ────────────────────────────
    reward_map = {"success": 1.0, "neutral": 0.5, "failure": 0.0}
    reward = reward_map.get(performance_label, 0.5)

    # ── 2. Accumulate reward ─────────────────────────────
    _rewards[rule_id] = _rewards.get(rule_id, 0.0) + reward

    # Ensure at least 1 play recorded (idempotent if record_play() was called)
    if _plays.get(rule_id, 0) == 0:
        _plays[rule_id] = 1

    # ── 3. Proportional weight update ────────────────────
    if performance_label == "success":
        adjustment  = lr * current_weight
        new_weight  = current_weight + adjustment
    elif performance_label == "failure":
        adjustment  = -(lr * current_weight)
        new_weight  = current_weight + adjustment
    else:
        # Neutral — no base weight change
        new_weight = current_weight
        adjustment = 0.0

    # Clamp to [0.10, 1.0]
    new_weight = max(0.10, min(1.0, new_weight))
    adjustment = new_weight - old_weight

    _weight_store[rule_id] = new_weight

    # ── 4. UCB1 score ────────────────────────────────────
    total_plays = max(1, sum(_plays.values()))
    rule_plays  = max(1, _plays[rule_id])
    rule_reward = _rewards.get(rule_id, 0.5)

    exploitation    = rule_reward / rule_plays
    exploration_bonus = c * math.sqrt(math.log(total_plays) / rule_plays)
    ucb1_score      = exploitation + exploration_bonus

    logger.info(
        "Weight updated: %s %.3f→%.3f (adj=%.3f, label=%s, ucb1=%.4f, plays=%d)",
        rule_id, old_weight, new_weight, adjustment,
        performance_label, ucb1_score, rule_plays,
    )

    return old_weight, new_weight, adjustment, ucb1_score, exploration_bonus


def get_ucb1_score(rule_id: str) -> float:
    """
    Return the current UCB1 score for a rule without updating it.
    Used by the Strategy Engine to re-rank rules at recommendation time.
    """
    total_plays    = max(1, sum(_plays.values()))
    rule_plays     = max(1, _plays.get(rule_id, 0))
    rule_reward    = _rewards.get(rule_id, 0.5)
    c              = getattr(settings, "UCB1_C", 1.414)

    exploitation      = rule_reward / rule_plays
    exploration_bonus = c * math.sqrt(math.log(total_plays) / rule_plays)
    return exploitation + exploration_bonus


def get_all_ucb1_scores() -> Dict[str, float]:
    """Return UCB1 scores for all rules that have been played at least once."""
    return {rule_id: get_ucb1_score(rule_id) for rule_id in _plays}


def get_state_summary() -> Dict[str, Dict]:
    """Return full state for debugging / API exposure."""
    return {
        rule_id: {
            "weight": _weight_store.get(rule_id, 0.5),
            "plays":  _plays.get(rule_id, 0),
            "reward": _rewards.get(rule_id, 0.0),
            "ucb1":   get_ucb1_score(rule_id),
        }
        for rule_id in set(list(_plays.keys()) + list(_weight_store.keys()))
    }


def reset_weights() -> None:
    """Reset all state (for testing)."""
    _weight_store.clear()
    _plays.clear()
    _rewards.clear()
