# Master Improvement Plan: Bravola AI Engine

This document consolidates the comprehensive upgrade strategy for the Bravola platform, covering both deep mathematical/ML engine enhancements and architectural/DevOps improvements.

## User Review Required
> [!IMPORTANT]
> This master plan unifies all improvement vectors. We will be changing core calculation logic, adding robust MLOps, upgrading the Ollama integration, and hardening the backend architecture. Please review carefully to ensure all constraints and priorities align with your vision for this real-world SaaS project.

---

## Part 1: AI Engine & Machine Learning Overhaul

### 1. Benchmark Engine (Math & Logic)
Current implementation uses naive ratios (`merchant_val / peer_median`). This scales linearly and breaks when peers have 0 values or extreme outliers.

*   **Change:** Upgrade [health_score.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/benchmark/health_score.py) to use **Z-scores** (Standard Deviations from the Mean).
*   **Formula:** `z_score = (merchant_kpi - peer_mean) / peer_std_dev`
*   **Normalization:** Pass the z-score through a Sigmoid curve `1 / (1 + e^(-z))` to gently bound the score between 0 and 100.
*   **Target Files:** [backend/engines/benchmark/health_score.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/benchmark/health_score.py), [backend/engines/benchmark/models/kpi_scorer.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/benchmark/models/kpi_scorer.py)

### 2. Strategy Engine (Bandwidth & Grouping)
Currently limits output to the highest-scoring 5 strategies.

*   **Change:** Overhaul the `StrategyResponse` schema to output multiple "Tracks" instead of a flat list. Tracks will include "Immediate Actions (Quick Wins)", "Long-Term Growth", and "Retention Rescues".
*   **Logic:** The scorer will categorize the top 10-15 strategies into these bands based on confidence scores and category types, giving the merchant a wider bandwidth of options without overwhelming them.
*   **Target Files:** [backend/engines/strategy/schemas.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/strategy/schemas.py), [backend/engines/strategy/service.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/strategy/service.py)

### 3. Feedback Engine (ML Improvements)
Currently statically adjusts weights up or down linearly.

*   **Change:** Implement a **Multi-Armed Bandit (MAB)** algorithm, specifically Upper Confidence Bound (UCB1). 
*   **Logic:** `score = base_weight + C * sqrt(ln(total_plays) / rule_plays)`. This naturally balances exploitation (using proven strategies) with exploration (trying out less-used strategies to see if they work).
*   **Target Files:** [backend/engines/feedback/weight_updater.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/feedback/weight_updater.py)

### 4. Discovery Engine (Enhanced Profiling)
*   **Change:** Add deeply predictive LLM zero-shot classification via Ollama as a fallback if the Scikit-learn models (Maturity/Vertical) return a confidence score below a critical threshold (e.g., < 0.50). This allows identifying "everything about any merchant" accurately.
*   **Target Files:** [backend/engines/discovery/service.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/discovery/service.py)

### 5. Smart Ollama Integration (RAG-based Chat)
*   **Change:** The current [chat.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/api/chat.py) endpoint takes a massive data dump and throws it into the system prompt. We will upgrade this to a smart routing agent.
*   **Logic:** Ollama will be instructed to classify the user's intent. If they ask about "Strategy", the prompt is injected strictly with Strategy data. If they ask about "Peers", it requests Benchmark data. This prevents context-window saturation and hallucination, answering specific merchant queries swiftly.
*   **Target Files:** [backend/api/chat.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/api/chat.py)

---

## Part 2: Architecture, Code Quality & DevOps

### 1. Architecture & Code Quality
*   **Dependency Injection over Singletons:** In [service.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/engines/strategy/service.py) files, controllers are initialized as module-level singletons, which loads ML models at import time. This delays startup and hampers testing. **Improvement:** Migrate these to FastAPI's `Depends()` system. Inject the engines lazily on request, or load them explicitly during the FastAPI [lifespan](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/api/main.py#34-69) and inject them from `app.state`.
*   **Deprecation Fixes:** Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` to future-proof the codebase for Python 3.12+.
*   **Strict Typing & Linting Enforcement:** Add a `.pre-commit-config.yaml` using `ruff` and `pyright`/`mypy` to enforce strict quality standards on every commit.

### 2. CI/CD & DevOps
*   **Continuous Integration Pipeline:** Automate the existing test suites (`tests/unit`, `tests/integration`) by adding a CI workflow (e.g., `.github/workflows/ci.yml`) to run tests and linters on PRs.
*   **Docker Healthchecks:** Add native `healthcheck` blocks to Postgres and Redis in [docker-compose.yml](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/docker-compose.yml), and ensure the `backend` service uses `depends_on: condition: service_healthy`.
*   **Multi-Stage Docker Builds:** Ensure the [Dockerfile](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/Dockerfile) builds cleanly, copying only necessary artifacts to a slim production image.

### 3. MLOps & Data Pipelines
*   **Model Drift & Weight Versioning:** Ensure weight updates in the Feedback Engine are versioned in the database with an audit log so we can rollback if "model drift" degrades recommendation performance.
*   **Async Polling Safety:** Push `model_registry.start_polling()` in [main.py](file:///c:/Users/mites/OneDrive/Desktop/Bravola/Bravola-Project-main/bravola-mini-saas-gemini/backend/api/main.py) into a dedicated background `asyncio.Task` utilizing `asyncio.to_thread` to prevent blocking the async FastAPI event loop.

### 4. Full-stack Connectivity
*   **Automated Frontend Client Generation:** Use an OpenAPI code generator (like `openapi-ts` or `orval`) in your ReactJS frontend repository to automatically generate React Query hooks and logic from FastAPI's `/openapi.json`.

### 5. API Security
*   **Rate Limiting:** Protect ML inference endpoints (e.g., `/engine/v1/strategy/generate`, `/api/v1/chat`) via a rate limiter (e.g., `slowapi`) to prevent abusive usage from exhausting backend AI resources.

---

## Verification Plan

### Automated Tests
*   `test_benchmark_health_score.py` — Update to assert the new Sigmoid Z-score logic bounds outputs (0-100), regardless of outliers.
*   `test_feedback_weight_updater.py` — Add mock data proving the UCB1 algorithm favors high-converting strategies while forcing periodic exploration.

### Manual Verification
*   Boot the docker-compose stack.
*   Post extreme outlier data to `/engine/v1/benchmark/report` to assure engine stability.
*   Test the `/api/v1/chat` endpoint with specific, multi-turn merchant questions to ensure dynamic context routing works perfectly via Ollama.
