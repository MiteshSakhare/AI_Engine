# Bravola AI Engine — Master Improvement Plan v2.0
## Real-World SaaS Overhaul

> [!IMPORTANT]
> This plan was created after a **full deep-read** of every engine file, schema, model, and explainer in the project. Every change below is grounded in the **actual current code**, not assumptions.

> [!NOTE]
> **Status: ✅ ALL 7 PHASES COMPLETE** — All upgrades have been implemented and verified in the codebase. README and API Testing Guide updated to reflect v2 changes.

---

## Executive Summary

After analyzing the entire backend, I identified **5 layers** of improvements across 6 areas. The project is well-structured but had significant gaps in math robustness, Ollama integration intelligence, ML learning depth, and discovery completeness that prevented it from being a true production-grade SaaS. This plan addressed all of them systematically.

---

## Part 1: Discovery Engine — "Know Everything About Any Merchant" ✅ COMPLETE

### Gaps Found & Fixed:
- ✅ `service.py` — LLM fallback for Persona when `persona_confidence < 0.55`
- ✅ `service.py` — LLM fallback for Maturity in grey zone (35-65)
- ✅ `schemas.py` — Added `target_audience`, `price_point_tier`, `key_value_proposition`, `growth_signals`, `dominant_channel`, `churn_risk_level`
- ✅ `schemas.py` — Added `price_hint`, `audience_hint`, `primary_challenge` to OnboardingResponses
- ✅ `persona.py` — Named-dict feature access via `_to_feature_dict()`, 6 persona tiers, confidence decay
- ✅ `maturity.py` — Input validation (clamp to non-negative), 5th component (email_engagement), named-dict access
- ✅ `service.py` — Weighted confidence: `(persona×0.45) + (vertical×0.35) + (maturity×0.20)`
- ✅ `service.py` — Fixed `datetime.utcnow()` → `datetime.now(timezone.utc)`
- ✅ `service.py` — Deep 11-key JSON enrichment via Ollama with temperature=0.1

---

## Part 2: Benchmark Engine — "Accurate, Real-World, No Nulls" ✅ COMPLETE

### Gaps Found & Fixed:
- ✅ `health_score.py` — Winsorization: clips at ±2σ before Z-score via `_winsorise()`
- ✅ `health_score.py` — Null/Missing handling: `_get_safe_val()` substitutes peer_mean for None/absent values
- ✅ `health_score.py` — 4th acquisition metric: `opt_in_rate`
- ✅ `clustering.py` — Expanded from 4 → 12 named clusters with maturity tiers
- ✅ `clustering.py` — 7 vertical keyword categories with smart matching
- ✅ `explainer.py` — Fixed silent `median_val == 0` skip → reports "unavailable" or "review data quality"
- ✅ `explainer.py` — Added `generate_health_summary()` — Ollama-powered narrative
- ✅ `service.py` — Beta CDF percentile via `scipy.stats.beta.cdf()` with graceful fallback
- ✅ `service.py` — Fixed `datetime.utcnow()` deprecation
- ✅ `schemas.py` — Added `health_summary`, `missing_metrics`, `percentile_method`

---

## Part 3: Strategy Engine — "Multi-Track, Dynamic, Solving Real Problems" ✅ COMPLETE

### Gaps Found & Fixed:
- ✅ `service.py` — **Fixed critical bug**: category routing uses exact enum values (`"email_engagement"` not `"Email"`)
- ✅ `service.py` — Dynamic **Crisis Response** track: triggers on health < 40 or 3+ gap_flags
- ✅ `service.py` — Ollama `strategy_narrative` executive summary
- ✅ `personalizer.py` — **NEW FILE**: batch Ollama rewriting of descriptions with merchant context
- ✅ `scorer.py` — Data-driven MVP lift: `lift = 0.3 + (global×0.5) + (normalised×0.2)`
- ✅ `scorer.py` — Budget-aware scoring: low→penalise audience_growth, high→boost revenue
- ✅ `scorer.py` — 3-key sort: score DESC → base_weight DESC → rule_id ASC
- ✅ `schemas.py` — Added `crisis_response` track, `strategy_narrative`, `total_triggered`, `tracks_populated`, `ollama_personalized`

---

## Part 4: Feedback Engine — "UCB1 Multi-Armed Bandit + Adaptive Learning" ✅ COMPLETE

### Gaps Found & Fixed:
- ✅ `weight_updater.py` — Full UCB1 implementation with `_plays`, `_rewards`, `get_ucb1_score()`, `get_all_ucb1_scores()`
- ✅ `weight_updater.py` — `record_play()` for tracking recommendation frequency
- ✅ `classifier.py` — 5-signal voting (added `list_growth_rate`)
- ✅ `classifier.py` — Cluster-adaptive baselines for 6 verticals via `_get_baseline(cluster_id)`
- ✅ `classifier.py` — Stricter: success requires 4/5 signals (was 3/4)
- ✅ `schemas.py` — Added `ucb1_score`, `exploration_bonus`, `total_rule_plays` to WeightUpdate
- ✅ `schemas.py` — Added `merchant_context` to FeedbackRequest, `feedback_summary` to response
- ✅ `service.py` — Passes cluster_id to classifier, includes UCB1 data in response, generates feedback summary

---

