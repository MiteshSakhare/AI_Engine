"""
Integration tests — Direct service-level testing.

Tests the complete pipeline for each engine without requiring
a database connection.

File: backend/tests/integration/test_endpoints.py
"""

import pytest
import asyncio

from engines.discovery.schemas import DiscoveryRequest, FeatureVector, OnboardingResponses
from engines.discovery.service import DiscoveryService

from engines.benchmark.schemas import BenchmarkRequest, KPIMetrics, BenchmarkContext
from engines.benchmark.service import BenchmarkService

from engines.strategy.schemas import (
    StrategyRequest, DiscoveryOutput, BenchmarkOutput, Constraints,
)
from engines.strategy.service import StrategyService

from engines.feedback.schemas import FeedbackRequest, CampaignMetrics, HumanFeedback
from engines.feedback.service import FeedbackService


def run_async(coro):
    """Helper to run async functions in sync tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestDiscoveryIntegration:
    """Full discovery pipeline integration test."""

    def test_full_pipeline_with_features_and_hint(self):
        service = DiscoveryService()
        request = DiscoveryRequest(
            merchant_id="test-merchant-001",
            feature_vector=FeatureVector(
                avg_order_value=75.0,
                repeat_rate=0.28,
                days_to_second_purchase=14.0,
                product_concentration=0.45,
                email_engagement_score=0.35,
                total_customer_count=2500,
                revenue_last_90d=185000.0,
                revenue_last_30d=62000.0,
            ),
            onboarding_responses=OnboardingResponses(vertical_hint="beauty"),
        )
        result = run_async(service.profile(request))

        assert result.merchant_id == "test-merchant-001"
        assert result.persona in ["loyalist", "value_seeker", "explorer", "bargain_hunter"]
        assert result.vertical == "beauty"
        assert 0 <= result.maturity_score <= 100
        assert result.initial_focus in ["acquisition", "retention", "engagement"]
        assert 0 <= result.confidence_score <= 1
        assert len(result.reasoning) > 0

    def test_minimal_request(self):
        service = DiscoveryService()
        request = DiscoveryRequest(merchant_id="test-merchant-002")
        result = run_async(service.profile(request))
        assert result.merchant_id == "test-merchant-002"


class TestBenchmarkIntegration:
    """Full benchmark pipeline integration test."""

    def test_full_pipeline(self):
        service = BenchmarkService()
        request = BenchmarkRequest(
            merchant_id="test-merchant-001",
            kpi_metrics=KPIMetrics(
                repeat_purchase_rate=0.22,
                open_rate_avg=0.18,
                click_rate_avg=0.035,
                conversion_rate_avg=0.012,
                revenue_per_email=0.85,
                customer_ltv=220.0,
                cart_abandonment_rate=0.68,
                new_customer_rate=0.48,
            ),
            context=BenchmarkContext(
                vertical="beauty",
                maturity_score=65,
                region="US",
            ),
        )
        result = run_async(service.report(request))

        assert 0 <= result.health_score <= 100
        assert result.funnel_scores.acquisition >= 0
        assert result.funnel_scores.conversion >= 0
        assert result.funnel_scores.retention >= 0
        assert isinstance(result.gap_flags, list)
        assert result.peer_cluster_id.startswith("beauty")


class TestStrategyIntegration:
    """Full strategy pipeline integration test."""

    def test_full_pipeline(self):
        service = StrategyService()
        request = StrategyRequest(
            merchant_id="test-merchant-001",
            discovery_output=DiscoveryOutput(
                persona="loyalist",
                vertical="beauty",
                maturity_score=65,
                initial_focus="retention",
            ),
            benchmark_output=BenchmarkOutput(
                health_score=42,
                gap_flags=["repeat purchase rate is 30% below peer median"],
                funnel_scores={"acquisition": 55, "conversion": 40, "retention": 35},
                peer_cluster_id="beauty-mid-us",
            ),
            constraints=Constraints(
                available_channels=["email"],
                active_flow_ids=[],
                budget_tier="mid",
            ),
        )
        result = run_async(service.generate(request))

        assert result.merchant_id == "test-merchant-001"
        assert hasattr(result, "tracks")
        all_strategies = (
            result.tracks.quick_wins
            + result.tracks.core_growth
            + result.tracks.retention_rescue
            + result.tracks.crisis_response
        )
        assert len(all_strategies) > 0
        for s in all_strategies:
            assert s.strategy_score > 0
            assert s.priority_rank >= 1
            assert len(s.campaigns) > 0
            assert s.category in ["revenue", "audience_engagement", "audience_growth", "email_engagement"]


class TestFeedbackIntegration:
    """Full feedback pipeline integration test."""

    def test_success_campaign(self):
        service = FeedbackService()
        request = FeedbackRequest(
            merchant_id="test-merchant-001",
            strategy_id_code="winback_30_day",
            triggered_rule_id="REV-01",
            campaign_metrics=CampaignMetrics(
                revenue_attributed=500.0,
                open_rate=0.30,
                click_rate=0.06,
                conversion_rate=0.02,
                unsubscribe_rate=0.001,
            ),
        )
        result = run_async(service.process(request))
        assert result.performance_label == "success"
        assert result.weight_updates[0].new_weight > result.weight_updates[0].old_weight

    def test_human_override(self):
        service = FeedbackService()
        request = FeedbackRequest(
            merchant_id="test-merchant-001",
            strategy_id_code="winback_30_day",
            triggered_rule_id="REV-02",
            campaign_metrics=CampaignMetrics(
                revenue_attributed=50.0,
                open_rate=0.10,
                click_rate=0.02,
                conversion_rate=0.005,
            ),
            human_feedback=HumanFeedback(action="approved"),
        )
        result = run_async(service.process(request))
        assert result.performance_label == "success"


class TestEndToEndPipeline:
    """Test all 4 engines chained together."""

    def test_full_chain(self):
        # 1. Discovery
        discovery_service = DiscoveryService()
        discovery_result = run_async(discovery_service.profile(
            DiscoveryRequest(
                merchant_id="chain-test-001",
                feature_vector=FeatureVector(
                    avg_order_value=65.0,
                    repeat_rate=0.15,
                    total_customer_count=800,
                    revenue_last_90d=45000.0,
                    revenue_last_30d=14000.0,
                ),
            )
        ))
        assert discovery_result.persona in ["loyalist", "value_seeker", "explorer", "bargain_hunter"]

        # 2. Benchmark
        benchmark_service = BenchmarkService()
        benchmark_result = run_async(benchmark_service.report(
            BenchmarkRequest(
                merchant_id="chain-test-001",
                kpi_metrics=KPIMetrics(
                    repeat_purchase_rate=0.15,
                    open_rate_avg=0.16,
                    click_rate_avg=0.03,
                    conversion_rate_avg=0.008,
                    revenue_per_email=0.60,
                    customer_ltv=150.0,
                    cart_abandonment_rate=0.72,
                    new_customer_rate=0.55,
                ),
                context=BenchmarkContext(
                    vertical=discovery_result.vertical,
                    maturity_score=discovery_result.maturity_score,
                ),
            )
        ))
        assert 0 <= benchmark_result.health_score <= 100

        # 3. Strategy
        strategy_service = StrategyService()
        strategy_result = run_async(strategy_service.generate(
            StrategyRequest(
                merchant_id="chain-test-001",
                discovery_output=DiscoveryOutput(
                    persona=discovery_result.persona,
                    vertical=discovery_result.vertical,
                    maturity_score=discovery_result.maturity_score,
                    initial_focus=discovery_result.initial_focus,
                ),
                benchmark_output=BenchmarkOutput(
                    health_score=benchmark_result.health_score,
                    gap_flags=benchmark_result.gap_flags,
                    funnel_scores={
                        "acquisition": benchmark_result.funnel_scores.acquisition,
                        "conversion": benchmark_result.funnel_scores.conversion,
                        "retention": benchmark_result.funnel_scores.retention,
                    },
                    peer_cluster_id=benchmark_result.peer_cluster_id,
                ),
            )
        ))
        all_strategies = (
            strategy_result.tracks.quick_wins
            + strategy_result.tracks.core_growth
            + strategy_result.tracks.retention_rescue
            + strategy_result.tracks.crisis_response
        )
        assert len(all_strategies) > 0

        # 4. Feedback
        first_strategy = all_strategies[0]
        feedback_service = FeedbackService()
        feedback_result = run_async(feedback_service.process(
            FeedbackRequest(
                merchant_id="chain-test-001",
                strategy_id_code=first_strategy.rule_id,
                triggered_rule_id=first_strategy.rule_id,
                campaign_metrics=CampaignMetrics(
                    revenue_attributed=350.0,
                    open_rate=0.28,
                    click_rate=0.05,
                    conversion_rate=0.015,
                    unsubscribe_rate=0.002,
                ),
            )
        ))
        assert feedback_result.performance_label in ["success", "neutral", "failure"]
