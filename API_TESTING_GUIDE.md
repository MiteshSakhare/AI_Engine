# Bravola AI Engine v2 — API Testing Guide

Complete testing reference for all API endpoints in the Bravola AI Engine v2. Includes curl (cmd.exe), PowerShell, and JSON body examples for Postman/Thunder Client.

> **⚠️ Windows PowerShell Users:** By default, PowerShell aliases `curl` to `Invoke-WebRequest` which will throw syntax errors with the `-H` flag. If using PowerShell, either type `curl.exe` instead of `curl`, or run these commands in a standard **Command Prompt (cmd)**.

> [!NOTE]
> **v2 Changes**: Discovery returns deep profiles, Benchmark includes Ollama narratives, Strategy has 4 tracks + crisis mode, Feedback returns UCB1 scores, and Chat now supports intent routing + SSE streaming.

---

## Base URLs
- **Localhost**: `http://localhost:8000`
- **Docker**: `http://localhost:80` (if mapped to port 80)

---

## 1. Root Endpoint
Checks if the engine API is online.

- **Endpoint**: `GET /`
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X GET http://localhost:8000/
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
  ```
- **Expected Output**:
  ```json
  {
    "message": "Bravola AI Engine is Online",
    "docs": "/docs",
    "health": "/health",
    "version": "v2"
  }
  ```

---

## 2. Health Endpoint
Deep health check of database and connected services.

- **Endpoint**: `GET /health`
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X GET http://localhost:8000/health
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  # 2. Check System Health
  Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

  # Expected Output:
  # status         : ok
  # version        : v2
  # environment    : development
  # engines        : {discovery, benchmark, strategy, feedback}
  # database       : connected
  # feature_store  : offline_fallback
  # model_registry : offline_fallback
  ```

---

## 3. Discovery Engine — Deep Merchant Profiling

Runs once at onboarding to determine a merchant's persona, vertical, maturity, and full deep profile.

> **v2 Changes**: Returns `target_audience`, `price_point_tier`, `key_value_proposition`, `growth_signals`, `dominant_channel`, `churn_risk_level`. Accepts `price_hint`, `audience_hint`, `primary_challenge` in onboarding. LLM fallback triggers for low-confidence persona (<0.55) and maturity grey zone (35-65).

- **Endpoint**: `POST /engine/v1/discovery/profile`
- **Headers**: `Content-Type: application/json`

### Test Case 1: Standard Merchant (Full Onboarding Data)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "feature_vector": {
      "avg_order_value": 75.50,
      "aov_variance": 12.30,
      "repeat_rate": 0.22,
      "purchase_frequency_variance": 0.05,
      "days_to_second_purchase": 45,
      "product_concentration": 0.60,
      "catalog_size": 150,
      "email_engagement_score": 0.45,
      "total_customer_count": 2500,
      "revenue_last_90d": 50000.00,
      "revenue_last_30d": 15000.00
    },
    "onboarding_responses": {
      "vertical_hint": "apparel",
      "goal_hint": "increase retention",
      "price_hint": "mid",
      "audience_hint": "Women 25-40 interested in sustainable fashion",
      "primary_challenge": "High cart abandonment rate"
    }
  }
  ```
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X POST http://localhost:8000/engine/v1/discovery/profile -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"feature_vector\":{\"avg_order_value\":75.5,\"aov_variance\":12.3,\"repeat_rate\":0.22,\"purchase_frequency_variance\":0.05,\"days_to_second_purchase\":45,\"product_concentration\":0.6,\"catalog_size\":150,\"email_engagement_score\":0.45,\"total_customer_count\":2500,\"revenue_last_90d\":50000.0,\"revenue_last_30d\":15000.0},\"onboarding_responses\":{\"vertical_hint\":\"apparel\",\"goal_hint\":\"increase retention\",\"price_hint\":\"mid\",\"audience_hint\":\"Women 25-40 sustainable fashion\",\"primary_challenge\":\"High cart abandonment\"}}"
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/engine/v1/discovery/profile" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","feature_vector":{"avg_order_value":75.5,"aov_variance":12.3,"repeat_rate":0.22,"purchase_frequency_variance":0.05,"days_to_second_purchase":45,"product_concentration":0.6,"catalog_size":150,"email_engagement_score":0.45,"total_customer_count":2500,"revenue_last_90d":50000.0,"revenue_last_30d":15000.0},"onboarding_responses":{"vertical_hint":"apparel","goal_hint":"increase retention","price_hint":"mid","audience_hint":"Women 25-40 sustainable fashion","primary_challenge":"High cart abandonment"}}'
  ```
