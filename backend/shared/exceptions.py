"""
Custom exception types for the AI Engine.

File: backend/shared/exceptions.py
"""


class BravolaEngineError(Exception):
    """Base exception for all AI engine errors."""

    def __init__(self, message: str = "Engine error", engine: str = "unknown"):
        self.engine = engine
        super().__init__(message)


class FeatureStoreError(BravolaEngineError):
    """Raised when Feast / feature store is unavailable or stale."""

    def __init__(self, message: str = "Feature store unavailable"):
        super().__init__(message, engine="feature_store")


class ModelRegistryError(BravolaEngineError):
    """Raised when MLflow model cannot be loaded."""

    def __init__(self, message: str = "Model registry error"):
        super().__init__(message, engine="model_registry")


class ModelNotFoundError(ModelRegistryError):
    """Raised when a specific model version/stage is not found."""

    def __init__(self, model_name: str, stage: str = "Production"):
        super().__init__(f"Model '{model_name}' not found at stage '{stage}'")


class InferenceError(BravolaEngineError):
    """Raised when model inference fails."""
    pass


class RuleEngineError(BravolaEngineError):
    """Raised when rule evaluation fails."""

    def __init__(self, message: str = "Rule engine error"):
        super().__init__(message, engine="strategy")


class RetrainTriggerError(BravolaEngineError):
    """Raised when retrain dispatch fails."""

    def __init__(self, message: str = "Retrain trigger failed"):
        super().__init__(message, engine="feedback")
