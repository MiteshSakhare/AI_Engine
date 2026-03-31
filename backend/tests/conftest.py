"""
Test configuration and fixtures.

File: backend/tests/conftest.py
"""

import sys
import os
from pathlib import Path

import pytest

# Add backend/ to Python path so imports work
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# Set test environment variables before importing app code
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture
def sample_feature_vector():
    """Sample merchant feature vector for testing."""
    return {
        "avg_order_value": 75.50,
        "repeat_rate": 0.28,
        "days_to_second_purchase": 14.0,
        "product_concentration": 0.45,
        "email_engagement_score": 0.35,
        "total_customer_count": 2500,
        "revenue_last_90d": 185000.0,
        "revenue_last_30d": 62000.0,
    }


@pytest.fixture
def sample_feature_array(sample_feature_vector):
    """Ordered feature array."""
    from engines.discovery.features import FEATURE_NAMES
    return [float(sample_feature_vector.get(f, 0)) for f in FEATURE_NAMES]


@pytest.fixture
def sample_kpi_metrics():
    """Sample KPI metrics for benchmark testing."""
    return {
        "repeat_purchase_rate": 0.22,
        "open_rate_avg": 0.18,
        "click_rate_avg": 0.035,
        "conversion_rate_avg": 0.012,
        "revenue_per_email": 0.85,
        "customer_ltv": 220.0,
        "cart_abandonment_rate": 0.68,
        "new_customer_rate": 0.48,
    }


@pytest.fixture
def sample_peer_medians():
    """Sample peer cluster medians."""
    return {
        "repeat_purchase_rate": 0.25,
        "open_rate_avg": 0.20,
        "click_rate_avg": 0.04,
        "conversion_rate_avg": 0.012,
        "revenue_per_email": 0.90,
        "customer_ltv": 200.0,
        "cart_abandonment_rate": 0.60,
        "new_customer_rate": 0.45,
    }


@pytest.fixture
def sample_peer_stds():
    """Sample peer cluster standard deviations."""
    return {
        "repeat_purchase_rate": 0.05,
        "open_rate_avg": 0.05,
        "click_rate_avg": 0.01,
        "conversion_rate_avg": 0.005,
        "revenue_per_email": 0.20,
        "customer_ltv": 50.0,
        "cart_abandonment_rate": 0.10,
        "new_customer_rate": 0.10,
    }