- **Expected Output (v2 Deep Profile)**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "persona": "explorer",
    "vertical": "apparel",
    "seasonality": "medium",
    "catalog_complexity": "medium",
    "maturity_score": 45,
    "initial_focus": "retention",
    "confidence_score": 0.78,
    "reasoning": "Moderate AOV ($75.50) with a 22% repeat rate suggests...",
    "target_audience": "Women 25-40 interested in sustainable fashion",
    "price_point_tier": "mid",
    "key_value_proposition": "Sustainable, ethically sourced fashion apparel",
    "growth_signals": ["Growing customer base", "Decent email engagement"],
    "dominant_channel": "email",
    "churn_risk_level": "medium",
    "model_version": "discovery-v2",
    "generated_at": "2026-03-30T08:00:00.000000+00:00"
  }
  ```
  *(Note: If Ollama is unavailable during the request, deep profile fields like `target_audience`, `reasoning`, and `growth_signals` may return as empty strings or empty lists.)*

### Test Case 2: High-Value Whale Detection (AOV > 300)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_whale",
    "feature_vector": {
      "avg_order_value": 450.00,
      "repeat_rate": 0.35,
      "days_to_second_purchase": 20,
      "product_concentration": 0.75,
      "email_engagement_score": 0.55,
      "total_customer_count": 800,
      "revenue_last_90d": 180000.00,
      "revenue_last_30d": 62000.00
    },
    "onboarding_responses": {
      "vertical_hint": "beauty",
      "goal_hint": "revenue growth",
      "price_hint": "luxury"
    }
  }
  ```
- **Expected**: `persona: "high_value_whales"`, high confidence, `price_point_tier: "luxury"`

