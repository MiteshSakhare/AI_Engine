"""
Strategy Rule Engine — Evaluate conditions against merchant metrics.

For each rule: evaluate condition → return set of triggered rules.

File: backend/engines/strategy/rules/engine.py
"""

import logging
from typing import Dict, Any, List

from engines.strategy.rules.rules_registry import RuleDefinition, get_all_rules

logger = logging.getLogger("bravola.strategy.rules")


class RuleEngine:
    """Evaluates marketing rules against merchant metrics and benchmark gaps."""

    def evaluate(
        self,
        kpi_metrics: Dict[str, Any],
        gap_flags: List[str],
        discovery: Dict[str, Any],
        active_flow_ids: List[str],
    ) -> List[RuleDefinition]:
        """
        Evaluate all 29 rules against input metrics.

        Returns list of triggered rules (where condition is met).
        """
        triggered = []

        for rule in get_all_rules():
            if self._evaluate_rule(rule, kpi_metrics):
                triggered.append(rule)
                logger.debug("Rule triggered: %s (%s)", rule.rule_id, rule.description)

        logger.info("Rules evaluated: %d triggered out of %d", len(triggered), len(get_all_rules()))
        return triggered

    def _evaluate_rule(
        self,
        rule: RuleDefinition,
        kpi_metrics: Dict[str, Any],
    ) -> bool:
        """Evaluate a single rule condition."""

        metric = rule.metric
        value = kpi_metrics.get(metric)

        if value is None:
            return False

        op = rule.threshold_operator
        threshold = rule.threshold_value

        # Boolean comparison (e.g. inventory_overstock_flag == True)
        if isinstance(threshold, bool):
            return bool(value) == threshold

        if op == "lt":
            return value < threshold
        elif op == "gt":
            return value > threshold
        elif op == "eq":
            if isinstance(threshold, (int, float)):
                return abs(float(value) - float(threshold)) < 0.001
            return value == threshold
        elif op == "lte":
            return value <= threshold
        elif op == "gte":
            return value >= threshold

        return False

    def filter_duplicates(
        self,
        triggered_rules: List[RuleDefinition],
        active_flow_ids: List[str],
    ) -> List[RuleDefinition]:
        """Remove rules whose flows are already active in Klaviyo."""
        if not active_flow_ids:
            return triggered_rules

        active_lower = [f.lower() for f in active_flow_ids]
        filtered = []

        for rule in triggered_rules:
            # Check if ALL of this rule's flows are already active
            rule_flows = [f.lower() for f in rule.flows]
            all_active = rule_flows and all(
                any(rf in af or af in rf for af in active_lower)
                for rf in rule_flows
            )

            if not all_active:
                filtered.append(rule)
            else:
                logger.info(
                    "Filtered rule %s — all flows already active",
                    rule.rule_id,
                )

        return filtered
