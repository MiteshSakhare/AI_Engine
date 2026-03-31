# 🤖 Bravola AI Engine — Python Microservices Implementation Plan

**Role:** AI Engine Developer (Python)
**Scope:** Build all 4 AI Engine microservices that power the Bravola Growth Marketing Brain
**Stack:** Python · FastAPI · Scikit-learn · XGBoost · Feast · MLflow · Celery · PostgreSQL · Redis

---

## Table of Contents

1. [Project Context — What Bravola Is](#1-project-context)
2. [Your Role in the Bigger System](#2-your-role-in-the-bigger-system)
3. [What You Are Building](#3-what-you-are-building)
4. [How the Engines Work Together](#4-how-the-engines-work-together)
5. [Project Folder Structure](#5-project-folder-structure)
6. [Technology Stack & Rationale](#6-technology-stack--rationale)
7. [Engine 1 — Discovery Engine](#7-engine-1--discovery-engine)
8. [Engine 2 — Benchmark Engine](#8-engine-2--benchmark-engine)
9. [Engine 3 — Strategy Engine](#9-engine-3--strategy-engine)
10. [Engine 4 — Feedback Engine](#10-engine-4--feedback-engine)
11. [Shared Infrastructure Plan](#11-shared-infrastructure-plan)
12. [Data Contracts with Node.js Team](#12-data-contracts-with-nodejs-team)
13. [ML Pipeline Plan](#13-ml-pipeline-plan)
14. [Feature Engineering Plan](#14-feature-engineering-plan)
15. [Model Training Plan](#15-model-training-plan)
16. [Model Serving Plan](#16-model-serving-plan)
17. [Testing Plan](#17-testing-plan)
18. [Sprint-by-Sprint Build Plan](#18-sprint-by-sprint-build-plan)
19. [Dependencies & Blockers](#19-dependencies--blockers)
20. [Definition of Done](#20-definition-of-done)

---

## 1. Project Context

### What is Bravola?

Bravola is an **AI Growth Marketing Strategist Platform** — a multi-tenant SaaS product that serves Shopify merchants. The platform automates what a human growth marketing strategist does: analyze a store's data, diagnose performance gaps, recommend the right marketing campaigns, execute those campaigns via Klaviyo, and learn from results over time.

The business problem it solves: a skilled human growth marketing strategist is expensive and limited in scale. Bravola encodes that expertise into software so it can serve hundreds of merchants simultaneously with the same quality of thinking.

### The Core Concept — "Growth Marketer's Brain"

The platform has four AI engines working in a closed loop that together simulate the decision-making of a senior growth marketer:

```
MERCHANT JOINS BRAVOLA
        │
        ▼
[ DISCOVERY ENGINE ]   "Who is this merchant? What stage are they at?"
        │
        ▼
[ BENCHMARK ENGINE ]   "How are they performing vs. similar stores?"
        │
        ▼
[ STRATEGY ENGINE ]    "What marketing moves should they make right now?"
        │
        ▼
[ HUMAN REVIEW ]       Strategist reviews, approves, or overrides
        │
        ▼
[ KLAVIYO EXECUTES ]   Campaign runs on the merchant's audience
        │
        ▼
[ FEEDBACK ENGINE ]    "Did it work? What should we learn from this?"
        │
        └──────────────────► Updates Strategy Engine (loop)
```

### Who Builds What?

| Team | What they build |
|---|---|
| **ReactJS Team** | Strategist Dashboard (review + approve strategies), Merchant Portal (onboarding, health view) |
| **Node.js Team** | API Gateway, all domain microservices (Merchant, Strategy, Feedback, Dashboard), Shopify Connector, Klaviyo Connector |
| **You (Python Team)** | The 4 AI Engines — the brain of the entire platform |

The Node.js team calls your Python FastAPI endpoints. You do not build any user-facing UI or any Shopify/Klaviyo integration. You receive cleaned data and return intelligent decisions.

---

## 2. Your Role in the Bigger System

### Where You Sit in the Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                  FULL SYSTEM ARCHITECTURE                        ║
║                                                                  ║
║  [ReactJS Frontend]                                              ║
║         │                                                        ║
║  [Node.js API Gateway]                                           ║
║         │                                                        ║
║  [Node.js Microservices]  ◄──── calls ────►  ╔══════════════╗   ║
║   • Merchant Service                         ║  YOUR SCOPE  ║   ║
║   • Strategy Service       ────calls────►    ║              ║   ║
║   • Feedback Service       ────calls────►    ║  Python AI   ║   ║
║   • Dashboard Service                        ║  Engines     ║   ║
║   • Shopify Connector                        ║  (FastAPI)   ║   ║
║   • Klaviyo Connector                        ╚══════════════╝   ║
║         │                                          │            ║
║  [PostgreSQL] ◄─────────────────────────────────── │            ║
║  [Redis]      ◄─────────────────────────────────── │            ║
║  [Feast]      ◄─────────────────────────────────── │            ║
║  [MLflow]     ◄─────────────────────────────────── │            ║
╚══════════════════════════════════════════════════════════════════╝
```

### What the Node.js Team Gives You (Inputs)

The Node.js team handles all Shopify and Klaviyo communication. By the time they call your engine, data is already:
- Cleaned and normalized in PostgreSQL tables (`customers_360`, `orders_enriched`, `campaign_performance`, `human_override_logs`)
- Available in the Feast feature store as engineered features
- Structured as a well-defined JSON payload (agreed API contract)

Your engines receive structured JSON → process → return structured JSON.

### What You Give the Node.js Team (Outputs)

Every engine returns a structured JSON object with:
- The decision/prediction
- A confidence score
- A human-readable reasoning string
- The model version that produced it

No vague text. No unstructured outputs. Everything is machine-readable and auditable.

---

## 3. What You Are Building

Four Python FastAPI microservices, each representing one AI engine. They can run as separate Docker containers or as modules within a single FastAPI app (recommended for MVP simplicity).

| Engine | Service Name | Core Task | ML Type |
|---|---|---|---|
| Discovery Engine | `discovery-engine` | Profile the merchant (persona, vertical, maturity) | Classification + Regression |
| Benchmark Engine | `benchmark-engine` | Score performance vs. peer group | Clustering + Regression |
| Strategy Engine | `strategy-engine` | Generate ranked marketing strategies | Rule Engine + Learning-to-Rank |
| Feedback Engine | `feedback-engine` | Learn from outcomes, update rule weights | Weight Optimization + Retrain triggers |

Additionally, you build:
- Shared ETL / feature pipelines (PostgreSQL → Feast)
- Model training scripts (offline, run via Celery workers)
- Model retraining job infrastructure (Celery + MLflow)

---

## 4. How the Engines Work Together

### Full Data & Signal Flow

```
  MERCHANT DATA (PostgreSQL)
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  FEATURE ENGINEERING PIPELINE                                   │
  │  Raw tables → computed features → pushed to Feast               │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
              ┌──────────────┘
              │
              ▼
  ┌──────────────────────────┐
  │   DISCOVERY ENGINE       │  ← Called once per merchant on onboarding completion
  │                          │    Re-run if merchant data significantly changes
  │  Input:  merchant_id     │
  │  + feature vector        │
  │  + onboarding answers    │
  │                          │
  │  Output: persona_label   │
  │          vertical_label  │
  │          maturity_score  │
  │          initial_focus   │
  └────────────┬─────────────┘
               │  output passed as input to ↓
               ▼
  ┌──────────────────────────┐
  │   BENCHMARK ENGINE       │  ← Called weekly per merchant
  │                          │
  │  Input:  merchant_id     │
  │  + KPI metrics           │
  │  + discovery output      │
  │  + peer context          │
  │                          │
  │  Output: health_score    │
  │          funnel_scores   │
  │          gap_flags       │
  │          peer_percentile │
  └────────────┬─────────────┘
               │  output passed as input to ↓
               ▼
  ┌──────────────────────────┐
  │   STRATEGY ENGINE        │  ← Called weekly per merchant (after Benchmark)
  │                          │
  │  Input:  merchant_id     │
  │  + discovery output      │
  │  + benchmark output      │
  │  + constraints           │
  │  + available channels    │
  │                          │
  │  Output: [ strategy      │
  │            objects ]     │
  └────────────┬─────────────┘
               │
               │  → Node.js saves strategies to DB
               │  → Human Strategist reviews/approves
               │  → Klaviyo executes campaigns
               │  → Campaign performance flows back
               ▼
  ┌──────────────────────────┐
  │   FEEDBACK ENGINE        │  ← Called after campaign results are available (~7–14 days)
  │                          │
  │  Input:  merchant_id     │
  │  + strategy_id           │
  │  + campaign performance  │
  │  + human_action          │
  │                          │
  │  Output: weight_updates  │
  │          retrain_flag    │
  │          next_cycle_hint │
  └──────────────────────────┘
          │
          └──────► Updated weights feed back into Strategy Engine (next run)
          └──────► If retrain_flag=true → Celery worker triggers retraining job
```

---

## 5. Project Folder Structure

```
bravola-ai/
│
├── README.md
├── pyproject.toml               # Project dependencies (Poetry or pip)
├── requirements.txt
├── .env.example                 # Environment variable template
├── docker-compose.yml           # For local dev (all 4 engines + dependencies)
├── Dockerfile                   # Single Dockerfile for all engines
│
├── api/
│   ├── main.py                  # FastAPI app — all 4 engines registered here
│   ├── dependencies.py          # Shared DI: DB session, feature store client, model loader
│   ├── health.py                # /health endpoint for all engines
│   └── middleware.py            # Request logging, tenant context injection, error handling
│
├── engines/
│   │
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── router.py            # FastAPI router: POST /engine/discovery/profile
│   │   ├── schemas.py           # Pydantic input/output schemas
│   │   ├── service.py           # Orchestrates feature fetch + model inference
│   │   ├── features.py          # Feature extraction from Feast / PostgreSQL
│   │   ├── models/
│   │   │   ├── persona.py       # Persona classifier (XGBoost)
│   │   │   ├── maturity.py      # Maturity scorer (Logistic Regression)
│   │   │   └── vertical.py      # Vertical classifier (Random Forest)
│   │   ├── explainer.py         # SHAP-based reasoning text generator
│   │   └── train/
│   │       ├── train_persona.py
│   │       ├── train_maturity.py
│   │       └── train_vertical.py
│   │
│   ├── benchmark/
│   │   ├── __init__.py
│   │   ├── router.py            # POST /engine/benchmark/report
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── features.py
│   │   ├── models/
│   │   │   ├── clustering.py    # K-Means peer grouping
│   │   │   ├── kpi_scorer.py    # Linear Regression KPI gap scoring
│   │   │   └── anomaly.py      # Isolation Forest (optional)
│   │   ├── health_score.py      # Health score formula implementation
│   │   ├── explainer.py
│   │   └── train/
│   │       ├── train_clusters.py
│   │       └── train_kpi_scorer.py
│   │
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── router.py            # POST /engine/strategy/generate
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── features.py
│   │   ├── rules/
│   │   │   ├── engine.py        # Rule matching logic
│   │   │   ├── loader.py        # Load rules from DB (imported from Excel)
│   │   │   └── rules_registry.py  # All rule definitions (REV-01, ENG-02, etc.)
│   │   ├── models/
│   │   │   └── ranker.py        # Learning-to-Rank model
│   │   ├── scorer.py            # strategy_score formula
│   │   ├── explainer.py
│   │   └── train/
│   │       └── train_ranker.py
│   │
│   ├── feedback/
│   │   ├── __init__.py
│   │   ├── router.py            # POST /engine/feedback/process
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── classifier.py        # Performance classifier (success/neutral/failure)
│   │   ├── weight_updater.py    # Rule weight adjustment logic
│   │   └── retrain_trigger.py   # Threshold check → Celery task dispatch
│
├── pipelines/
│   │
│   ├── etl/
│   │   ├── shopify_to_postgres.py    # (Interface only — Node.js team owns this)
│   │   ├── klaviyo_to_postgres.py    # (Interface only — Node.js team owns this)
│   │   └── README.md                # Documents expected table schemas
│   │
│   ├── feature_engineering/
│   │   ├── merchant_features.py     # customers_360 + orders_enriched → features
│   │   ├── engagement_features.py   # campaign_performance → email features
│   │   ├── peer_features.py         # Peer-normalized features (gap to cluster median)
│   │   └── feast_push.py            # Write computed features to Feast online + offline store
│   │
│   └── retraining/
│       ├── tasks.py                 # Celery task definitions (retrain per engine)
│       ├── celery_app.py            # Celery app configuration
│       ├── retrain_discovery.py
│       ├── retrain_benchmark.py
│       ├── retrain_strategy.py
│       └── evaluate.py             # Shared evaluation utilities
│
├── shared/
│   ├── db.py                    # SQLAlchemy async DB connection + session
│   ├── feature_store.py         # Feast client wrapper (get_online_features)
│   ├── model_registry.py        # MLflow client wrapper (load, register, promote)
│   ├── schemas.py               # Shared Pydantic base schemas
│   ├── logging.py               # Structured JSON logging (structlog)
│   ├── config.py                # Settings via Pydantic BaseSettings
│   └── exceptions.py            # Custom exception types
│
└── tests/
    ├── conftest.py              # Fixtures (mock DB, mock feature store, mock models)
    ├── unit/
    │   ├── test_discovery_service.py
    │   ├── test_benchmark_service.py
    │   ├── test_strategy_rules.py
    │   ├── test_strategy_scorer.py
    │   └── test_feedback_weight_updater.py
    ├── integration/
    │   ├── test_discovery_endpoint.py
    │   ├── test_benchmark_endpoint.py
    │   ├── test_strategy_endpoint.py
    │   └── test_feedback_endpoint.py
    └── fixtures/
        ├── sample_merchant_features.json
        ├── sample_benchmark_report.json
        └── sample_strategy_output.json
```

---

## 6. Technology Stack & Rationale

| Technology | Purpose | Why |
|---|---|---|
| **Python 3.11** | Runtime | Best ML ecosystem, async support |
| **FastAPI** | Web framework | Async, auto OpenAPI docs, Pydantic native |
| **Pydantic v2** | Data validation / schemas | Type-safe I/O contracts |
| **SQLAlchemy (async)** | PostgreSQL ORM | Async DB access for FastAPI |
| **Scikit-learn** | Core ML models | Mature, interpretable, fast training |
| **XGBoost** | Gradient boosting | Best performance for tabular data |
| **SHAP** | Model explainability | Feature importance → human reasoning |
| **Feast** | Feature store | Consistent features between training & serving |
| **MLflow** | Model registry | Versioning, experiment tracking, promotion |
| **Celery** | Async task queue | Background retraining jobs |
| **Redis** | Celery broker + cache | Low-latency, used by rest of system too |
| **Pandas / NumPy** | Feature engineering | Standard data manipulation |
| **Pytest** | Testing | Fixtures, async test support |
| **Structlog** | Structured logging | JSON logs for Grafana/Loki ingestion |
| **Docker** | Containerization | Consistent dev + prod environments |

**What we are NOT using:**
- No LLMs (OpenAI, Anthropic, Ollama) — all models are domain-specific classical ML
- No heavy deep learning frameworks (TensorFlow, PyTorch) — not needed for tabular data
- No black-box AutoML — all models are hand-designed for explainability

---

## 7. Engine 1 — Discovery Engine

### Purpose
Answer: **"Who is this merchant, and what stage of growth are they at?"**

Runs once per merchant at onboarding completion. Can be re-run if the merchant's profile changes significantly (e.g., after 90 days of data accumulates).

### What It Does

Takes merchant feature data and Lola chatbot onboarding answers → returns a structured merchant profile used by all downstream engines.

### Input Data

```
Sources:
  - customers_360 table        → order + customer behavioral metrics
  - orders_enriched table      → revenue, product, order sequence data
  - onboarding_sessions table  → Lola chatbot qualifying answers (goals, context)
  - Feast online store         → pre-computed feature vector for this merchant_id
```

**Features used:**

| Feature | Description | Source |
|---|---|---|
| `avg_order_value` | Mean order value across all orders | orders_enriched |
| `repeat_rate` | % of customers who ordered more than once | customers_360 |
| `days_to_second_purchase` | Median days between 1st and 2nd order | customers_360 |
| `product_concentration` | Top 3 SKUs as % of total revenue | orders_enriched |
| `email_engagement_score` | Composite: `0.6 * open_rate + 0.4 * click_rate` | campaign_performance |
| `total_customer_count` | Total unique customers | customers_360 |
| `revenue_last_90d` | Rolling 90-day revenue | orders_enriched |
| `revenue_last_30d` | Rolling 30-day revenue | orders_enriched |
| `onboarding_vertical_hint` | Merchant's stated industry (from Lola) | onboarding_sessions |
| `onboarding_goal_hint` | Merchant's stated growth goal | onboarding_sessions |

### Models to Build

**Model A — Persona Classifier**
- Algorithm: XGBoost (GradientBoostingClassifier)
- Task: Multi-class classification
- Labels: `loyalist` | `value_seeker` | `explorer` | `bargain_hunter`
- Output: `{ persona_label, persona_confidence }`
- Metric: F1-macro > 0.75

**Model B — Maturity Scorer**
- Algorithm: Logistic Regression (calibrated to produce probabilities)
- Task: Regression (0–100 scale)
- Logic: Calibrated probability → multiply by 100 → maturity_score
- Output: `{ maturity_score: int }`
- Metric: MAE < 8 points

**Model C — Vertical Classifier**
- Algorithm: Random Forest
- Task: Multi-class classification
- Labels: `beauty` | `apparel` | `food` | `home` | `pet` | `sports` | `other`
- Uses `onboarding_vertical_hint` as a strong prior feature
- Output: `{ vertical_label, vertical_confidence }`
- Metric: Top-1 accuracy > 0.80

### API Contract

```
Endpoint: POST /engine/discovery/profile

Request:
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
    "goal_hint": "retention"
  }
}

Response:
{
  "merchant_id": "uuid",
  "persona": "loyalist",
  "vertical": "beauty",
  "maturity_score": 72,
  "initial_focus": "retention",
  "confidence_score": 0.89,
  "reasoning": "High repeat rate (18%) and strong 90-day revenue signals a loyalist customer base. Maturity score of 72 reflects an established store with clear retention opportunity.",
  "model_version": "discovery-v1.2",
  "generated_at": "2025-01-01T12:00:00Z"
}
```

### Internal Logic Flow

```
POST /engine/discovery/profile
         │
         ▼
Validate request (Pydantic)
         │
         ▼
Load feature vector from Feast online store
(or use feature_vector from request if provided)
         │
         ▼
Run Model A (XGBoost) → persona_label + confidence
Run Model B (LogReg)  → maturity_score
Run Model C (RF)      → vertical_label + confidence
         │
         ▼
Determine initial_focus:
  IF maturity_score < 40  → "acquisition"
  IF repeat_rate < 0.20   → "retention"
  ELSE                    → "engagement"
         │
         ▼
Generate reasoning text (SHAP values → natural language)
         │
         ▼
Return structured response
```

### Explainability Plan

Use SHAP to generate feature importance for each inference:
- Extract top 2 SHAP features driving the persona prediction
- Format into human-readable string: `"Strong repeat rate (0.18) and high product concentration drove the 'loyalist' classification"`
- Store reasoning in DB alongside output (for audit)

---

## 8. Engine 2 — Benchmark Engine

### Purpose
Answer: **"How is this merchant performing compared to stores like theirs?"**

Runs weekly per merchant. Compares KPIs against a peer group cluster.

### Input Data

```
Sources:
  - customers_360        → repeat rate, LTV, lifecycle stages
  - orders_enriched      → revenue, AOV, cart abandonment
  - campaign_performance → open/click/conversion rates
  - merchant_profiles    → vertical + maturity (from Discovery)
  - Feast                → pre-computed KPI features
```

**Features used:**

| Feature | Description |
|---|---|
| `repeat_purchase_rate` | % of customers who ordered 2+ times |
| `open_rate_avg` | Average email open rate across campaigns |
| `click_rate_avg` | Average email click rate across campaigns |
| `conversion_rate_avg` | Average email → purchase conversion |
| `revenue_per_email` | Revenue / emails sent |
| `customer_ltv` | Average customer lifetime value |
| `cart_abandonment_rate` | Checkouts not completed / total checkouts |
| `new_customer_rate` | New customers / total customers this period |
| `vertical` | From Discovery output |
| `maturity_score` | From Discovery output |

### Models to Build

**Model A — Peer Clustering**
- Algorithm: K-Means (K = 8–12, tuned via silhouette score)
- Task: Group merchants into peer clusters by {vertical, size, maturity}
- Output: `peer_cluster_id` per merchant
- Metric: Silhouette score > 0.45
- Note: Retrained monthly as merchant base grows

**Model B — KPI Gap Scorer**
- Algorithm: Linear Regression (one per KPI per cluster)
- Task: Score each merchant's KPI gap vs. cluster median
- Output: sub-scores 0–100 per KPI dimension
- Metric: MAE < 5 points

**Health Score Formula (deterministic, not ML):**
```
health_score     = (0.30 × acquisition_score)
                 + (0.30 × conversion_score)
                 + (0.40 × retention_score)

acquisition_score  = f(new_customer_rate, open_rate, click_rate vs peer median)
conversion_score   = f(conversion_rate, revenue_per_email vs peer median)
retention_score    = f(repeat_purchase_rate, customer_ltv, cart_abandonment vs peer median)

Each sub-score: gap to peer median, normalized to 0–100
```

### API Contract

```
Endpoint: POST /engine/benchmark/report

Request:
{
  "merchant_id": "uuid",
  "kpi_metrics": {
    "repeat_purchase_rate": 0.14,
    "open_rate_avg": 0.21,
    "click_rate_avg": 0.04,
    "conversion_rate_avg": 0.012,
    "revenue_per_email": 0.83,
    "customer_ltv": 210.00,
    "cart_abandonment_rate": 0.68,
    "new_customer_rate": 0.55
  },
  "context": {
    "vertical": "beauty",
    "maturity_score": 72,
    "region": "US"
  }
}

Response:
{
  "merchant_id": "uuid",
  "health_score": 61,
  "funnel_scores": {
    "acquisition": 70,
    "conversion": 58,
    "retention": 55
  },
  "peer_percentile": 42,
  "peer_cluster_id": "beauty-mid-us",
  "gap_flags": [
    "repeat_purchase_rate is 18% below peer median (32%)",
    "cart_abandonment_rate is 12% above peer median (56%)"
  ],
  "kpi_snapshot": { ... },
  "model_version": "benchmark-v1.1",
  "generated_at": "2025-01-01T12:00:00Z"
}
```

### Internal Logic Flow

```
POST /engine/benchmark/report
         │
         ▼
Validate request (Pydantic)
         │
         ▼
Assign merchant to peer cluster
(load cluster model from MLflow → predict cluster_id)
         │
         ▼
Fetch peer cluster medians from Feast / cache
         │
         ▼
Compute KPI gaps (merchant value - cluster median)
         │
         ▼
Compute sub-scores (acquisition, conversion, retention)
         │
         ▼
Compute health_score via weighted formula
         │
         ▼
Identify gap_flags (KPIs where gap > threshold)
         │
         ▼
Compute peer_percentile
(rank this merchant vs. all merchants in cluster)
         │
         ▼
Return structured report
```

---

## 9. Engine 3 — Strategy Engine

### Purpose
Answer: **"Given what we know about this merchant, what marketing actions should they take right now?"**

This is the **most important engine** — the core "Growth Marketer's Brain." It combines domain expertise (from the Excel rule frameworks) with ML ranking to produce prioritized, actionable strategies.

### The Excel Rule Framework (Critical)

The Bravola team has documented growth-marketing rules in Excel spreadsheets (REV-xx, ENG-xx rule sets). These encode what a human strategist would do in specific situations. Your job is to import these rules into a Python rule engine.

**Example rules:**
```
Rule REV-01: Low repeat purchase rate (< 20%) → Trigger WIN_BACK campaign
Rule REV-02: High margin SKUs not promoted → Trigger UPSELL campaign
Rule ENG-01: Low email open rate (< 15%) → Trigger REENGAGEMENT flow
Rule ENG-02: Inactive subscribers > 30% → Trigger SUNSET sequence
Rule AUD-01: No welcome series active → Trigger WELCOME_SERIES
Rule AUD-02: No referral program → Trigger REFERRAL_LAUNCH
```

Each rule has: a condition, a strategy type, campaign suggestions, and a base weight (importance score).

### Input Data

```
Sources (passed by Node.js):
  - discovery output (persona, vertical, maturity_score)
  - benchmark output (health_score, gap_flags, funnel_scores)
  - merchant constraints (min_roas, budget_tier)
  - available_channels (["email", "sms"])
  - active_klaviyo_flows (what's already running — to avoid duplication)
```

### Models to Build

**Component A — Rule Engine (deterministic)**
- Load all rules from DB (imported from Excel by Node.js team)
- For each rule: evaluate condition against input features
- Return: set of triggered rules with base weights

**Component B — Learning-to-Rank (LTR) Model**
- Algorithm: RankNet or LambdaRank (pairwise ranking)
- Task: Re-rank triggered strategies by predicted revenue lift
- Training data: historical `(merchant_features, strategy_chosen, revenue_outcome)` tuples
- Output: ranking adjustment for each candidate strategy
- Metric: NDCG@3 > 0.70

**Strategy Scoring Formula (hybrid):**
```
strategy_score = (rule_base_weight   × W_rule)
               + (model_lift_score   × W_model)
               - (confidence_penalty × W_penalty)

Where:
  rule_base_weight   = Excel-defined importance of this rule (0–1)
  model_lift_score   = LTR model's predicted revenue lift (0–1)
  confidence_penalty = reduction when confidence_score is low
  W_rule, W_model, W_penalty = global weights (tuned by Feedback Engine)
```

### API Contract

```
Endpoint: POST /engine/strategy/generate

Request:
{
  "merchant_id": "uuid",
  "discovery_output": {
    "persona": "loyalist",
    "vertical": "beauty",
    "maturity_score": 72,
    "initial_focus": "retention"
  },
  "benchmark_output": {
    "health_score": 61,
    "gap_flags": ["repeat_purchase_rate is 18% below peer median"],
    "funnel_scores": { "acquisition": 70, "conversion": 58, "retention": 55 },
    "peer_cluster_id": "beauty-mid-us"
  },
  "constraints": {
    "available_channels": ["email"],
    "active_flow_ids": ["welcome_series", "abandoned_cart"],
    "budget_tier": "mid"
  }
}

Response:
{
  "merchant_id": "uuid",
  "strategy_batch_id": "batch-uuid",
  "strategies": [
    {
      "strategy_id_code": "winback_30_day",
      "triggered_rule_id": "REV-01",
      "segment": "lapsed_30_days",
      "channel": "email",
      "theme": "Win-Back",
      "timing": "immediate",
      "priority_rank": 1,
      "confidence_score": 0.87,
      "expected_impact": "high",
      "reasoning": "Your repeat purchase rate (14%) is 18% below the peer median (32%) for beauty stores. Win-back campaigns in this vertical have shown an average 12% lift in repeat purchases.",
      "rule_weighted_score": 0.72,
      "model_lift_score": 0.91,
      "confidence_penalty": 0.05,
      "strategy_score": 0.834
    },
    {
      "strategy_id_code": "cart_recovery_flow",
      "triggered_rule_id": "REV-05",
      "segment": "abandoned_carts_7d",
      "channel": "email",
      "theme": "Cart Recovery",
      "timing": "triggered",
      "priority_rank": 2,
      ...
    }
  ],
  "model_version": "strategy-v2.0",
  "generated_at": "2025-01-01T12:00:00Z"
}
```

### Internal Logic Flow

```
POST /engine/strategy/generate
         │
         ▼
Validate request (Pydantic)
         │
         ▼
Load all active rules from rules_registry
         │
         ▼
Evaluate each rule condition against:
  - merchant feature vector (from Feast)
  - benchmark gap_flags
  - discovery persona/maturity
  → Produces: candidate strategy set (rules that fired)
         │
         ▼
Filter out duplicates of active Klaviyo flows
         │
         ▼
For each candidate: compute rule_weighted_score
         │
         ▼
Load LTR model from MLflow
Run model → model_lift_score per candidate
         │
         ▼
Compute final strategy_score per candidate
         │
         ▼
Sort by strategy_score → assign priority_rank
         │
         ▼
Generate reasoning text per strategy
(triggered rule description + gap metric + peer comparison)
         │
         ▼
Return top N strategies (N = configurable, default 5)
```

---

## 10. Engine 4 — Feedback Engine

### Purpose
Answer: **"What did we learn from this campaign? How should we adjust?"**

Runs after campaign performance data is available (typically 7–14 days post-execution). Also processes human override signals in near real-time.

### Input Data

```
Sources (passed by Node.js):
  - strategy_id            (which strategy we're evaluating)
  - merchant_id
  - campaign_performance:
    - emails_sent, open_rate, click_rate, conversion_rate, revenue_attributed
  - human_action:          "approved" | "rejected" | "overridden"
  - override_details:      (if overridden) what changed + reason
  - peer_benchmarks:       cluster medians (for comparison)
```

### Logic to Build

**Component A — Performance Classifier**
```
Rules (deterministic — no ML needed here):

IF conversion_rate > peer_median_conversion AND revenue_attributed > baseline:
    performance_class = "success"

ELIF conversion_rate < (0.5 × peer_median_conversion):
    performance_class = "failure"

ELSE:
    performance_class = "neutral"
```

**Component B — Rule Weight Updater**
```
For each rule_id that was active in this strategy:

  learning_rate = 0.05  (tunable config)

  IF performance_class == "success":
      new_weight = min(old_weight + learning_rate, 1.0)

  IF performance_class == "failure":
      new_weight = max(old_weight - learning_rate, 0.1)

  IF human_action == "overridden":
      new_weight = max(old_weight - (learning_rate × 0.6), 0.1)
      → log override for future model retraining

  IF human_action == "rejected":
      new_weight = max(old_weight - (learning_rate × 0.8), 0.1)

Updated weights written back to rules_registry in DB
```

**Component C — Retrain Trigger**
```
Count failures + overrides in past 14 days for a given engine.

IF count > RETRAIN_THRESHOLD (configurable, default: 20):
    dispatch Celery task: retrain_strategy_engine()
    log: retrain triggered, reason, timestamp
```

### API Contract

```
Endpoint: POST /engine/feedback/process

Request:
{
  "merchant_id": "uuid",
  "strategy_id": "uuid",
  "triggered_rule_ids": ["REV-01", "ENG-02"],
  "campaign_performance": {
    "emails_sent": 4200,
    "open_rate": 0.28,
    "click_rate": 0.06,
    "conversion_rate": 0.018,
    "revenue_attributed": 3800.00
  },
  "peer_benchmarks": {
    "median_conversion_rate": 0.014
  },
  "human_action": "approved",
  "override_details": null
}

Response:
{
  "merchant_id": "uuid",
  "strategy_id": "uuid",
  "performance_class": "success",
  "weight_updates": [
    { "rule_id": "REV-01", "old_weight": 0.85, "new_weight": 0.90 },
    { "rule_id": "ENG-02", "old_weight": 0.70, "new_weight": 0.75 }
  ],
  "retrain_triggered": false,
  "retrain_reason": null,
  "next_review_hint": "This merchant's retention metrics are improving. Consider a loyalty upsell strategy next cycle.",
  "processed_at": "2025-01-15T09:00:00Z"
}
```

---

## 11. Shared Infrastructure Plan

### 11.1 Database Access (`shared/db.py`)

- SQLAlchemy async engine + session factory
- Connection pooling configured for concurrent FastAPI requests
- Per-request session via FastAPI dependency injection
- All queries include `merchant_id` filter (tenant isolation — mirrors Node.js RLS)

### 11.2 Feature Store Client (`shared/feature_store.py`)

- Feast client wrapper for fetching online features per merchant
- `get_features(merchant_id) → dict` — single call returns full feature vector
- Falls back to direct DB query if Feast is stale or unavailable
- Feature freshness check: log warning if features > 24h old

### 11.3 Model Registry Client (`shared/model_registry.py`)

- MLflow client wrapper
- `load_model(engine_name, stage="Production") → model` — loads current production model
- Models loaded at app startup and cached in memory (not re-loaded per request)
- Background thread checks for new model version every 60s (hot-swap without restart)

### 11.4 Configuration (`shared/config.py`)

```
Environment variables (all required):
  DATABASE_URL           Async PostgreSQL connection string
  REDIS_URL              Redis connection string
  FEAST_REPO_PATH        Path to Feast feature repository
  MLFLOW_TRACKING_URI    MLflow server URL
  CELERY_BROKER_URL      Redis URL for Celery
  LOG_LEVEL              INFO | DEBUG | WARNING
  LEARNING_RATE          Feedback Engine weight update step (default: 0.05)
  RETRAIN_THRESHOLD      Failure count before retraining (default: 20)
  MAX_STRATEGIES         Max strategies to return (default: 5)
```

### 11.5 Logging (`shared/logging.py`)

- Structured JSON logging via `structlog`
- Every log entry includes: `merchant_id`, `engine`, `trace_id`, `timestamp`, `level`
- AI decisions additionally log: `model_version`, `confidence_score`, `input_feature_hash`
- Ingested by Grafana Loki for the ops team

### 11.6 API Middleware (`api/middleware.py`)

- **Request logging**: log every inbound request with merchant_id + latency
- **Error handling**: catch unhandled exceptions → return structured error JSON
- **Health checks**: `/health` returns `{ status: ok, engines: [...], models_loaded: true }`
- **Trace ID injection**: generate UUID per request, attach to all logs

---

## 12. Data Contracts with Node.js Team

You do not control the database schema or the Shopify/Klaviyo ETL. The Node.js team owns that. You must agree on these contracts before building:

### 12.1 Tables You Read From (Node.js team owns these)

| Table | Key Columns You Need |
|---|---|
| `customers_360` | `merchant_id`, `repeat_rate`, `avg_order_value`, `days_to_second_purchase`, `email_engagement_score` |
| `orders_enriched` | `merchant_id`, `order_date`, `total_price`, `product_categories`, `is_repeat_order` |
| `campaign_performance` | `merchant_id`, `strategy_id`, `open_rate`, `click_rate`, `conversion_rate`, `revenue_attributed` |
| `human_override_logs` | `merchant_id`, `strategy_id`, `override_reason`, `strategist_id` |
| `onboarding_sessions` | `merchant_id`, `responses` (JSONB) |
| `merchant_profiles` | `merchant_id` (you write to this) |
| `benchmark_reports` | `merchant_id` (you write to this) |
| `strategies` | `merchant_id`, `strategy_id_code`, `status` (you write strategy data via API response) |

### 12.2 Tables You Write To

You do not write directly to the DB. You return JSON via API → Node.js team writes to DB. Exception: MLflow and Feast you own entirely.

### 12.3 Agreed Internal API Versioning

- All engine endpoints versioned: `/engine/v1/discovery/profile`
- Breaking schema changes communicated ≥ 1 sprint ahead
- Pydantic schemas shared as a Python package (or JSON Schema doc) with Node.js team
- Node.js team writes integration tests against your OpenAPI spec

---

## 13. ML Pipeline Plan

### Full ML Lifecycle

```
OFFLINE (Training):
  PostgreSQL normalized tables
        │
        ▼
  Feature engineering scripts (pandas/numpy)
        │
        ▼
  Feast offline store (S3-backed) — historical features for training
        │
        ▼
  Model training scripts (scikit-learn / XGBoost)
        │
        ▼
  Evaluation (metrics check against test set)
        │
  Pass? Yes ──► MLflow: log experiment + register model version
        │  No ──► discard, alert team via Slack
        │
        ▼
  Promote model version to "Production" stage in MLflow

ONLINE (Serving):
  FastAPI app starts → load Production model from MLflow
        │
        ▼
  Feast online store (Redis-backed) → real-time feature serving
        │
        ▼
  Inference → structured response returned to Node.js
```

### Celery Retraining Workers

Separate Celery worker processes (not the FastAPI app) handle:
- Weekly scheduled retraining jobs (per engine)
- On-demand retraining triggered by Feedback Engine threshold
- Worker tasks defined in `pipelines/retraining/tasks.py`
- Results logged to MLflow; new model promoted automatically if evaluation passes

---

## 14. Feature Engineering Plan

### Pipeline: PostgreSQL → Feast

Run daily (or more frequently as needed) via Celery scheduled task.

**Step 1 — Order Features** (`feature_engineering/merchant_features.py`)
```
FROM orders_enriched:
  - avg_order_value          = mean(total_price) per merchant
  - repeat_rate              = count(customers with 2+ orders) / count(distinct customers)
  - days_to_second_purchase  = median(gap between order_sequence=1 and order_sequence=2)
  - product_concentration    = revenue of top 3 SKUs / total revenue
  - revenue_last_30d         = sum(total_price) WHERE order_date > NOW() - 30 days
  - revenue_last_90d         = sum(total_price) WHERE order_date > NOW() - 90 days
```

**Step 2 — Engagement Features** (`feature_engineering/engagement_features.py`)
```
FROM campaign_performance:
  - open_rate_avg            = mean(open_rate) per merchant last 90d
  - click_rate_avg           = mean(click_rate) per merchant last 90d
  - conversion_rate_avg      = mean(conversion_rate) per merchant last 90d
  - revenue_per_email        = sum(revenue_attributed) / sum(emails_sent)
  - email_engagement_score   = 0.6 * open_rate_avg + 0.4 * click_rate_avg
```

**Step 3 — Peer-Normalized Features** (`feature_engineering/peer_features.py`)
```
FROM clustering output:
  - For each merchant, fetch cluster medians
  - gap_repeat_rate          = repeat_rate - cluster_median_repeat_rate
  - gap_open_rate            = open_rate_avg - cluster_median_open_rate
  - gap_conversion_rate      = conversion_rate_avg - cluster_median_conversion
  - peer_percentile          = percentileofscore(cluster, merchant_score)
```

**Step 4 — Push to Feast**
```
Write computed features to:
  - Feast offline store (S3/PostgreSQL) — for model training
  - Feast online store (Redis) — for real-time inference
```

---

## 15. Model Training Plan

### Training Data Requirements

| Engine | Minimum Training Records | Label Source |
|---|---|---|
| Discovery — Persona | 200+ labeled merchants per persona | Manual labels by Bravola strategists |
| Discovery — Maturity | 500+ merchants with outcome history | Derived from revenue growth trajectory |
| Discovery — Vertical | 100+ per vertical (7+ verticals) | Onboarding answers + manual verification |
| Benchmark — Clustering | All active merchants (no labels needed) | Unsupervised |
| Benchmark — KPI Scorer | 300+ merchants with performance history | Peer median gaps |
| Strategy — LTR | 500+ (strategy, features, outcome) tuples | From historical campaign results |
| Feedback — Weight Opt. | N/A (rule-based, no model training) | — |

### Bootstrapping Problem (MVP)

We don't have 500+ merchants at launch. Plan:

1. **Phase 1 (0–50 merchants):** Run purely rule-based Strategy Engine. No LTR model. Use Excel rule weights as-is.
2. **Phase 2 (50–200 merchants):** Train initial LTR model on early data. Expect lower quality but functional.
3. **Phase 3 (200+ merchants):** Full LTR training with enough examples for generalization.

Discovery and Benchmark Engines can be trained from day one using:
- Manually labeled pilot merchant data (Bravola team labels 50–100 merchants)
- Synthetic augmentation for rare persona/vertical combinations

### Training Script Conventions

Each training script (`train/train_*.py`) must:
1. Load training data from Feast offline store or PostgreSQL
2. Define feature set (explicit list — no auto-discovery)
3. Define train/val/test split (70/15/15)
4. Train model with explicit hyperparameters
5. Evaluate on test set — check against minimum threshold
6. If passes: log to MLflow, register model version, optionally promote

---

## 16. Model Serving Plan

### FastAPI App Startup

```
On startup:
  1. Connect to PostgreSQL (verify connectivity)
  2. Connect to Feast online store (verify connectivity)
  3. Load all production models from MLflow:
     - discovery.persona_model
     - discovery.maturity_model
     - discovery.vertical_model
     - benchmark.cluster_model
     - benchmark.kpi_scorer
     - strategy.ranker_model
  4. Load rules registry from DB (all rule definitions + weights)
  5. Start background thread for model version polling (60s interval)
  6. Return health check: OK
```

### Model Version Management

- Production model loaded by label `stage="Production"` in MLflow
- Never use `stage="latest"` in production — always a named version
- New model promoted → background thread detects version change → hot-swaps model
- Rollback: re-promote previous MLflow version → picked up within 60s

### Inference Latency Targets

| Engine | Target p99 Latency | Notes |
|---|---|---|
| Discovery | < 1s | Runs once per merchant, not time-critical |
| Benchmark | < 2s | Weekly run, batch acceptable |
| Strategy | < 5s | Weekly run, batch acceptable |
| Feedback | < 500ms | Near real-time weight update |

---

## 17. Testing Plan

### Test Pyramid

```
┌────────────────────────────────┐
│    Integration Tests (20%)     │  Full endpoint tests (mock external deps)
├────────────────────────────────┤
│      Unit Tests (70%)          │  Service logic, models, rules, scoring
├────────────────────────────────┤
│     Contract Tests (10%)       │  Schema validation vs. Node.js team's expectations
└────────────────────────────────┘
```

### Unit Test Plan

| Module | What to Test |
|---|---|
| `discovery/service.py` | Feature vector → correct persona output, edge cases |
| `benchmark/health_score.py` | Score formula math, boundary values (0, 50, 100) |
| `strategy/rules/engine.py` | Each rule: condition met → correct strategy triggered |
| `strategy/scorer.py` | Score formula produces expected ranking order |
| `feedback/weight_updater.py` | Weight increases on success, decreases on failure, clamp at 0.1 and 1.0 |
| `feedback/classifier.py` | Performance classification edge cases |

### Integration Test Plan

For each engine endpoint:
1. Start FastAPI test client (no real DB/Feast/MLflow)
2. Mock: DB session, Feast client, MLflow model loader
3. Send well-formed request
4. Assert: response schema valid, status 200, key fields present
5. Send malformed request → assert 422 Validation Error
6. Simulate model load failure → assert 503 with structured error

### Fixtures Plan

Maintain a `tests/fixtures/` directory with:
- `sample_merchant_features.json` — realistic feature vector for a beauty/loyalist merchant
- `sample_benchmark_report.json` — benchmark output matching the feature vector
- `sample_strategy_output.json` — expected strategy objects for the above inputs
- Used in both unit and integration tests for consistency

### CI Pipeline for Tests

```
On every pull request:
  1. flake8 + mypy (lint + type check)
  2. pytest unit tests (fast, no external deps)
  3. pytest integration tests (mocked deps)
  4. Coverage report (target: >80%)

On merge to main:
  5. Build Docker image
  6. Scan with Trivy (security)
  7. Deploy to staging
  8. Run smoke tests against staging (real DB, real Feast)
```

---

## 18. Sprint-by-Sprint Build Plan

Total: **8 sprints (16 weeks)** for the Python AI Engine scope only.

---

### Sprint 1 (Weeks 1–2): Foundation & Shared Infrastructure

**Goal:** Project scaffold, dependencies working, all shared modules built.

**Tasks:**
- [ ] Set up `pyproject.toml` with all dependencies (FastAPI, SQLAlchemy, Feast, MLflow, Celery, XGBoost, SHAP, structlog, pytest)
- [ ] Create folder structure (all files as empty stubs)
- [ ] Build `shared/config.py` — all environment variables loaded via Pydantic BaseSettings
- [ ] Build `shared/db.py` — async SQLAlchemy session factory, dependency injection
- [ ] Build `shared/feature_store.py` — Feast client wrapper with fallback to DB
- [ ] Build `shared/model_registry.py` — MLflow load/register/promote wrappers
- [ ] Build `shared/logging.py` — structlog JSON logger with merchant_id + trace_id
- [ ] Build `shared/exceptions.py` — custom exception classes
- [ ] Build `api/main.py` — FastAPI app (empty routers registered, health endpoint)
- [ ] Build `api/middleware.py` — request logging, error handling middleware
- [ ] Set up `docker-compose.yml` for local dev (FastAPI + PostgreSQL + Redis + MLflow)
- [ ] Set up `pytest` configuration + `conftest.py` with base fixtures

**Done when:** `docker-compose up` starts the app, `/health` returns 200, DB and Feast connections verified.

---

### Sprint 2 (Weeks 3–4): Feature Engineering Pipeline

**Goal:** All merchant features computed from DB and pushed to Feast.

**Tasks:**
- [ ] Review and document all PostgreSQL table schemas with Node.js team
- [ ] Build `pipelines/feature_engineering/merchant_features.py` — order + customer features
- [ ] Build `pipelines/feature_engineering/engagement_features.py` — email KPI features
- [ ] Build `pipelines/feature_engineering/feast_push.py` — write to Feast online + offline store
- [ ] Define Feast feature views and entities for all feature groups
- [ ] Set up Celery app + broker connection (`pipelines/retraining/celery_app.py`)
- [ ] Schedule daily feature pipeline job (Celery beat)
- [ ] Write unit tests for all feature computation functions
- [ ] Write integration test: run pipeline on sample DB data → verify Feast output

**Done when:** Feature pipeline runs, correct features appear in Feast online store for a test merchant.

---

### Sprint 3 (Weeks 5–6): Discovery Engine

**Goal:** Discovery Engine endpoint live, persona/maturity/vertical models trained.

**Tasks:**
- [ ] Build `engines/discovery/schemas.py` — Pydantic request + response models
- [ ] Build `engines/discovery/features.py` — fetch feature vector from Feast
- [ ] Build `engines/discovery/models/persona.py` — XGBoost wrapper (train + infer)
- [ ] Build `engines/discovery/models/maturity.py` — Logistic Regression wrapper
- [ ] Build `engines/discovery/models/vertical.py` — Random Forest wrapper
- [ ] Build `engines/discovery/explainer.py` — SHAP → reasoning text
- [ ] Build `engines/discovery/service.py` — orchestrate all 3 models + explainer
- [ ] Build `engines/discovery/router.py` — FastAPI route
- [ ] Write `engines/discovery/train/train_persona.py` — full training script
- [ ] Write `engines/discovery/train/train_maturity.py`
- [ ] Write `engines/discovery/train/train_vertical.py`
- [ ] Train initial models on seed/synthetic data → register in MLflow
- [ ] Write unit tests for service logic
- [ ] Write integration tests for endpoint

**Done when:** `POST /engine/v1/discovery/profile` with sample merchant returns correct JSON with persona, maturity_score, vertical, reasoning, and model_version.

---

### Sprint 4 (Weeks 7–8): Benchmark Engine

**Goal:** Benchmark Engine endpoint live, clustering and KPI scoring models trained.

**Tasks:**
- [ ] Build `engines/benchmark/schemas.py`
- [ ] Build `engines/benchmark/features.py`
- [ ] Build `engines/benchmark/models/clustering.py` — K-Means peer grouping
- [ ] Build `engines/benchmark/models/kpi_scorer.py` — Linear Regression gap scoring
- [ ] Build `engines/benchmark/health_score.py` — deterministic health score formula
- [ ] Build `engines/benchmark/explainer.py` — gap_flags + reasoning generation
- [ ] Build `engines/benchmark/service.py`
- [ ] Build `engines/benchmark/router.py`
- [ ] Write training scripts for clustering + kpi_scorer
- [ ] Add `peer_features.py` to feature engineering pipeline (peer-normalized features)
- [ ] Train initial models → register in MLflow
- [ ] Write unit + integration tests

**Done when:** `POST /engine/v1/benchmark/report` returns health_score, funnel_scores, gap_flags, peer_percentile with model_version.

---

### Sprint 5 (Weeks 9–11): Strategy Engine — Rules + Scoring

**Goal:** Rule Engine built, all Excel rules imported, strategy scoring working.

**Tasks:**
- [ ] Coordinate with Node.js team: receive Excel rules as JSON/DB rows
- [ ] Build `engines/strategy/rules/rules_registry.py` — all rule definitions (conditions, weights, strategy types)
- [ ] Build `engines/strategy/rules/loader.py` — load rules from DB
- [ ] Build `engines/strategy/rules/engine.py` — evaluate conditions against features
- [ ] Build `engines/strategy/scorer.py` — strategy_score formula implementation
- [ ] Build `engines/strategy/schemas.py`
- [ ] Build `engines/strategy/features.py`
- [ ] Build `engines/strategy/explainer.py` — per-strategy reasoning text
- [ ] Build `engines/strategy/service.py` — orchestrate rules + scoring + dedup
- [ ] Build `engines/strategy/router.py`
- [ ] Write unit tests for every rule condition
- [ ] Write unit tests for scorer (correct ranking order)
- [ ] Write integration test for full endpoint

**Note:** LTR model is NOT included yet — use rule_base_weight only. LTR model is added in Sprint 6 when training data exists.

**Done when:** `POST /engine/v1/strategy/generate` returns ranked strategy objects using rule-only scoring. No LTR model yet.

---

### Sprint 6 (Weeks 12–13): Strategy Engine — LTR Model + Feedback Engine

**Goal:** LTR ranking model trained (on initial data), Feedback Engine built.

**Tasks:**
- [ ] Build `engines/strategy/models/ranker.py` — LTR model wrapper (RankNet or sklearn-based)
- [ ] Write `engines/strategy/train/train_ranker.py` — full training script
- [ ] Train LTR model on initial strategy outcome data → integrate into scoring
- [ ] Build `engines/feedback/schemas.py`
- [ ] Build `engines/feedback/classifier.py` — performance classifier
- [ ] Build `engines/feedback/weight_updater.py` — rule weight update logic
- [ ] Build `engines/feedback/retrain_trigger.py` — threshold check + Celery dispatch
- [ ] Build `engines/feedback/service.py`
- [ ] Build `engines/feedback/router.py`
- [ ] Build Celery retraining tasks for all 4 engines
- [ ] Write unit tests for weight updater (success/failure/override paths)
- [ ] Write integration tests for feedback endpoint

**Done when:** `POST /engine/v1/feedback/process` correctly updates rule weights and returns performance_class. Celery retrain task queues correctly when threshold exceeded.

---

### Sprint 7 (Week 14): End-to-End Integration & Hardening

**Goal:** All 4 engines work together end-to-end, integration tested with Node.js team.

**Tasks:**
- [ ] End-to-end integration test: Discovery → Benchmark → Strategy (all chained)
- [ ] Verify all engine outputs match agreed contracts with Node.js team
- [ ] Load test: 50 concurrent strategy generation requests — verify latency targets
- [ ] Add model hot-swap logic (background version polling)
- [ ] Review all error handling: every external dependency failure returns structured error
- [ ] Security review: validate no merchant data leaks between tenant requests
- [ ] Write complete OpenAPI spec review (all endpoints documented)
- [ ] Fix all issues found in integration testing

**Done when:** Full pipeline runs correctly in staging. Node.js team can call all 4 engines successfully.

---

### Sprint 8 (Weeks 15–16): Feedback Loop Activation & Production Readiness

**Goal:** Feedback loop live with real data, platform production-ready.

**Tasks:**
- [ ] Activate Feedback Engine on first real campaign results
- [ ] Run first weight update cycle — verify rule weights change correctly
- [ ] Verify retrain trigger fires correctly (test with synthetic failure data)
- [ ] Run full weekly ML pipeline (feature engineering + strategy generation for all merchants)
- [ ] Tune model hyperparameters based on initial real-world performance
- [ ] Set up model drift monitoring (confidence score distribution tracking)
- [ ] Set up Grafana dashboards: engine latency, model confidence, retrain activity
- [ ] Set up PagerDuty alerts for engine failures
- [ ] Final documentation: API docs, runbooks for retraining, oncall guide
- [ ] Production deployment checklist complete

**Done when:** Full feedback loop demonstrated working. Strategies improve measurably after first feedback cycle.

---

## 19. Dependencies & Blockers

### What You Need from the Node.js Team

| Dependency | When You Need It | Risk if Delayed |
|---|---|---|
| PostgreSQL schema + migrations finalized | Sprint 1 | Feature engineering blocked |
| `customers_360` table populated with test data | Sprint 2 | Cannot test feature pipeline |
| `campaign_performance` table schema | Sprint 2 | Engagement features blocked |
| Excel rules as importable JSON/DB rows | Sprint 5 | Rules Engine blocked |
| `active_klaviyo_flows` field available | Sprint 5 | Strategy dedup logic blocked |
| Strategy outcome data (even synthetic) | Sprint 6 | LTR model training blocked |

### What You Give the Node.js Team

| Deliverable | Sprint | Format |
|---|---|---|
| FastAPI OpenAPI spec (all 4 engines) | Sprint 1 (stubs) | Auto-generated from Pydantic schemas |
| Discovery Engine live | Sprint 3 | REST endpoint |
| Benchmark Engine live | Sprint 4 | REST endpoint |
| Strategy Engine live | Sprint 5 | REST endpoint |
| Feedback Engine live | Sprint 6 | REST endpoint |
| Model hot-swap without restart | Sprint 7 | Background behavior |

### External Infrastructure Dependencies

| Dependency | Owner | Risk |
|---|---|---|
| MLflow server running | DevOps | Model training blocked if unavailable |
| Feast server + Redis online store | DevOps | Real-time inference blocked |
| Celery broker (Redis) | DevOps | Retraining jobs blocked |
| PostgreSQL access | Node.js / DevOps | Everything blocked |

---

## 20. Definition of Done

A Python AI Engine is considered complete and production-ready when:

### Per Engine
- [ ] FastAPI endpoint live and returns correct schema for valid request
- [ ] Returns structured error JSON for invalid request (422) or dependency failure (503)
- [ ] Model loaded from MLflow (not hardcoded)
- [ ] Features loaded from Feast (not hardcoded)
- [ ] Reasoning text generated and included in every response
- [ ] Model version included in every response
- [ ] Unit test coverage > 80% for service logic
- [ ] Integration test passes against staging environment
- [ ] p99 latency within target (Discovery < 1s, Benchmark < 2s, Strategy < 5s, Feedback < 500ms)
- [ ] Endpoint documented in OpenAPI spec

### For the Full AI Engine Service
- [ ] All 4 engines live in staging
- [ ] End-to-end pipeline tested: Discovery → Benchmark → Strategy → Feedback
- [ ] Feedback loop demonstrated: weight updates correctly reflect campaign outcomes
- [ ] Celery retraining worker functions and logs to MLflow
- [ ] Grafana dashboard shows all 4 engine metrics
- [ ] PagerDuty alert fires on engine failure
- [ ] No cross-tenant data leakage verified via automated test
- [ ] Docker image builds cleanly, starts up in < 30s
- [ ] README covers: local setup, running tests, deploying, retraining models, rollback procedure