### Test Case 3: Low-Confidence LLM Fallback (Minimal Data)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_sparse",
    "feature_vector": {
      "avg_order_value": 30.00,
      "repeat_rate": 0.05,
      "total_customer_count": 50,
      "revenue_last_90d": 1500.00
    }
  }
  ```
- **Expected**: Low confidence score, persona and vertical may be LLM-corrected, maturity < 25

---

## 4. Benchmark Engine — Winsorized Z-Score Report

Benchmarks a merchant against a peer group using Winsorized Z-scores and generates an Ollama health narrative.

> **v2 Changes**: Winsorized Z-scores (±2σ), null-safe metric handling, Beta CDF percentile, `health_summary` narrative, `missing_metrics`, `percentile_method`, 12 named clusters, `opt_in_rate` as 4th acquisition metric.

- **Endpoint**: `POST /engine/v1/benchmark/report`
- **Headers**: `Content-Type: application/json`

### Test Case 1: Standard Benchmark

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "kpi_metrics": {
      "repeat_purchase_rate": 0.22,
      "open_rate_avg": 0.18,
      "click_rate_avg": 0.04,
      "conversion_rate_avg": 0.02,
      "revenue_per_email": 1.25,
      "customer_ltv": 150.0,
      "cart_abandonment_rate": 0.65,
      "new_customer_rate": 0.15,
      "refund_rate": 0.03,
      "social_engagement_score": 5.0,
      "customer_acquisition_cost": 25.0,
      "referral_rate": 0.05,
      "onsite_time_avg": 120.0,
      "bounce_rate_avg": 0.40,
      "product_review_rate": 0.08,
      "spam_complaint_rate": 0.001,
      "click_to_open_rate": 0.15,
      "sms_optin_rate": 0.10,
      "opt_in_rate": 0.04
    },
    "context": {
      "vertical": "apparel",
      "maturity_score": 45,
      "region": "US"
    }
  }
  ```
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X POST http://localhost:8000/engine/v1/benchmark/report -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"kpi_metrics\":{\"repeat_purchase_rate\":0.22,\"open_rate_avg\":0.18,\"click_rate_avg\":0.04,\"conversion_rate_avg\":0.02,\"revenue_per_email\":1.25,\"customer_ltv\":150.0,\"cart_abandonment_rate\":0.65,\"new_customer_rate\":0.15,\"refund_rate\":0.03,\"social_engagement_score\":5.0,\"customer_acquisition_cost\":25.0,\"referral_rate\":0.05,\"onsite_time_avg\":120.0,\"bounce_rate_avg\":0.40,\"product_review_rate\":0.08,\"spam_complaint_rate\":0.001,\"click_to_open_rate\":0.15,\"sms_optin_rate\":0.10,\"opt_in_rate\":0.04},\"context\":{\"vertical\":\"apparel\",\"maturity_score\":45,\"region\":\"US\"}}"
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/engine/v1/benchmark/report" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","kpi_metrics":{"repeat_purchase_rate":0.22,"open_rate_avg":0.18,"click_rate_avg":0.04,"conversion_rate_avg":0.02,"revenue_per_email":1.25,"customer_ltv":150.0,"cart_abandonment_rate":0.65,"new_customer_rate":0.15,"refund_rate":0.03,"social_engagement_score":5.0,"customer_acquisition_cost":25.0,"referral_rate":0.05,"onsite_time_avg":120.0,"bounce_rate_avg":0.40,"product_review_rate":0.08,"spam_complaint_rate":0.001,"click_to_open_rate":0.15,"sms_optin_rate":0.10,"opt_in_rate":0.04},"context":{"vertical":"apparel","maturity_score":45,"region":"US"}}'
  ```
- **Expected Output (v2)**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "health_score": 55,
    "funnel_scores": {
      "acquisition": 62,
      "conversion": 58,
      "retention": 42
    },
    "peer_percentile": 48,
    "percentile_method": "sigmoid_z_beta",
    "peer_cluster_id": "apparel-mid-us",
    "gap_flags": [
      "Repeat Purchase Rate is 21.4% below peer median (28.0%)",
      "Cart Abandonment Rate is 4.8% above peer median (62.0%)"
    ],
    "missing_metrics": [],
    "health_summary": "This apparel merchant scores 55/100, sitting below their mid-tier peers. Retention is the weakest funnel stage at 42/100 — the high cart abandonment rate (65%) relative to the peer median (62%) is the most critical gap to address.",
    "kpi_snapshot": {
      "repeat_purchase_rate": 0.22,
      "open_rate_avg": 0.18,
      "click_rate_avg": 0.04,
      "conversion_rate_avg": 0.02,
      "revenue_per_email": 1.25,
      "customer_ltv": 150.0,
      "cart_abandonment_rate": 0.65,
      "new_customer_rate": 0.15,
      "refund_rate": 0.03,
      "social_engagement_score": 5.0,
      "customer_acquisition_cost": 25.0,
      "referral_rate": 0.05,
      "onsite_time_avg": 120.0,
      "bounce_rate_avg": 0.40,
      "product_review_rate": 0.08,
      "spam_complaint_rate": 0.001,
      "click_to_open_rate": 0.15,
      "sms_optin_rate": 0.10,
      "opt_in_rate": 0.04
    },
    "model_version": "benchmark-v2",
    "generated_at": "2026-03-30T08:05:00.000000+00:00"
  }
  ```
  *(Note: `Invoke-RestMethod` in PowerShell might render empty arrays like `gap_flags: []` as objects `{}`. This is a PowerShell display quirk, and the API correctly returns `[]`.)*

