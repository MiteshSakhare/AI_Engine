"""
Shared FastAPI dependencies — DB session, feature store, model loader.

File: backend/api/dependencies.py
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from shared.db import get_db
from shared.feature_store import FeatureStoreClient, feature_store_client
from shared.model_registry import ModelRegistry, model_registry


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Alias for shared db dependency."""
    async for session in get_db():
        yield session


def get_feature_store() -> FeatureStoreClient:
    """Return the global feature store client."""
    return feature_store_client


def get_model_registry() -> ModelRegistry:
    """Return the global model registry."""
    return model_registry
