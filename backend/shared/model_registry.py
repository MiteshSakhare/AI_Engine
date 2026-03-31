"""
MLflow Model Registry client wrapper.

- load_model(engine_name, stage="Production") → model
- Models loaded at app startup and cached in memory
- Background thread checks for new model version every 60s

File: backend/shared/model_registry.py
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

from shared.config import settings

logger = logging.getLogger("bravola.model_registry")


class ModelRegistry:
    """
    Wraps MLflow model loading with in-memory caching
    and background version polling.

    When MLflow is unavailable (dev mode), returns None
    and engines fall back to their built-in default models.
    """

    def __init__(self) -> None:
        self._client = None
        self._models: Dict[str, Any] = {}
        self._versions: Dict[str, str] = {}
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False
        self._init_mlflow()

    def _init_mlflow(self) -> None:
        if not settings.MLFLOW_TRACKING_URI:
            logger.info("MLflow not configured — engines will use built-in models")
            return

        try:
            import mlflow

            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            self._client = mlflow.tracking.MlflowClient()
            logger.info("MLflow connected: %s", settings.MLFLOW_TRACKING_URI)
        except Exception as exc:
            logger.warning("MLflow init failed: %s", exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    def load_model(
        self,
        engine_name: str,
        stage: str = "Production",
    ) -> Optional[Any]:
        """
        Load a model from MLflow by engine name and stage.
        Returns cached version if already loaded.
        """
        cache_key = f"{engine_name}/{stage}"

        if cache_key in self._models:
            return self._models[cache_key]

        if not self._client:
            return None

        try:
            import mlflow.pyfunc

            model_uri = f"models:/{engine_name}/{stage}"
            model = mlflow.pyfunc.load_model(model_uri)
            self._models[cache_key] = model
            logger.info("Model loaded: %s (stage=%s)", engine_name, stage)
            return model
        except Exception as exc:
            logger.warning("Failed to load model %s: %s", cache_key, exc)
            return None

    def register_model(
        self,
        model: Any,
        engine_name: str,
        metrics: Optional[Dict[str, float]] = None,
    ) -> Optional[str]:
        """Log and register a model with MLflow."""
        if not self._client:
            logger.info("MLflow unavailable — model not registered")
            return None

        try:
            import mlflow

            with mlflow.start_run(run_name=f"{engine_name}_training"):
                if metrics:
                    mlflow.log_metrics(metrics)
                info = mlflow.sklearn.log_model(
                    model,
                    artifact_path=engine_name,
                    registered_model_name=engine_name,
                )
            version = info.registered_model_version
            logger.info("Model registered: %s v%s", engine_name, version)
            return version
        except Exception as exc:
            logger.warning("Model registration failed: %s", exc)
            return None

    def start_polling(self) -> None:
        """Start background thread that checks for new model versions."""
        if not self._client or self._running:
            return

        self._running = True
        thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="model-version-poller",
        )
        self._poll_thread = thread
        thread.start()
        logger.info("Model version polling started (interval=%ds)", settings.MODEL_POLL_INTERVAL_SECONDS)

    def stop_polling(self) -> None:
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(settings.MODEL_POLL_INTERVAL_SECONDS)
            try:
                self._check_versions()
            except Exception as exc:
                logger.warning("Model poll error: %s", exc)

    def _check_versions(self) -> None:
        """Check MLflow for new Production versions and hot-swap."""
        client = self._client
        if not client:
            return

        for cache_key, model in list(self._models.items()):
            engine_name, stage = cache_key.split("/")
            try:
                versions = client.get_latest_versions(engine_name, stages=[stage])
                if versions:
                    latest = versions[0].version
                    if self._versions.get(cache_key) != latest:
                        logger.info("New model version detected: %s v%s", engine_name, latest)
                        self._models.pop(cache_key, None)
                        self._versions.pop(cache_key, None)
                        self.load_model(engine_name, stage)
                        self._versions[cache_key] = latest
            except Exception:
                pass


# Singleton
model_registry = ModelRegistry()