### Test Case 2: Extreme Outlier (Winsorization Test)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_outlier",
    "kpi_metrics": {
      "repeat_purchase_rate": 0.95,
      "new_customer_rate": 5.0,
      "cart_abandonment_rate": 0.01,
      "conversion_rate_avg": 0.50,
      "open_rate_avg": 0.90,
      "click_rate_avg": 0.50,
      "revenue_per_email": 50.0,
      "customer_ltv": 5000.0,
      "opt_in_rate": 0.80
    },
    "context": { "vertical": "beauty", "maturity_score": 90, "region": "US" }
  }
  ```
- **Expected**: Health score should NOT be 100 — Winsorization clips extreme values at ±2σ. Score should cap around 85-95.

### Test Case 3: Missing Metrics (Null Handling)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_sparse_kpi",
    "kpi_metrics": {
      "repeat_purchase_rate": 0.18,
      "open_rate_avg": 0.20,
      "conversion_rate_avg": 0.01
    },
    "context": { "vertical": "food", "maturity_score": 50, "region": "US" }
  }
  ```
- **Expected**: `missing_metrics` will list all omitted metrics (they default to 0 but are flagged). Score should be moderate (~50) since missing metrics are substituted with peer mean.

---

## 5. Strategy Engine — 4-Track Strategy with Crisis Mode

Generates actionable marketing strategies across 4 tracks based on discovery and benchmark data.

> **v2 Changes**: 4th `crisis_response` track, `strategy_narrative` (Ollama executive summary), `total_triggered`, `tracks_populated`, Ollama-personalized descriptions, budget-aware scoring, data-driven MVP lift, fixed category routing bug.

- **Endpoint**: `POST /engine/v1/strategy/generate`
- **Headers**: `Content-Type: application/json`

### Test Case 1: Standard Strategy (Healthy Merchant)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "discovery_output": {
      "persona": "explorer",
      "vertical": "apparel",
      "maturity_score": 45,
      "initial_focus": "engagement"
    },
    "benchmark_output": {
      "health_score": 62,
      "gap_flags": ["low_retention"],
      "funnel_scores": {"acquisition": 70, "conversion": 55, "retention": 40},
      "peer_cluster_id": "apparel-mid-us"
    },
    "constraints": {
      "available_channels": ["email", "sms"],
      "active_flow_ids": [],
      "budget_tier": "mid"
    }
  }
  ```
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X POST http://localhost:8000/engine/v1/strategy/generate -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"discovery_output\":{\"persona\":\"explorer\",\"vertical\":\"apparel\",\"maturity_score\":45,\"initial_focus\":\"engagement\"},\"benchmark_output\":{\"health_score\":62,\"gap_flags\":[\"low_retention\"],\"funnel_scores\":{\"acquisition\":70,\"conversion\":55,\"retention\":40},\"peer_cluster_id\":\"apparel-mid-us\"},\"constraints\":{\"available_channels\":[\"email\",\"sms\"],\"active_flow_ids\":[],\"budget_tier\":\"mid\"}}"
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/engine/v1/strategy/generate" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","discovery_output":{"persona":"explorer","vertical":"apparel","maturity_score":45,"initial_focus":"engagement"},"benchmark_output":{"health_score":62,"gap_flags":["low_retention"],"funnel_scores":{"acquisition":70,"conversion":55,"retention":40},"peer_cluster_id":"apparel-mid-us"},"constraints":{"available_channels":["email","sms"],"active_flow_ids":[],"budget_tier":"mid"}}'
  ```