## Part 5: Ollama Integration — "Smart Intent Routing" ✅ COMPLETE

### Gaps Found & Fixed:
- ✅ `ollama_client.py` — Temperature parameter on `generate()` and `chat()`
- ✅ `ollama_client.py` — `generate_streaming()` async generator for SSE
- ✅ `ollama_client.py` — `classify_intent()` with validation against VALID_INTENTS
- ✅ `ollama_client.py` — Configurable timeout from settings
- ✅ `chat.py` — 2-step intent routing pipeline (classify → inject relevant context)
- ✅ `chat.py` — 5 context extractors (benchmark, strategy, discovery, feedback, general)
- ✅ `chat.py` — `/api/v1/chat/stream` SSE endpoint
- ✅ `chat.py` — Merchant-specific system prompt with health score and gap count

---

## Part 6: Architecture & Code Quality ✅ COMPLETE

### Issues Found & Fixed:
- ✅ `config.py` — Added: `UCB1_C`, `OLLAMA_TIMEOUT_SECONDS`, `OLLAMA_TEMPERATURE_JSON/REASONING/CHAT`, `MAX_STRATEGIES_PER_TRACK`, `TOTAL_STRATEGY_CANDIDATES`
- ✅ `config.py` — `MODEL_VERSION` bumped to `v2`
- ✅ All service files — Fixed `datetime.utcnow()` → `datetime.now(timezone.utc)` in discovery, benchmark, strategy, feedback

---

## Execution Summary

| Phase | Scope | Status | Files Changed |
|-------|-------|--------|---------------|
| **Phase 1** | Benchmark Math | ✅ COMPLETE | `health_score.py`, `clustering.py`, `explainer.py`, `service.py`, `schemas.py` |
| **Phase 2** | Feedback UCB1 | ✅ COMPLETE | `weight_updater.py`, `classifier.py`, `schemas.py`, `service.py` |
| **Phase 3** | Discovery Deep Profiling | ✅ COMPLETE | `service.py`, `schemas.py`, `persona.py`, `maturity.py` |
| **Phase 4** | Strategy Engine Fix + Dynamic Tracks | ✅ COMPLETE | `service.py`, `scorer.py`, `schemas.py`, `personalizer.py` (NEW) |
| **Phase 5** | Smart Ollama Chat Routing | ✅ COMPLETE | `chat.py`, `ollama_client.py` |
| **Phase 6** | Config + Architecture | ✅ COMPLETE | `config.py`, all service files |
| **Phase 7** | Documentation Update | ✅ COMPLETE | `README.md`, `API_TESTING_GUIDE.md`, `implementation_plan.md` |

---

## Suggestions for Further Upgrades (Future Scope)

> [!TIP]
> These are NOT in the current plan but recommended for the next iteration.

1. **Persistent Weight Store (Database)**: Move `_weight_store`, `_plays`, `_rewards` from in-memory dicts to a PostgreSQL table. Create a `rule_weights` table via Alembic migration. Critical for production reliability.

2. **Streaming Chat UI Integration**: The new `/api/v1/chat/stream` SSE endpoint will require a frontend update to switch from `fetch` to `EventSource`. Coordinate with your Node.js/React team.

3. **Model Drift Monitoring**: Add a background Celery task that runs weekly, computes average UCB1 reward rates across all rules, and alerts (log/email) if any rule's reward rate drops below 0.3 for 20+ plays.

4. **Merchant Analytics Dashboard**: Add a new `/api/v1/analytics/{merchant_id}/summary` endpoint that aggregates discovery + benchmark + strategy + feedback data into a single merchant health report.

5. **A/B Testing Module**: Reserve 10% of strategy recommendations to be randomly swapped with the next-best rule to build a proper held-out control group for statistical significance testing.

6. **Rate Limiting**: Add `slowapi` rate limiter to `/engine/v1/strategy/generate` and `/api/v1/chat` to protect AI resources from abuse.

7. **OpenAPI Client Generation**: Use `openapi-ts` or `orval` to auto-generate React Query hooks from `/engine/openapi.json` for the frontend team.

8. **`asyncio.to_thread()` for Model Registry**: Wrap `model_registry.start_polling()` in `asyncio.to_thread()` to prevent event loop blocking during startup.

---

## Verification Plan

### Automated Tests
After each phase, run:
```bash
pytest tests/unit/test_benchmark_health_score.py  # Phase 1
pytest tests/unit/test_feedback_weight_updater.py  # Phase 2
pytest tests/unit/test_discovery_service.py        # Phase 3
pytest tests/unit/test_strategy_scorer.py          # Phase 4
pytest tests/integration/                          # All phases
```

### Manual API Verification
1. **Benchmark**: POST extreme outlier data (e.g., `new_customer_rate: 5.0`) — should clamp to cluster max, not produce score > 100
2. **Strategy**: POST request for merchant with `health_score: 20` — should trigger Crisis Response track
3. **Discovery**: POST with `vertical_confidence: 0.3` — should trigger Ollama fallback and return `target_audience`, `price_point_tier`
4. **Chat**: Ask "What are my worst performing metrics?" — should trigger `benchmark` intent, inject only benchmark context
5. **Feedback**: POST 25+ feedback events → confirm `retrain_triggered: true` and UCB1 scores appear in response
