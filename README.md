# 🚀 Bravola AI Engine v2.0 — Growth Marketing Brain

> **AI-powered Growth Marketing Strategist Platform for Shopify Merchants**

Bravola encodes the decision-making of a senior growth marketer into 4 AI engine microservices. It analyzes store data, diagnoses performance gaps, recommends marketing campaigns, and learns from results — all at scale.

> [!IMPORTANT]
> **v2.0 Overhaul** — This release includes major upgrades across all engines:
> Winsorized Z-score benchmarking, UCB1 multi-armed bandit feedback, deep merchant profiling with LLM fallback, dynamic crisis response tracks, Ollama intent-routed chat, SSE streaming, and budget-aware strategy scoring. See [Changelog](#-v20-changelog) for full details.

---

## 📐 System Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║                    BRAVOLA SYSTEM ARCHITECTURE                      ║
║                                                                      ║
║  [ReactJS Frontend]  ←── Strategist Dashboard / Merchant Portal      ║
║         │                                                            ║
║  [Node.js API Gateway]                                               ║
║         │                                                            ║
║  [Node.js Microservices]  ◄──── calls ────►  ╔══════════════════╗   ║
║   • Merchant Service                         ║  THIS REPO       ║   ║
║   • Strategy Service       ────calls────►    ║                  ║   ║
║   • Feedback Service       ────calls────►    ║  Python AI       ║   ║
║   • Dashboard Service                        ║  Engines v2      ║   ║
║   • Shopify Connector                        ║  (FastAPI)       ║   ║
║   • Klaviyo Connector                        ╚══════════════════╝   ║
║         │                                          │                 ║
║  [PostgreSQL] ◄─────────────────────────────────── │                 ║
║  [Redis]      ◄─────────────────────────────────── │                 ║
║  [Celery]     ◄─────────────────────────────────── │                 ║
║  [Ollama]     ◄──── Local LLM (llama3.2:3b) ───── │                 ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🧠 The Four AI Engines (Closed-Loop Pipeline)

```
  MERCHANT DATA (PostgreSQL)
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  FEATURE ENGINEERING PIPELINE                                   │
  │  Raw tables → computed features → stored                        │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
              ┌──────────────┘
              │
              ▼
  ┌────────────────────────────┐
  │   1. DISCOVERY ENGINE      │  ← Called once per merchant at onboarding
  │   "Who is this merchant?"  │
  │                            │  Output: persona, vertical, maturity_score,
  │   POST /engine/v1/         │    initial_focus, target_audience, price_tier,
  │        discovery/profile   │    growth_signals, churn_risk, dominant_channel
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │   2. BENCHMARK ENGINE      │  ← Called weekly per merchant
  │   "How are they doing vs   │
  │    similar stores?"        │  Output: health_score, funnel_scores,
  │                            │    gap_flags, peer_percentile (Beta CDF),
  │   POST /engine/v1/         │    health_summary (Ollama narrative),
  │        benchmark/report    │    missing_metrics, percentile_method
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │   3. STRATEGY ENGINE       │  ← Called weekly after Benchmark
  │   "What marketing moves    │
  │    should they make?"      │  Output: 4-track strategy (quick_wins,
  │                            │    core_growth, retention_rescue,
  │   POST /engine/v1/         │    crisis_response), strategy_narrative,
  │        strategy/generate   │    Ollama-personalised descriptions
  └────────────┬───────────────┘
               │  → Human reviews → Klaviyo executes → Results flow back
               ▼
  ┌────────────────────────────┐
  │   4. FEEDBACK ENGINE       │  ← Called after campaign results (~7-14 days)
  │   "Did it work? What do    │
  │    we learn?"              │  Output: UCB1 scores, weight_updates,
  │                            │    exploration_bonus, feedback_summary,
  │   POST /engine/v1/         │    retrain_flag, total_rule_plays
  │        feedback/process    │
  └────────────────────────────┘
               │
               └──► Updated UCB1 scores feed back into Strategy Engine
               └──► retrain_flag=true → Celery triggers retraining
```

---

## 📁 Project Directory Structure

```
bravola-mini-saas-gemini/
│
├── .env                         # Root environment variables (for docker-compose)
├── docker-compose.yml           # All services: postgres, redis, backend, celery, ollama
├── API_TESTING_GUIDE.md         # Complete API testing reference with curl/PowerShell
├── README.md                    # ← You are here
│
└── backend/                     # Python FastAPI Application
    │
    ├── .env                     # Backend-specific env vars
    ├── .env.example             # Template for .env setup
    ├── Dockerfile               # Python 3.10-slim + dependencies
    ├── requirements.txt         # All Python dependencies
    ├── requirements-dev.txt     # Dev/testing dependencies
    ├── alembic.ini              # Alembic migration config
    │
    ├── Docs/
    │   └── implementation_plan.md   # v2 Master Improvement Plan (completed)
    │
    ├── api/                     # FastAPI Application Layer
    │   ├── main.py              # App factory, router registration, CORS, lifespan
    │   ├── chat.py              # 🆕 Smart intent-routed chat + SSE streaming
    │   ├── dependencies.py      # Shared DI: DB session, feature store, model loader
    │   ├── health.py            # GET /health — readiness/liveness probe
    │   └── middleware.py        # Request logging, tenant context, error handling
    │
    ├── engines/                 # 🧠 The 4 AI Engine Modules
    │   │
    │   ├── discovery/           # Engine 1: Merchant Profiling
    │   │   ├── router.py        # POST /engine/v1/discovery/profile
    │   │   ├── schemas.py       # 🆕 Deep profile: target_audience, growth_signals, etc.
    │   │   ├── service.py       # 🆕 LLM fallback for persona & maturity grey zone
    │   │   ├── features.py      # Feature extraction & ordering
    │   │   ├── explainer.py     # SHAP-based reasoning text generator
    │   │   └── models/
    │   │       ├── persona.py   # 🆕 Named-dict features, 6 persona tiers, confidence decay
    │   │       ├── maturity.py  # 🆕 5-component formula (+ email engagement), input validation
    │   │       └── vertical.py  # Random Forest — industry vertical classifier
    │   │
    │   ├── benchmark/           # Engine 2: Performance vs. Peers
    │   │   ├── router.py        # POST /engine/v1/benchmark/report
    │   │   ├── schemas.py       # 🆕 health_summary, missing_metrics, percentile_method
    │   │   ├── service.py       # 🆕 Beta CDF percentile, Ollama health narrative
    │   │   ├── features.py      # KPI feature extraction
    │   │   ├── health_score.py  # 🆕 Winsorized Z-scores, null-safe, opt_in_rate metric
    │   │   ├── explainer.py     # 🆕 generate_health_summary(), fixed median==0 skip
    │   │   └── models/
    │   │       ├── clustering.py  # 🆕 12 named clusters, keyword vertical detection
    │   │       └── kpi_scorer.py  # Linear Regression KPI gap scoring
    │   │
    │   ├── strategy/            # Engine 3: Marketing Strategy Generator ⭐
    │   │   ├── router.py        # POST /engine/v1/strategy/generate
    │   │   ├── schemas.py       # 🆕 crisis_response track, strategy_narrative, totals
    │   │   ├── service.py       # 🆕 Crisis track, fixed category routing, Ollama narrative
    │   │   ├── features.py      # Extract KPI metrics from benchmark output
    │   │   ├── scorer.py        # 🆕 Data-driven MVP lift, budget-aware scoring, 3-key sort
    │   │   ├── personalizer.py  # 🆕 NEW: batch Ollama rewriting of descriptions
    │   │   ├── explainer.py     # Strategy reasoning text generator
    │   │   ├── rules/
    │   │   │   ├── engine.py        # Rule condition evaluator
    │   │   │   ├── loader.py        # Load rules from DB (Excel import)
    │   │   │   └── rules_registry.py # All 29 rules (SSS_4SH Framework)
    │   │   └── models/
    │   │       └── ranker.py    # Learning-to-Rank model (lift predictions)
    │   │
    │   └── feedback/            # Engine 4: Learning from Results
    │       ├── router.py        # POST /engine/v1/feedback/process
    │       ├── schemas.py       # 🆕 UCB1 fields, merchant_context, feedback_summary
    │       ├── service.py       # 🆕 Cluster-aware classification, UCB1 data in response
    │       ├── classifier.py    # 🆕 5-signal voting, cluster-adaptive baselines
    │       ├── weight_updater.py  # 🆕 Full UCB1 MAB: plays, rewards, exploration bonus
    │       └── retrain_trigger.py # Threshold check → Celery task dispatch
    │
    ├── pipelines/               # Data & ML Pipelines
    │   ├── feature_engineering/
    │   │   ├── merchant_features.py    # customers_360 + orders → features
    │   │   ├── engagement_features.py  # campaign_performance → email features
    │   │   ├── peer_features.py        # Peer-normalized features
    │   │   └── feast_push.py           # Push features to Feast store
    │   └── retraining/
    │       ├── celery_app.py    # Celery app configuration
    │       └── tasks.py         # Celery retrain tasks per engine
    │
    ├── shared/                  # Cross-cutting Infrastructure
    │   ├── config.py            # 🆕 UCB1_C, OLLAMA_TIMEOUT, temperature configs
    │   ├── ollama_client.py     # 🆕 temperature param, classify_intent(), streaming
    │   ├── db.py                # Async SQLAlchemy engine, session, DI
    │   ├── feature_store.py     # Feast client wrapper
    │   ├── model_registry.py    # MLflow client wrapper (load/register/promote)
    │   ├── schemas.py           # Shared Pydantic base schemas
    │   ├── logging.py           # Structured JSON logging (structlog)
    │   └── exceptions.py        # Custom exception types
    │
    ├── alembic/                 # Database Migrations
    │   ├── env.py               # Migration environment setup
    │   ├── script.py.mako       # Migration script template
    │   └── versions/            # Migration version files
    │
    └── tests/                   # Test Suite
        ├── conftest.py          # Shared fixtures & test config
        ├── fixtures/
        │   └── sample_merchant_features.json
        ├── unit/
        │   ├── test_discovery_service.py
        │   ├── test_benchmark_health_score.py
        │   ├── test_strategy_rules.py
        │   ├── test_strategy_scorer.py
        │   └── test_feedback_weight_updater.py
        └── integration/
            └── test_endpoints.py  # End-to-end pipeline tests
```

---

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.10** | Runtime |
| **FastAPI** | Async web framework with auto OpenAPI docs |
| **Pydantic v2** | Type-safe I/O validation for all API contracts |
| **SQLAlchemy (async)** | PostgreSQL ORM with async support |
| **Scikit-learn** | Core ML models (LogReg, KMeans, RF) |
| **XGBoost** | Gradient boosting for persona classification |
| **SciPy** | Beta CDF for peer percentile estimation |
| **Ollama** | Local LLM integration (intent routing, reasoning, personalisation) |
| **Celery + Redis** | Async task queue for background retraining |
| **PostgreSQL 15** | Primary data store |
| **Redis 7** | Celery broker + caching |
| **Alembic** | Database migration management |
| **Structlog** | Structured JSON logging |
| **Docker** | Containerized deployment |
| **Pytest** | Unit + integration testing |

---

## 🏗️ Strategy Engine — 29-Rule Framework (SSS_4SH)

The Strategy Engine uses a production rule set extracted from client Excel frameworks:

| Category | Weight | Rules | IDs |
|---|---|---|---|
| **Revenue** | 40% | 8 rules | REV-01 → REV-08 |
| **Audience Growth** | 30% | 6 rules | AUD-01 → AUD-06 |
| **Audience Engagement** | 15% | 8 rules | ENG-01 → ENG-08 |
| **Email Engagement** | 15% | 7 rules | OPEN-01 → OPEN-07 |

### v2 Scoring Formula

```
strategy_score = (global_weight × W_rule)
               + (model_lift_score × W_model)
               - (confidence_penalty × W_penalty)

Default weights: W_rule=0.5, W_model=0.3, W_penalty=0.2
(Tuned dynamically by the Feedback Engine's UCB1 system)
```

#### v2 Improvements:
- **Data-driven MVP lift**: `lift = 0.3 + (global_weight × 0.5) + (normalised_weight × 0.2)` — replaces hardcoded `0.5`
- **Budget-aware scoring**: Low budget penalises `audience_growth` × 0.75, boosts `email_engagement` × 1.05; High budget boosts `revenue` × 1.10
- **3-key deterministic sort**: Primary: `strategy_score` DESC → Secondary: `base_weight` DESC → Tertiary: `rule_id` ASC

---

## 🔄 UCB1 Multi-Armed Bandit (Feedback Engine)

v2 replaces simple proportional weight updates with a full UCB1 implementation:

```
UCB1_score = (cumulative_reward / plays) + C × sqrt(ln(total_plays) / plays)

C = 1.414 (sqrt(2), configurable via UCB1_C setting)
```

| Signal | Reward |
|---|---|
| `success` | +1.0 |
| `neutral` | +0.5 |
| `failure` | +0.0 |

The UCB1 exploration bonus ensures under-tested strategies get periodic re-evaluation, preventing the system from converging prematurely on a few "safe" rules.

---

## 🤖 Ollama AI Integration

v2 adds intelligent Ollama usage across all engines:

| Feature | Engine | Temperature | Purpose |
|---|---|---|---|
| **Intent Classification** | Chat | 0.1 | Route queries to correct context section |
| **Deep Profile Enrichment** | Discovery | 0.1 | Extract 11-key merchant JSON profile |
| **Health Narrative** | Benchmark | 0.7 | Narrative paragraph about merchant standing |
| **Strategy Personalisation** | Strategy | 0.4 | Batch-rewrite descriptions for merchant context |
| **Chat Reasoning** | Chat | 0.8 | Conversational merchant-facing responses |
| **Feedback Summary** | Feedback | 0.7 | Brief insight on campaign outcome |
| **SSE Streaming** | Chat | 0.8 | Token-by-token streaming responses |

All features gracefully fall back to heuristic/deterministic output when Ollama is unavailable.

---

## 📊 Peer Clustering — 12 Named Clusters

v2 expands from 4 clusters to **12 named clusters** with maturity tiers:

| Vertical | Low | Mid | High |
|---|---|---|---|
| Beauty / Cosmetics | ✅ | ✅ | ✅ |
| Apparel / Fashion | ✅ | ✅ | ✅ |
| Food & Beverage | — | ✅ | ✅ |
| Electronics / Tech | — | ✅ | — |
| Health & Wellness | — | ✅ | — |
| Home Goods / Furniture | — | ✅ | — |
| Pet Supplies | — | ✅ | — |
| General / Other | ✅ | ✅ | — |

Each cluster has curated **medians** and **standard deviations** for 9 KPI metrics sourced from Klaviyo and Shopify benchmark studies.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git
- (Optional) Ollama for LLM-powered features — `ollama pull llama3.2:3b`

### 1. Clone & configure
```bash
git clone <repo-url>
cd bravola-mini-saas-gemini

# Edit .env file with your required configuration variables
# Make sure Ollama is accessible (default: http://ollama:11434)
```

### 2. Start all services
```bash
docker-compose up --build -d
```

This starts:
| Service | Port | Description |
|---|---|---|
| `bravola-backend` | `8000` | FastAPI AI Engine v2 |
| `bravola-postgres` | `5432` | PostgreSQL database |
| `bravola-redis` | `6379` | Redis cache/broker |
| `bravola-celery-worker` | — | Background retraining |
| `bravola-celery-beat` | — | Scheduled task scheduler |

### 3. Verify
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Check Ollama availability (optional)
curl http://localhost:8000/api/v1/chat/status
```

---

## 🔌 API Endpoints

| Method | Endpoint | Engine | Purpose |
|---|---|---|---|
| `GET` | `/health` | — | Readiness/liveness probe |
| `GET` | `/docs` | — | Interactive Swagger UI |
| `POST` | `/engine/v1/discovery/profile` | Discovery | Profile a merchant (deep profile) |
| `POST` | `/engine/v1/benchmark/report` | Benchmark | Score vs. peer group (Winsorized Z) |
| `POST` | `/engine/v1/strategy/generate` | Strategy | Generate 4-track ranked strategies |
| `POST` | `/engine/v1/feedback/process` | Feedback | Process results (UCB1 learning) |
| `POST` | `/api/v1/chat` | Chat | Intent-routed merchant chat |
| `POST` | `/api/v1/chat/stream` | Chat | SSE streaming chat |
| `GET` | `/api/v1/chat/status` | Chat | Ollama health check |

### Example: Discovery Engine (v2 Response)

```json
// POST /engine/v1/discovery/profile
{
  "merchant_id": "uuid",
  "feature_vector": {
    "avg_order_value": 87.50,
    "repeat_rate": 0.18,
    "days_to_second_purchase": 32,
    "product_concentration": 0.61,
    "email_engagement_score": 0.24,
    "total_customer_count": 3420,
    "revenue_last_90d": 148000.00,
    "revenue_last_30d": 51000.00
  },
  "onboarding_responses": {
    "vertical_hint": "beauty",
    "goal_hint": "retention",
    "price_hint": "premium",
    "audience_hint": "Women 25-45 skincare enthusiasts",
    "primary_challenge": "High cart abandonment"
  }
}

// v2 Response — Full Deep Profile
{
  "merchant_id": "uuid",
  "persona": "loyalist",
  "vertical": "beauty",
  "seasonality": "high",
  "catalog_complexity": "medium",
  "maturity_score": 72,
  "initial_focus": "engagement",
  "confidence_score": 0.89,
  "reasoning": "High repeat rate (18%) and strong 90-day revenue...",
  "target_audience": "Women 25-45 interested in premium skincare",
  "price_point_tier": "premium",
  "key_value_proposition": "Clean, sustainable formulations with proven results",
  "growth_signals": ["Rising repeat rate", "Growing email list", "Strong LTV"],
  "dominant_channel": "email",
  "churn_risk_level": "low",
  "model_version": "discovery-v2",
  "generated_at": "2026-03-30T08:00:00.000000+00:00"
}
```

### Example: Benchmark Engine (v2 Response)

```json
// v2 Response — Winsorized Z-Score + Ollama Narrative
{
  "merchant_id": "uuid",
  "health_score": 62,
  "funnel_scores": {
    "acquisition": 70,
    "conversion": 55,
    "retention": 40
  },
  "peer_percentile": 58,
  "percentile_method": "sigmoid_z_beta",
  "peer_cluster_id": "beauty-mid-us",
  "gap_flags": [
    "Repeat Purchase Rate is 28.0% below peer median (32.0%)",
    "Cart Abandonment Rate is 12.5% above peer median (56.0%)"
  ],
  "missing_metrics": ["opt_in_rate"],
  "health_summary": "This beauty merchant scores 62/100, performing below their mid-tier peers...",
  "kpi_snapshot": { "repeat_purchase_rate": 0.22, "..." : "..." },
  "model_version": "benchmark-v2",
  "generated_at": "2026-03-30T08:05:00.000000+00:00"
}
```

### Example: Strategy Engine (v2 Response with Crisis Track)

```json
// v2 Response — 4-Track Strategy with Ollama Personalisation
{
  "merchant_id": "uuid",
  "strategy_batch_id": "batch_abc123",
  "tracks": {
    "quick_wins": [ { "rule_id": "REV-01", "..." : "..." } ],
    "core_growth": [ { "rule_id": "AUD-02", "..." : "..." } ],
    "retention_rescue": [ { "rule_id": "ENG-05", "..." : "..." } ],
    "crisis_response": [ { "rule_id": "REV-03", "..." : "..." } ]
  },
  "strategy_narrative": "⚠️ Crisis mode: 15 strategies evaluated for this beauty merchant...",
  "total_triggered": 15,
  "tracks_populated": 4,
  "model_version": "strategy-v2",
  "generated_at": "2026-03-30T08:10:00.000000+00:00"
}
```

### Example: Feedback Engine (v2 Response with UCB1)

```json
// v2 Response — UCB1 Multi-Armed Bandit
{
  "merchant_id": "uuid",
  "strategy_id_code": "STR-01",
  "performance_label": "success",
  "weight_updates": [
    {
      "rule_id": "REV-01",
      "old_weight": 0.500,
      "new_weight": 0.525,
      "adjustment": 0.025,
      "ucb1_score": 1.9142,
      "exploration_bonus": 0.4142,
      "total_rule_plays": 3
    }
  ],
  "retrain_triggered": false,
  "feedback_event_count": 7,
  "feedback_summary": "Strategy STR-01 (rule REV-01) exceeded expectations...",
  "model_version": "feedback-v2",
  "generated_at": "2026-03-30T08:15:00.000000+00:00"
}
```

---

## 🧪 Running Tests

```bash
# From backend directory
cd backend

# Unit tests
python -m pytest tests/unit/ -v

# Integration tests (full pipeline)
python -m pytest tests/integration/ -v

# All tests with coverage
python -m pytest tests/ -v --cov=engines --cov=shared

# Specific engine tests
python -m pytest tests/unit/test_benchmark_health_score.py -v   # Winsorization + null handling
python -m pytest tests/unit/test_feedback_weight_updater.py -v  # UCB1 implementation
python -m pytest tests/unit/test_discovery_service.py -v        # Deep profiling
python -m pytest tests/unit/test_strategy_scorer.py -v          # Budget-aware scoring
```

---

## 📊 Docker Services Architecture

```
docker-compose.yml
│
├── postgres (PostgreSQL 15-alpine)
│   └── Port 5432 │ Volume: postgres_data
│
├── redis (Redis 7-alpine)
│   └── Port 6379 │ Volume: redis_data
│
├── backend (Python FastAPI)
│   ├── Port 8000
│   ├── Runs: alembic upgrade head → uvicorn
│   └── Depends on: postgres ✓, redis ✓
│
├── celery_worker
│   ├── Runs: celery worker (concurrency=4)
│   └── Depends on: postgres ✓, redis ✓
│
└── celery_beat
    ├── Runs: celery beat scheduler
    └── Depends on: redis ✓

Network: bravola_network (bridge)
```

---

## 🔒 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SECRET_KEY` | — | JWT signing key (change in prod!) |
| `ML_ARTIFACTS_PATH` | `./ml_artifacts` | Path to ML model artifacts |
| `MODEL_VERSION` | `v2` | Current model version tag |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama LLM service URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model to use |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | Ollama request timeout |
| `OLLAMA_TEMPERATURE_JSON` | `0.1` | Temperature for JSON extraction |
| `OLLAMA_TEMPERATURE_REASONING` | `0.7` | Temperature for reasoning |
| `OLLAMA_TEMPERATURE_CHAT` | `0.8` | Temperature for merchant chat |
| `MAX_STRATEGIES` | `5` | Max strategies per generation (legacy) |
| `MAX_STRATEGIES_PER_TRACK` | `5` | Max items per strategy track |
| `TOTAL_STRATEGY_CANDIDATES` | `20` | Max rules evaluated before trimming |
| `W_RULE` / `W_MODEL` / `W_PENALTY` | `0.5 / 0.3 / 0.2` | Strategy scoring weights |
| `LEARNING_RATE` | `0.05` | Feedback weight update rate |
| `RETRAIN_THRESHOLD` | `20` | Feedback count to trigger retrain |
| `UCB1_C` | `1.414` | UCB1 exploration constant (√2) |

---

## 📋 v2.0 Changelog

### Phase 1: Benchmark Math
- ✅ Winsorized Z-scores (clip at ±2σ before scoring)
- ✅ Null/missing metric handling (substitute peer mean → neutral Z-score)
- ✅ 4th acquisition metric: `opt_in_rate` (email list growth)
- ✅ 12 named peer clusters (was 4)
- ✅ Keyword-based vertical matching (7 vertical categories)
- ✅ Beta CDF percentile estimation (SciPy)
- ✅ Ollama-powered `health_summary` narrative
- ✅ Fixed `median_val == 0` silent skip in gap flags

### Phase 2: Feedback UCB1
- ✅ Full UCB1 Multi-Armed Bandit implementation
- ✅ Play counting (`record_play()`, `get_all_ucb1_scores()`)
- ✅ Reward accumulation with proper exploitation/exploration balance
- ✅ 5-signal voting classifier (added `list_growth_rate`)
- ✅ Cluster-adaptive baselines (6 vertical-specific baseline sets)
- ✅ UCB1 scores + exploration bonus in API response

### Phase 3: Discovery Deep Profiling
- ✅ 11-key LLM enrichment JSON (target_audience, price_tier, growth_signals, etc.)
- ✅ LLM fallback for persona when confidence < 0.55
- ✅ LLM fallback for maturity in grey zone (35-65)
- ✅ 6 persona tiers (added `discount_driven`, `high_value_whales`)
- ✅ Named-dict feature access (replaces fragile index-based `features[0]`)
- ✅ Confidence decay when features are missing/zero
- ✅ 5-component maturity formula (added email engagement)
- ✅ Input validation (clamp all inputs to non-negative)

### Phase 4: Strategy Engine
- ✅ **Fixed critical bug**: category routing now uses exact enum values (`email_engagement` not `"Email"`)
- ✅ Dynamic **Crisis Response** track (triggers on health < 40 or 3+ gap flags)
- ✅ Ollama strategy personaliser (`personalizer.py`) — single batch call for all items
- ✅ Ollama `strategy_narrative` — executive summary
- ✅ Data-driven MVP lift estimation (replaces hardcoded 0.5)
- ✅ Budget-aware scoring adjustments
- ✅ 3-key deterministic sort (score → weight → rule_id)

### Phase 5: Smart Ollama Chat
- ✅ 2-step intent routing pipeline (classify → inject relevant context)
- ✅ 5 intent categories with context extractors
- ✅ SSE streaming endpoint (`/api/v1/chat/stream`)
- ✅ Merchant-specific system prompt with health context
- ✅ Temperature parameter on `generate()` and `chat()`

### Phase 6: Config & Architecture
- ✅ All new config params (`UCB1_C`, `OLLAMA_TIMEOUT_SECONDS`, temperature configs)
- ✅ `datetime.utcnow()` → `datetime.now(timezone.utc)` across all files
- ✅ `MODEL_VERSION` bumped to `v2`

---

## 🔮 Future Roadmap

1. **Persistent Weight Store**: Migrate UCB1 state from in-memory dicts to PostgreSQL `rule_weights` table
2. **Streaming Chat Frontend**: Update React frontend to use EventSource for `/api/v1/chat/stream`
3. **Model Drift Monitoring**: Weekly Celery task to alert on declining UCB1 reward rates
4. **Merchant Analytics Dashboard**: `/api/v1/analytics/{merchant_id}/summary` aggregating all engines
5. **A/B Testing Module**: 10% holdout control group for statistical significance
6. **Rate Limiting**: `slowapi` on `/engine/v1/strategy/generate` and `/api/v1/chat`
7. **OpenAPI Client Generation**: Auto-generate React Query hooks from `/engine/openapi.json`

---

## 📝 License

Proprietary — Bravola Inc.
