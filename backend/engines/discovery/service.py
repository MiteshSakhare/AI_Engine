"""
Discovery Engine — Service (orchestrator) v2.

Major upgrades:
  - LLM Fallback for Persona: triggers when persona_confidence < 0.55
  - LLM Fallback for Maturity: validates/corrects score in grey zone (35-65)
  - Deep profile enrichment: Ollama returns full 9-key JSON including
    target_audience, price_point_tier, key_value_proposition, growth_signals,
    dominant_channel, churn_risk_level
  - Improved confidence scoring: weighted blend of all 3 model signals
  - Fixed datetime.utcnow() deprecation
  - Churn risk computed deterministically from maturity + repeat_rate

File: backend/engines/discovery/service.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from engines.discovery.schemas import DiscoveryRequest, DiscoveryResponse
from engines.discovery.features import get_feature_vector, features_to_array
from engines.discovery.models.persona import PersonaClassifier
from engines.discovery.models.maturity import MaturityScorer
from engines.discovery.models.vertical import VerticalClassifier
from engines.discovery.explainer import generate_reasoning
from shared.config import settings
from shared.model_registry import model_registry
from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.discovery.service")

# Confidence thresholds for LLM fallback
PERSONA_CONFIDENCE_THRESHOLD  = 0.55
VERTICAL_CONFIDENCE_THRESHOLD = 0.50
MATURITY_GREY_ZONE             = (35, 65)   # Ollama validates maturity within this range


class DiscoveryService:
    """Orchestrates the Discovery Engine pipeline."""

    def __init__(self) -> None:
        persona_model   = model_registry.load_model("discovery.persona")
        maturity_model  = model_registry.load_model("discovery.maturity")
        vertical_model  = model_registry.load_model("discovery.vertical")

        self.persona_classifier  = PersonaClassifier(model=persona_model)
        self.maturity_scorer     = MaturityScorer(model=maturity_model)
        self.vertical_classifier = VerticalClassifier(model=vertical_model)

    async def profile(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """
        Full discovery pipeline:
        1. Load features
        2. Run 3 ML models (persona, maturity, vertical)
        3. LLM fallback for low-confidence predictions
        4. Deep profile enrichment (always run if features or onboarding data present)
        5. Compute churn risk, initial focus, and composite confidence
        6. Generate reasoning text (SHAP or heuristic + Ollama)
        7. Return complete merchant profile
        """
        logger.info("Running discovery for merchant %s", request.merchant_id)

        # ── 1. Feature vector ────────────────────────────
        features = get_feature_vector(
            merchant_id=request.merchant_id,
            request_features=request.feature_vector,
        )
        feature_array = features_to_array(features)

        # ── 2. Model inference ───────────────────────────
        persona_label, persona_confidence   = self.persona_classifier.predict(feature_array)
        maturity_score                       = self.maturity_scorer.predict(feature_array)
        vertical_hint = (
            request.onboarding_responses.vertical_hint
            if request.onboarding_responses else None
        )
        vertical_label, vertical_confidence = self.vertical_classifier.predict(
            feature_array, vertical_hint=vertical_hint,
        )

        # ── 3 & 4. LLM Enrichment ────────────────────────
        # Always enrich if: data is present OR low model confidence
        should_enrich = (
            request.feature_vector is not None
            or request.onboarding_responses is not None
            or vertical_confidence < VERTICAL_CONFIDENCE_THRESHOLD
            or persona_confidence < PERSONA_CONFIDENCE_THRESHOLD
        )

        # Deep profile defaults
        seasonality         = "neutral"
        catalog_complexity  = "low"
        target_audience     = ""
        price_point_tier    = "mid"
        key_value_prop      = ""
        growth_signals: list[str] = []
        dominant_channel    = "email"

        if should_enrich:
            enriched = await self._llm_enrich_profile(
                request, features, vertical_label, persona_label, maturity_score,
                vertical_confidence, persona_confidence,
            )

            if enriched:
                # Vertical override
                if vertical_confidence < VERTICAL_CONFIDENCE_THRESHOLD and "vertical" in enriched:
                    vertical_label      = enriched["vertical"]
                    vertical_confidence = 0.85  # Assigned confidence for LLM fallback

                # Persona override
                if persona_confidence < PERSONA_CONFIDENCE_THRESHOLD and "persona" in enriched:
                    persona_label      = enriched["persona"]
                    persona_confidence = 0.80

                # Maturity correction in grey zone
                if MATURITY_GREY_ZONE[0] <= maturity_score <= MATURITY_GREY_ZONE[1]:
                    llm_maturity = enriched.get("maturity_score")
                    if isinstance(llm_maturity, (int, float)):
                        maturity_score = max(0, min(100, int(llm_maturity)))

                # Deep profile fields
                seasonality         = enriched.get("seasonality", "neutral")
                catalog_complexity  = enriched.get("catalog_complexity", "low")
                target_audience     = enriched.get("target_audience", "")
                price_point_tier    = enriched.get("price_point_tier", "mid")
                key_value_prop      = enriched.get("key_value_proposition", "")
                growth_signals      = enriched.get("growth_signals", [])
                dominant_channel    = enriched.get("dominant_channel", "email")

        # ── 5. Derived signals ───────────────────────────
        repeat_rate   = features.get("repeat_rate", 0)
        initial_focus = self._determine_initial_focus(maturity_score, repeat_rate)
        churn_risk    = self._determine_churn_risk(maturity_score, repeat_rate)

        # Composite confidence: weighted blend of all 3 model signals
        maturity_normalised = maturity_score / 100.0
        confidence_score = round(
            (persona_confidence * 0.45)
            + (vertical_confidence * 0.35)
            + (maturity_normalised * 0.20),
            2,
        )

        # ── 6. Reasoning ─────────────────────────────────
        reasoning = await generate_reasoning(
            persona=persona_label,
            vertical=vertical_label,
            maturity_score=maturity_score,
            initial_focus=initial_focus,
            features=features,
        )

        # ── 7. Response ──────────────────────────────────
        return DiscoveryResponse(
            merchant_id=request.merchant_id,
            persona=persona_label,
            vertical=vertical_label,
            seasonality=seasonality,
            catalog_complexity=catalog_complexity,
            maturity_score=maturity_score,
            initial_focus=initial_focus,
            confidence_score=confidence_score,
            reasoning=reasoning,
            target_audience=target_audience,
            price_point_tier=price_point_tier,
            key_value_proposition=key_value_prop,
            growth_signals=growth_signals,
            dominant_channel=dominant_channel,
            churn_risk_level=churn_risk,
            model_version=f"discovery-{settings.MODEL_VERSION}",
            generated_at=datetime.now(timezone.utc),
        )

    async def _llm_enrich_profile(
        self,
        request: DiscoveryRequest,
        features: dict,
        current_vertical: str,
        current_persona: str,
        current_maturity: int,
        vertical_confidence: float,
        persona_confidence: float,
    ) -> dict:
        """
        Use Ollama to extract a complete deep profile from merchant data.

        Returns a JSON object with up to 9 keys. Uses low temperature (0.1)
        for structured JSON extraction to minimise hallucination.
        """
        system_prompt = (
            "You are a merchant profiling AI. Output strictly valid JSON only. "
            "No markdown, no code blocks, no explanations. Raw JSON object only."
        )

        onboarding_data = (
            request.onboarding_responses.model_dump()
            if request.onboarding_responses else {}
        )

        prompt = (
            f"Analyze this Shopify merchant data and return a JSON profile:\n"
            f"Features: {json.dumps(features, default=str)}\n"
            f"Onboarding: {json.dumps(onboarding_data)}\n"
            f"Current vertical guess: {current_vertical} (confidence: {vertical_confidence:.2f})\n"
            f"Current persona guess: {current_persona} (confidence: {persona_confidence:.2f})\n"
            f"Current maturity score: {current_maturity}/100\n\n"
            "Return a JSON object with these keys (all required):\n"
            "1. 'vertical': string — industry vertical (apparel/beauty/food_beverage/electronics/health_wellness/home_goods/pet_supplies/other)\n"
            "2. 'persona': string — customer archetype (loyalist/value_seeker/explorer/bargain_hunter/discount_driven/high_value_whales)\n"
            "3. 'maturity_score': integer 0-100 — store operational maturity\n"
            "4. 'seasonality': string — high/medium/low/neutral\n"
            "5. 'catalog_complexity': string — high/medium/low (based on product variety)\n"
            "6. 'target_audience': string — 1-sentence audience description\n"
            "7. 'price_point_tier': string — budget/mid/premium/luxury\n"
            "8. 'key_value_proposition': string — 1-sentence what makes this merchant unique\n"
            "9. 'growth_signals': array of strings — up to 3 positive growth indicators observed\n"
            "10. 'dominant_channel': string — email/social/both/paid\n"
            "11. 'churn_risk_level': string — low/medium/high"
        )

        try:
            response_text = await ollama_client.generate(
                prompt, system=system_prompt, temperature=0.1
            )
            if response_text:
                clean_json = (
                    response_text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                return json.loads(clean_json)
        except json.JSONDecodeError as e:
            logger.warning("LLM profile JSON parse failed: %s", e)
        except Exception as e:
            logger.warning("LLM profile enrich failed: %s", e)

        return {}

    @staticmethod
    def _determine_initial_focus(maturity_score: int, repeat_rate: float) -> str:
        """
        Determine initial marketing focus area.

        IF maturity_score < 40 → 'acquisition'  (grow the customer base first)
        IF repeat_rate < 0.20  → 'retention'    (stop the churn leaking)
        ELSE                   → 'engagement'   (deepen existing relationships)
        """
        if maturity_score < 40:
            return "acquisition"
        if repeat_rate < 0.20:
            return "retention"
        return "engagement"

    @staticmethod
    def _determine_churn_risk(maturity_score: int, repeat_rate: float) -> str:
        """
        Compute churn risk level from maturity and repeat purchase rate.

        High risk: low maturity AND low repeat rate
        Low risk:  high maturity OR high repeat rate
        """
        if maturity_score < 35 and repeat_rate < 0.15:
            return "high"
        if maturity_score >= 65 or repeat_rate >= 0.30:
            return "low"
        return "medium"


# Singleton
discovery_service = DiscoveryService()
