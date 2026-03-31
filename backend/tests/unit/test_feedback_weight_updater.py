"""
Unit tests for Feedback Engine weight updater.

File: backend/tests/unit/test_feedback_weight_updater.py
"""

import pytest

from engines.feedback.weight_updater import update_weight, reset_weights
from engines.feedback.classifier import classify_performance
from engines.feedback.schemas import CampaignMetrics


class TestWeightUpdater:
    """Test rule weight adjustment logic."""

    def setup_method(self):
        """Reset weight store before each test."""
        reset_weights()

    def test_success_increases_weight(self):
        old, new, adj, _, _ = update_weight("REV-01", "success", current_weight=0.50)
        assert new > old
        assert adj > 0

    def test_failure_decreases_weight(self):
        old, new, adj, _, _ = update_weight("REV-01", "failure", current_weight=0.50)
        assert new < old
        assert adj < 0

    def test_neutral_no_change(self):
        old, new, adj, _, _ = update_weight("REV-01", "neutral", current_weight=0.50)
        assert old == new
        assert adj == 0

    def test_weight_clamped_at_min(self):
        """Weight should never go below 0.10."""
        old, new, _, _, _ = update_weight("REV-01", "failure", current_weight=0.10)
        assert new >= 0.10

    def test_weight_clamped_at_max(self):
        """Weight should never exceed 1.0."""
        old, new, _, _, _ = update_weight("REV-01", "success", current_weight=0.98)
        assert new <= 1.0

    def test_repeated_success_converges_to_max(self):
        """Many successes should push weight toward 1.0."""
        w = 0.50
        for _ in range(100):
            _, w, _, _, _ = update_weight("REV-01", "success", current_weight=w)
        assert w == 1.0

    def test_repeated_failure_converges_to_min(self):
        """Many failures should push weight toward 0.10."""
        w = 0.50
        for _ in range(100):
            _, w, _, _, _ = update_weight("REV-01", "failure", current_weight=w)
        assert w == 0.10


class TestPerformanceClassifier:
    """Test campaign performance classification."""

    def test_high_engagement_is_success(self):
        metrics = CampaignMetrics(
            revenue_attributed=500.0,
            open_rate=0.30,
            click_rate=0.06,
            conversion_rate=0.02,
            unsubscribe_rate=0.001,
        )
        assert classify_performance(metrics) == "success"

    def test_no_engagement_is_failure(self):
        metrics = CampaignMetrics(
            revenue_attributed=0,
            open_rate=0,
            click_rate=0,
            conversion_rate=0,
            unsubscribe_rate=0,
        )
        assert classify_performance(metrics) == "failure"

    def test_high_unsubscribe_is_failure(self):
        metrics = CampaignMetrics(
            revenue_attributed=200.0,
            open_rate=0.25,
            click_rate=0.04,
            conversion_rate=0.01,
            unsubscribe_rate=0.05,  # 10x baseline
        )
        assert classify_performance(metrics) == "failure"

    def test_moderate_performance_is_neutral(self):
        metrics = CampaignMetrics(
            revenue_attributed=50.0,
            open_rate=0.22,  # Boosted slightly above baseline of 0.20
            click_rate=0.035, # Boosted slightly above baseline of 0.03
            conversion_rate=0.008,
            unsubscribe_rate=0.002,
        )
        assert classify_performance(metrics) == "neutral"
