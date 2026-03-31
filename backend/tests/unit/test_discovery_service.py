"""
Unit tests for the Discovery Engine service.

Tests: persona classification, maturity scoring, vertical classification,
initial_focus determination.

File: backend/tests/unit/test_discovery_service.py
"""

import pytest

from engines.discovery.models.persona import PersonaClassifier, PERSONA_LABELS
from engines.discovery.models.maturity import MaturityScorer
from engines.discovery.models.vertical import VerticalClassifier, VERTICAL_LABELS


class TestPersonaClassifier:
    """Test persona classification heuristic."""

    def test_loyalist_high_repeat_engagement(self):
        # repeat_rate=0.30, email_engagement=0.40 → loyalist
        features = [80, 0.30, 12, 0.50, 0.40, 3000, 200000, 70000]
        persona, confidence = PersonaClassifier().predict(features)
        assert persona == "loyalist"
        assert confidence >= 0.5

    def test_value_seeker_high_aov_low_repeat(self):
        # aov=150, repeat_rate=0.10 → value_seeker
        features = [150, 0.10, 30, 0.50, 0.20, 500, 50000, 15000]
        persona, confidence = PersonaClassifier().predict(features)
        assert persona == "value_seeker"
        assert confidence >= 0.5

    def test_bargain_hunter_low_aov_low_engagement(self):
        # aov=25, email_engagement=0.10 → bargain_hunter
        features = [25, 0.18, 45, 0.60, 0.10, 800, 20000, 6000]
        persona, confidence = PersonaClassifier().predict(features)
        assert persona == "bargain_hunter"
        assert confidence >= 0.5

    def test_explorer_low_concentration(self):
        # product_concentration=0.20 → explorer
        features = [60, 0.15, 20, 0.20, 0.25, 1200, 80000, 25000]
        persona, confidence = PersonaClassifier().predict(features)
        assert persona == "explorer"
        assert confidence >= 0.5

    def test_all_labels_valid(self):
        features = [50, 0.10, 20, 0.50, 0.20, 500, 30000, 10000]
        persona, _ = PersonaClassifier().predict(features)
        assert persona in PERSONA_LABELS


class TestMaturityScorer:
    """Test maturity scoring heuristic."""

    def test_new_store_low_maturity(self):
        features = [30, 0.05, 60, 0.80, 0.10, 50, 2000, 600]
        score = MaturityScorer().predict(features)
        assert 0 <= score <= 100
        assert score < 30

    def test_established_store_high_maturity(self):
        features = [120, 0.35, 10, 0.30, 0.45, 15000, 600000, 200000]
        score = MaturityScorer().predict(features)
        assert score >= 60

    def test_boundary_zero(self):
        features = [0, 0, 0, 0, 0, 0, 0, 0]
        score = MaturityScorer().predict(features)
        assert score == 0

    def test_score_range(self):
        features = [75, 0.20, 18, 0.40, 0.30, 2000, 150000, 50000]
        score = MaturityScorer().predict(features)
        assert 0 <= score <= 100


class TestVerticalClassifier:
    """Test vertical classification."""

    def test_onboarding_hint_beauty(self):
        features = [50] * 8
        vertical, confidence = VerticalClassifier().predict(features, vertical_hint="beauty products")
        assert vertical == "beauty"
        assert confidence >= 0.85

    def test_onboarding_hint_fashion(self):
        features = [50] * 8
        vertical, confidence = VerticalClassifier().predict(features, vertical_hint="fashion clothing")
        assert vertical == "apparel"
        assert confidence >= 0.85

    def test_onboarding_hint_pet(self):
        features = [50] * 8
        vertical, confidence = VerticalClassifier().predict(features, vertical_hint="dog treats")
        assert vertical == "pet"

    def test_no_hint_fallback(self):
        features = [50] * 8
        vertical, confidence = VerticalClassifier().predict(features)
        assert vertical in VERTICAL_LABELS

    def test_all_labels_valid(self):
        for hint in ["beauty", "apparel", "food", "home", "pet", "sports", "other"]:
            vertical, _ = VerticalClassifier().predict([50] * 8, vertical_hint=hint)
            assert vertical in VERTICAL_LABELS