- **Expected Output (v2)**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "strategy_batch_id": "batch_uuid_here",
    "tracks": {
      "quick_wins": [
        {
          "rule_id": "REV-01",
          "category": "revenue",
          "description": "Implement a post-purchase win-back flow...",
          "campaigns": ["Win-back Email"],
          "flows": ["Post-Purchase"],
          "qualifying_questions": ["Is email integrated?"],
          "priority_rank": 1,
          "confidence_score": 0.88,
          "reasoning": "Low retention and moderate AOV make this high impact...",
          "rule_weighted_score": 8.5,
          "model_lift_score": 0.72,
          "confidence_penalty": 0.0,
          "strategy_score": 5.35,
          "creative_notes": "Focus on recently purchased product categories.",
          "ollama_personalized": true
        }
      ],
      "core_growth": [],
      "retention_rescue": [],
      "crisis_response": []
    },
    "strategy_narrative": "15 strategies evaluated for this apparel merchant with an 'explorer' customer base. Health score: 62/100. Focus: retention and engagement.",
    "total_triggered": 15,
    "tracks_populated": 1,
    "model_version": "strategy-v2",
    "generated_at": "2026-03-30T08:10:00.000000+00:00"
  }
  ```

### Test Case 2: Crisis Mode (Health < 40 + Multiple Gaps)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_crisis",
    "discovery_output": {
      "persona": "bargain_hunter",
      "vertical": "electronics",
      "maturity_score": 25,
      "initial_focus": "acquisition"
    },
    "benchmark_output": {
      "health_score": 28,
      "gap_flags": [
        "low_retention", "high_abandonment", "low_open_rate",
        "low_conversion", "poor_ltv"
      ],
      "funnel_scores": {"acquisition": 35, "conversion": 20, "retention": 15},
      "peer_cluster_id": "electronics-mid-us"
    },
    "constraints": {
      "available_channels": ["email"],
      "active_flow_ids": [],
      "budget_tier": "low"
    }
  }
  ```
- **Expected**: `crisis_response` track should be populated. `strategy_narrative` should include crisis mode warning. Budget-tier "low" penalises audience_growth rules.

