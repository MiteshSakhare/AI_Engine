"""
Unit tests for the Benchmark Engine health score formula.

File: backend/tests/unit/test_benchmark_health_score.py
"""

import pytest

from engines.benchmark.health_score import compute_health_score


class TestHealthScore:
    """Test the deterministic health score formula."""

    def test_at_median_score_is_50(self, sample_peer_medians, sample_peer_stds):
        """When merchant matches peer medians exactly → ~50."""
        result = compute_health_score(sample_peer_medians, sample_peer_medians, sample_peer_stds)
        assert 45 <= result["health_score"] <= 55

    def test_zero_kpis_is_very_low(self, sample_peer_medians, sample_peer_stds):
        """All-zero KPIs → very low score (capped at ~25 because 0 abandonment is great)."""
        zero_kpis = {k: 0 for k in sample_peer_medians}
        result = compute_health_score(zero_kpis, sample_peer_medians, sample_peer_stds)
        assert result["health_score"] <= 30

    def test_double_median_is_high(self, sample_peer_medians, sample_peer_stds):
        """Double the peer median → high score (capped by ±2σ Winsorization to ~88)."""
        double_kpis = {k: v * 2 for k, v in sample_peer_medians.items()}
        # For abandonment rate, lower is better, so set to half
        double_kpis["cart_abandonment_rate"] = sample_peer_medians["cart_abandonment_rate"] / 2
        result = compute_health_score(double_kpis, sample_peer_medians, sample_peer_stds)
        assert 80 <= result["health_score"] <= 90

    def test_funnel_subscores_present(self, sample_kpi_metrics, sample_peer_medians, sample_peer_stds):
        """Result should contain all three funnel sub-scores."""
        result = compute_health_score(sample_kpi_metrics, sample_peer_medians, sample_peer_stds)
        assert "acquisition_score" in result
        assert "conversion_score" in result
        assert "retention_score" in result
        assert 0 <= result["acquisition_score"] <= 100
        assert 0 <= result["conversion_score"] <= 100
        assert 0 <= result["retention_score"] <= 100

    def test_score_range(self, sample_kpi_metrics, sample_peer_medians, sample_peer_stds):
        """Health score should always be 0–100."""
        result = compute_health_score(sample_kpi_metrics, sample_peer_medians, sample_peer_stds)
        assert 0 <= result["health_score"] <= 100

    def test_weights_sum_correctly(self, sample_kpi_metrics, sample_peer_medians, sample_peer_stds):
        """Health = 0.30×acq + 0.30×conv + 0.40×ret."""
        result = compute_health_score(sample_kpi_metrics, sample_peer_medians, sample_peer_stds)
        expected = int(round(
            0.30 * result["acquisition_score"]
            + 0.30 * result["conversion_score"]
            + 0.40 * result["retention_score"]
        ))
        # Allow ±1 rounding tolerance
        assert abs(result["health_score"] - expected) <= 1
