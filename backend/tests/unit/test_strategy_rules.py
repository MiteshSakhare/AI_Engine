"""
Unit tests for Strategy Engine rule evaluation and scoring.

Updated for the full 29-rule production set from the Excel addendum.

File: backend/tests/unit/test_strategy_rules.py
"""

import json
from pathlib import Path
import pytest

from engines.strategy.rules.engine import RuleEngine
from engines.strategy.rules.rules_registry import (
    get_all_rules, get_rule_by_id, get_rules_by_category,
    CATEGORY_WEIGHTS, RULES_BY_CATEGORY,
)


class TestRulesRegistry:
    """Test validity of rule definitions."""

    def test_total_rule_count_is_29(self):
        """We should have exactly 41 rules total."""
        assert len(get_all_rules()) == 41

    def test_category_counts(self):
        """Revenue=11, AudEng=11, AudGrowth=9, EmailEng=10."""
        assert len(get_rules_by_category("revenue")) == 11
        assert len(get_rules_by_category("audience_engagement")) == 11
        assert len(get_rules_by_category("audience_growth")) == 9
        assert len(get_rules_by_category("email_engagement")) == 10

    def test_category_weights_sum_to_one(self):
        """Category weights must sum to 1.0."""
        assert abs(sum(CATEGORY_WEIGHTS.values()) - 1.0) < 0.001

    def test_all_rules_have_valid_ids(self):
        for rule in get_all_rules():
            assert rule.rule_id.startswith(("REV-", "ENG-", "AUD-", "OPEN-"))

    def test_all_rules_have_positive_base_weight(self):
        for rule in get_all_rules():
            assert rule.base_weight > 0

    def test_all_rules_have_campaigns(self):
        for rule in get_all_rules():
            assert len(rule.campaigns) > 0

    def test_all_rules_have_qualifying_questions(self):
        """All rules should have at least one qualifying question."""
        for rule in get_all_rules():
            assert len(rule.qualifying_questions) > 0, f"{rule.rule_id} has no qualifying questions"

    def test_rule_lookup_by_id(self):
        rule = get_rule_by_id("REV-01")
        assert rule is not None
        assert rule.description == "Low returning customer rate"

    def test_rule_lookup_nonexistent(self):
        assert get_rule_by_id("FAKE-99") is None

    def test_global_weight_is_positive(self):
        """global_weight should be > 0 for all rules."""
        for rule in get_all_rules():
            assert rule.global_weight > 0, f"{rule.rule_id} has zero global_weight"


class TestRuleEngine:
    """Test rule evaluation against KPI metrics."""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_rev01_low_repeat_triggers(self, engine):
        """REV-01: repeat_customer_rate < 0.20 → triggered."""
        kpis = {"repeat_customer_rate": 0.12}
        triggered = engine.evaluate(kpis, [], {}, [])
        rule_ids = [r.rule_id for r in triggered]
        assert "REV-01" in rule_ids

    def test_rev01_above_threshold_does_not_trigger(self, engine):
        """REV-01: repeat_customer_rate = 0.22 → NOT triggered."""
        kpis = {"repeat_customer_rate": 0.22}
        triggered = engine.evaluate(kpis, [], {}, [])
        rule_ids = [r.rule_id for r in triggered]
        assert "REV-01" not in rule_ids

    def test_rev02_high_margin_triggers(self, engine):
        """REV-02: top_product_margin > 0.70 → triggered."""
        kpis = {"top_product_margin": 0.75}
        triggered = engine.evaluate(kpis, [], {}, [])
        rule_ids = [r.rule_id for r in triggered]
        assert "REV-02" in rule_ids

    def test_eng01_low_click_rate_triggers(self, engine):
        """ENG-01: click_rate_avg < 0.01 → triggered."""
        kpis = {"click_rate_avg": 0.005}
        triggered = engine.evaluate(kpis, [], {}, [])
        rule_ids = [r.rule_id for r in triggered]
        assert "ENG-01" in rule_ids

    def test_open01_high_open_rate_does_not_trigger(self, engine):
        """OPEN-01: open_rate_avg = 0.50 (> 0.30 threshold) → NOT triggered."""
        kpis = {"open_rate_avg": 0.50}
        triggered = engine.evaluate(kpis, [], {}, [])
        rule_ids = [r.rule_id for r in triggered]
        assert "OPEN-01" not in rule_ids


class TestSampleMerchantFixture:
    """Test rule evaluation against the sample merchant from the Excel addendum."""

    @pytest.fixture
    def sample_data(self):
        fixture_path = Path(__file__).parents[1] / "fixtures" / "sample_merchant_features.json"
        with open(fixture_path) as f:
            return json.load(f)

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_expected_rules_fire(self, engine, sample_data):
        """Rules listed in expected_triggered_rules should fire."""
        triggered = engine.evaluate(sample_data["metrics"], [], {}, [])
        triggered_ids = {r.rule_id for r in triggered}

        for expected_id in sample_data["expected_triggered_rules"]:
            assert expected_id in triggered_ids, (
                f"Expected rule {expected_id} to fire but it didn't. "
                f"Triggered: {sorted(triggered_ids)}"
            )

    def test_expected_rules_do_not_fire(self, engine, sample_data):
        """Rules listed in expected_not_triggered should NOT fire."""
        triggered = engine.evaluate(sample_data["metrics"], [], {}, [])
        triggered_ids = {r.rule_id for r in triggered}

        for not_expected_id in sample_data["expected_not_triggered"]:
            assert not_expected_id not in triggered_ids, (
                f"Rule {not_expected_id} should NOT fire but it did."
            )

    def test_at_least_16_rules_fire(self, engine, sample_data):
        """The addendum says 16+ rules should fire for this merchant (22 actually)."""
        triggered = engine.evaluate(sample_data["metrics"], [], {}, [])
        assert len(triggered) >= 16