### Test Case 3: High Budget Revenue Boost

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_high_budget",
    "discovery_output": {
      "persona": "high_value_whales",
      "vertical": "beauty",
      "maturity_score": 80,
      "initial_focus": "engagement"
    },
    "benchmark_output": {
      "health_score": 75,
      "gap_flags": [],
      "funnel_scores": {"acquisition": 80, "conversion": 70, "retention": 75},
      "peer_cluster_id": "beauty-high-us"
    },
    "constraints": {
      "available_channels": ["email", "sms", "push"],
      "active_flow_ids": [],
      "budget_tier": "high"
    }
  }
  ```
- **Expected**: Revenue rules boosted ×1.10, audience growth boosted ×1.05. No crisis track. High confidence scores.

---

## 6. Feedback Engine — UCB1 Multi-Armed Bandit

Ingests campaign performance and human feedback. Updates rule weights using UCB1 with 5-signal cluster-aware classification.

> **v2 Changes**: UCB1 `ucb1_score` + `exploration_bonus` in response, `total_rule_plays`, `feedback_summary` (Ollama), `merchant_context` for cluster-adaptive baselines, 5-signal voting (added `list_growth_rate`).

- **Endpoint**: `POST /engine/v1/feedback/process`
- **Headers**: `Content-Type: application/json`

### Test Case 1: Successful Campaign (Basic)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "strategy_id_code": "STR-01",
    "triggered_rule_id": "REV-01",
    "campaign_metrics": {
      "revenue_attributed": 1250.00,
      "open_rate": 0.45,
      "click_rate": 0.05,
      "conversion_rate": 0.03,
      "unsubscribe_rate": 0.001,
      "list_growth_rate": 0.015
    },
    "human_feedback": {
      "action": "approved",
      "comment": "Worked great — repeat customers responded well"
    }
  }
  ```
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X POST http://localhost:8000/engine/v1/feedback/process -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"strategy_id_code\":\"STR-01\",\"triggered_rule_id\":\"REV-01\",\"campaign_metrics\":{\"revenue_attributed\":1250.0,\"open_rate\":0.45,\"click_rate\":0.05,\"conversion_rate\":0.03,\"unsubscribe_rate\":0.001,\"list_growth_rate\":0.015},\"human_feedback\":{\"action\":\"approved\",\"comment\":\"Worked great\"}}"
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/engine/v1/feedback/process" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","strategy_id_code":"STR-01","triggered_rule_id":"REV-01","campaign_metrics":{"revenue_attributed":1250.0,"open_rate":0.45,"click_rate":0.05,"conversion_rate":0.03,"unsubscribe_rate":0.001,"list_growth_rate":0.015},"human_feedback":{"action":"approved","comment":"Worked great"}}'
  ```
- **Expected Output (v2 — UCB1)**:
  ```json
  {
    "merchant_id": "test_merchant_001",
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
        "total_rule_plays": 1
      }
    ],
    "retrain_triggered": false,
    "feedback_event_count": 1,
    "feedback_summary": "Strategy STR-01 (rule REV-01) exceeded expectations. Weight increased from 0.50 to 0.53. UCB1 exploration score: 1.914 — high exploration potential.",
    "model_version": "feedback-v2",
    "generated_at": "2026-03-30T08:15:00.000000+00:00"
  }
  ```

### Test Case 2: Failed Campaign (High Unsubscribes)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "strategy_id_code": "STR-02",
    "triggered_rule_id": "AUD-03",
    "campaign_metrics": {
      "revenue_attributed": 50.00,
      "open_rate": 0.10,
      "click_rate": 0.008,
      "conversion_rate": 0.001,
      "unsubscribe_rate": 0.025,
      "list_growth_rate": -0.01
    },
    "human_feedback": {
      "action": "rejected",
      "comment": "Too aggressive, caused list churn"
    }
  }
  ```
- **Expected**: `performance_label: "failure"` (high unsubscribes trigger hard failure). Weight decreases. Lower UCB1 exploitation score.

### Test Case 3: Cluster-Aware Classification (Beauty Merchant)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_beauty_merchant",
    "strategy_id_code": "STR-03",
    "triggered_rule_id": "ENG-01",
    "campaign_metrics": {
      "revenue_attributed": 180.00,
      "open_rate": 0.26,
      "click_rate": 0.06,
      "conversion_rate": 0.015,
      "unsubscribe_rate": 0.002,
      "list_growth_rate": 0.02
    },
    "merchant_context": {
      "cluster_id": "beauty-mid-us",
      "vertical": "beauty",
      "maturity_score": 55
    }
  }
  ```
- **Expected**: Uses beauty-specific baselines (open_rate threshold 0.25, not general 0.20). Classification may differ from the general baseline.

### Test Case 4: Retrain Trigger Test

Send 20+ feedback events to trigger model retraining:
```bash
# Repeat this 21 times to trigger retrain (RETRAIN_THRESHOLD=20)
for i in {1..21}; do
  curl -X POST http://localhost:8000/engine/v1/feedback/process \
    -H "Content-Type: application/json" \
    -d "{\"merchant_id\":\"test_retrain\",\"strategy_id_code\":\"STR-$i\",\"triggered_rule_id\":\"REV-01\",\"campaign_metrics\":{\"revenue_attributed\":500.0,\"open_rate\":0.30,\"click_rate\":0.04,\"conversion_rate\":0.02,\"unsubscribe_rate\":0.001,\"list_growth_rate\":0.01}}"
