"""
Unit tests for Strategy scoring formula.

File: backend/tests/unit/test_strategy_scorer.py
"""

import pytest

from engines.strategy.scorer import compute_strategy_scores
from engines.strategy.rules.rules_registry import get_rule_by_id


class TestStrategyScorer:
    """Test the hybrid scoring formula with category weights."""

    def test_scores_are_sorted_descending(self):
        """Scored strategies should come back sorted by score."""
        rules = [get_rule_by_id("REV-01"), get_rule_by_id("ENG-02"), get_rule_by_id("REV-07")]
        rules = [r for r in rules if r is not None]
        scored = compute_strategy_scores(rules)
        scores = [s[4] for s in scored]
        assert scores == sorted(scores, reverse=True)

    def test_rev07_scores_highest_in_revenue(self):
        """REV-07 (base_weight=35, highest in Revenue) should rank highly."""
        rules = [get_rule_by_id("REV-07"), get_rule_by_id("REV-02")]
        rules = [r for r in rules if r is not None]
        scored = compute_strategy_scores(rules)
        # REV-07 should be first (higher weight)
        assert scored[0][0].rule_id == "REV-07"

    def test_score_is_positive(self):
        """All scores should be positive with default parameters."""
        rules = [get_rule_by_id(r) for r in ["REV-01", "REV-03", "ENG-01", "AUD-01", "OPEN-01"]]
        rules = [r for r in rules if r is not None]
        scored = compute_strategy_scores(rules)
        for _, _, _, _, score in scored:
            assert score > 0

    def test_global_weight_uses_category_weights(self):
        """Revenue rule weight should factor in 0.40 category weight."""
        rule = get_rule_by_id("REV-07")
        assert rule is not None
        # REV-07 base_weight=35, total in revenue ~100, category weight=0.40
        # global_weight = (35/150) * 0.40 = 0.093
        assert 0.08 <= rule.global_weight <= 0.20

    def test_empty_rules_returns_empty(self):
        """Empty input → empty output."""
        scored = compute_strategy_scores([])
        assert scored == []
