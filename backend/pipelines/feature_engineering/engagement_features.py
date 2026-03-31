"""
Engagement Feature Engineering Pipeline.

Computes email engagement metrics from Klaviyo data.

File: backend/pipelines/feature_engineering/engagement_features.py
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("bravola.pipelines.engagement_features")


def compute_engagement_features(
    email_events: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Compute engagement features from email event data.

    Input: raw email send/open/click/unsubscribe events.
    Output: engagement metrics dict.
    """

    if not email_events:
        return {
            "open_rate_avg": 0.0,
            "click_rate_avg": 0.0,
            "unsubscribe_rate": 0.0,
            "email_engagement_score": 0.0,
        }

    total_sent = sum(1 for e in email_events if e.get("event_type") == "sent")
    total_opened = sum(1 for e in email_events if e.get("event_type") == "opened")
    total_clicked = sum(1 for e in email_events if e.get("event_type") == "clicked")
    total_unsub = sum(1 for e in email_events if e.get("event_type") == "unsubscribed")

    open_rate = total_opened / max(total_sent, 1)
    click_rate = total_clicked / max(total_sent, 1)
    unsub_rate = total_unsub / max(total_sent, 1)

    # Composite engagement score
    engagement_score = (0.5 * open_rate) + (0.35 * click_rate) - (0.15 * unsub_rate)
    engagement_score = max(0, min(1, engagement_score))

    return {
        "open_rate_avg": round(open_rate, 4),
        "click_rate_avg": round(click_rate, 4),
        "unsubscribe_rate": round(unsub_rate, 4),
        "email_engagement_score": round(engagement_score, 4),
    }