done
```
- **Expected**: On the 20th event, `retrain_triggered: true`. On the 21st, counter resets to 1.

---

## 7. Chat API — Intent-Routed Conversations

Conversational endpoint powered by Ollama with 2-step intent routing.

> **v2 Changes**: Smart intent classification routes queries to only relevant context. New `merchant_id` field, `intent` in response. Richer merchant-specific system prompt. New `/stream` SSE endpoint.

- **Endpoint**: `POST /api/v1/chat`
- **Headers**: `Content-Type: application/json`

### Test Case 1: Benchmark Intent (Performance Questions)

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "messages": [
      {
        "role": "user",
        "content": "Why is my retention score so low?"
      }
    ],
    "context": {
      "discovery_output": {
        "persona": "explorer",
        "vertical": "apparel",
        "maturity_score": 45,
        "initial_focus": "retention",
        "target_audience": "Women 25-40",
        "growth_signals": ["Growing email list"]
      },
      "benchmark_output": {
        "health_score": 55,
        "gap_flags": ["low_retention", "high_abandonment"],
        "funnel_scores": {"acquisition": 70, "conversion": 55, "retention": 40},
        "peer_cluster_id": "apparel-mid-us",
        "peer_percentile": 48,
        "missing_metrics": []
      }
    }
  }
  ```
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"messages\":[{\"role\":\"user\",\"content\":\"Why is my retention score so low?\"}],\"context\":{\"discovery_output\":{\"persona\":\"explorer\",\"vertical\":\"apparel\",\"maturity_score\":45},\"benchmark_output\":{\"health_score\":55,\"gap_flags\":[\"low_retention\",\"high_abandonment\"],\"funnel_scores\":{\"acquisition\":70,\"conversion\":55,\"retention\":40},\"peer_cluster_id\":\"apparel-mid-us\"}}}"
  ```
  **Powershell**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","messages":[{"role":"user","content":"Why is my retention score so low?"}],"context":{"discovery_output":{"persona":"explorer","vertical":"apparel","maturity_score":45},"benchmark_output":{"health_score":55,"gap_flags":["low_retention","high_abandonment"],"funnel_scores":{"acquisition":70,"conversion":55,"retention":40},"peer_cluster_id":"apparel-mid-us"}}}'
  ```
  **Powershell**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","messages":[{"role":"user","content":"Why is my retention score so low?"}],"context":{"benchmark_output":{"health_score":55,"gap_flags":["low_retention"]}}}' | Format-List
  ```
- **Expected Output**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "reply": "Your retention score of 40/100 is significantly below your apparel peer group. The primary driver is a high cart abandonment rate relative to peers in the apparel-mid-us cluster...",
    "intent": "benchmark"
  }
  ```

### Test Case 2: Strategy Intent

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "messages": [
      {
        "role": "user",
        "content": "What campaigns should I run to grow my email list?"
      }
    ],
    "context": {
      "strategy_output": {
        "tracks": {
          "core_growth": [
            {"rule_id": "AUD-01", "description": "Pop-up signup incentive campaign"}
          ]
        },
        "strategy_narrative": "Focus on audience growth to expand reach."
      }
    }
  }
  ```
- **Expected**: `intent: "strategy"` — injects only strategy track summaries, not benchmark or discovery data.

### Test Case 3: Discovery Intent

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "messages": [
      { "role": "user", "content": "Who are my best customers?" }
    ],
    "context": {
      "discovery_output": {
        "persona": "loyalist",
        "vertical": "beauty",
        "maturity_score": 72,
        "target_audience": "Women 25-45 skincare enthusiasts",
        "price_point_tier": "premium",
        "growth_signals": ["High repeat rate", "Strong LTV"],
        "churn_risk_level": "low",
        "dominant_channel": "email"
      }
    }
  }
  ```
- **Expected**: `intent: "discovery"` — injects persona, target audience, growth signals, etc.

### Test Case 4: Multi-Turn Conversation

- **JSON Body**:
  ```json
  {
    "merchant_id": "test_merchant_001",
    "messages": [
      { "role": "user", "content": "What's my biggest weakness?" },
      { "role": "assistant", "content": "Your retention score is the weakest at 40/100..." },
      { "role": "user", "content": "How do I fix it?" }
    ],
    "context": {
      "benchmark_output": {
        "health_score": 55,
        "gap_flags": ["low_retention"],
        "funnel_scores": {"acquisition": 70, "conversion": 55, "retention": 40}
      }
    }
  }
  ```
- **Expected**: AI should provide retention-focused recommendations, maintaining context from the first exchange.

---

## 8. Chat SSE Streaming

Streams chat responses token-by-token for a faster perceived response time.

- **Endpoint**: `POST /api/v1/chat/stream`
- **Response**: `text/event-stream` (Server-Sent Events)

- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d "{\"merchant_id\":\"test_merchant_001\",\"messages\":[{\"role\":\"user\",\"content\":\"Give me a quick overview of my store performance\"}],\"context\":{\"benchmark_output\":{\"health_score\":55,\"gap_flags\":[\"low_retention\"]}}}"
  ```
  **Powershell**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/stream" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"merchant_id":"test_merchant_001","messages":[{"role":"user","content":"Give me a quick overview of my store performance"}],"context":{"benchmark_output":{"health_score":55,"gap_flags":["low_retention"]}}}'
  ```
- **Expected Output** (streamed):
  ```
  data: [INTENT:benchmark]

  data: Your

  data:  store

  data:  is

  data:  performing

  ...

  data: [DONE]
  ```

---

## 9. Chat Status (Ollama Health)

Checks if Ollama LLM is locally running and available.

- **Endpoint**: `GET /api/v1/chat/status`
- **Terminal (cURL / cmd.exe)**:
  ```bash
  curl -X GET http://localhost:8000/api/v1/chat/status
  ```
- **PowerShell (Invoke-RestMethod)**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/status" -Method Get
  ```
- **Expected Output**:
  ```json
  {
    "ollama_available": true,
    "model": "llama3.2:3b",
    "base_url": "http://localhost:11434"
  }
  ```

---

## 10. Testing Checklist — v2 Verification

Use this checklist to verify all v2 upgrades are working:

| # | Test | Endpoint | What to Verify |
|---|---|---|---|
| 1 | Winsorization | Benchmark | POST extreme outlier data (`new_customer_rate: 5.0`) → score should NOT exceed ~95 |
| 2 | Null handling | Benchmark | POST with missing metrics → `missing_metrics` populated, scores ~50 |
| 3 | Crisis mode | Strategy | POST with `health_score: 20` + 5 gap flags → `crisis_response` track populated |
| 4 | Budget scoring | Strategy | POST with `budget_tier: "low"` → audience_growth rules penalised |
| 5 | LLM fallback | Discovery | POST with `vertical_confidence: 0.3` → Ollama enrichment fires |
| 6 | Deep profile | Discovery | POST with `price_hint` + `audience_hint` → returns full deep profile |
| 7 | UCB1 scores | Feedback | POST 3+ events → `ucb1_score` and `exploration_bonus` in response |
| 8 | Cluster baselines | Feedback | POST with `merchant_context.cluster_id: "beauty-mid-us"` → uses beauty baselines |
| 9 | Intent routing | Chat | Ask "What are my worst KPIs?" → `intent: "benchmark"` |
| 10 | Streaming | Chat/Stream | POST to `/stream` → SSE data lines appear |
| 11 | Retrain trigger | Feedback | POST 20+ events → `retrain_triggered: true` |
| 12 | Persona tiers | Discovery | POST AOV > 300 + repeat > 0.25 → `persona: "high_value_whales"` |
| 13 | Health narrative | Benchmark | Response includes non-empty `health_summary` |
| 14 | Strategy narrative | Strategy | Response includes non-empty `strategy_narrative` |
| 15 | Personalisation | Strategy | Items with `ollama_personalized: true` when Ollama is available |
