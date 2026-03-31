"""
Strategy Engine — Ollama Personalizer v2.

Batch-rewrites strategy descriptions to be merchant-specific.

Instead of generic descriptions like "Low returning customer rate",
merchants see: "Your beauty customers are churning faster than your peers —
a Winback campaign targeting lapsed loyalists could recover 15-20% of them."

Design:
  - Single Ollama call for ALL items (not one per item) — minimises latency.
  - Falls back to original descriptions if Ollama is unavailable.
  - Uses low temperature (0.4) for factual but readable output.

File: backend/engines/strategy/personalizer.py
"""

from __future__ import annotations

import json
import logging
from typing import List

from engines.strategy.schemas import StrategyItem
from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.strategy.personalizer")


async def personalize_strategy_items(
    items: List[StrategyItem],
    persona: str,
    vertical: str,
    maturity_score: int,
    budget_tier: str = "mid",
) -> List[StrategyItem]:
    """
    Rewrite strategy item descriptions using Ollama with merchant context.

    Makes a SINGLE Ollama call for ALL items in batch to minimise latency.
    Returns the same list with descriptions rewritten (ollama_personalized=True)
    or the original list if Ollama is unavailable or fails.
    """
    if not items or not ollama_client.available:
        return items

    # Build compact item list for the prompt
    item_list = [
        {"id": item.rule_id, "description": item.description, "category": item.category}
        for item in items
    ]

    system_prompt = (
        "You are Bravola's strategy copywriter. Rewrite marketing strategy descriptions "
        "to be specific to this merchant's context. Be concise (1-2 sentences per item), "
        "actionable, and data-informed. Do NOT use markdown or bullet points. "
        "Output strictly valid JSON only — an array of objects."
    )

    prompt = (
        f"Merchant profile:\n"
        f"  Persona: {persona}\n"
        f"  Vertical: {vertical}\n"
        f"  Maturity score: {maturity_score}/100\n"
        f"  Budget tier: {budget_tier}\n\n"
        f"Rewrite each strategy description to be specific to this {vertical} merchant "
        f"with a '{persona}' customer base. Keep the same intent but make it personal.\n\n"
        f"Input strategies:\n{json.dumps(item_list, indent=2)}\n\n"
        "Return a JSON array with objects containing 'id' and 'description' fields only. "
        "Example: [{\"id\": \"REV-01\", \"description\": \"Your personalized description here.\"}]"
    )

    try:
        response_text = await ollama_client.generate(
            prompt, system=system_prompt, temperature=0.4
        )
        if not response_text:
            return items

        clean_json = (
            response_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        personalized_list = json.loads(clean_json)

        # Build lookup: rule_id → new description
        desc_map = {
            entry["id"]: entry["description"]
            for entry in personalized_list
            if "id" in entry and "description" in entry
        }

        # Apply personalised descriptions
        updated_items = []
        for item in items:
            if item.rule_id in desc_map:
                updated_item = item.model_copy(
                    update={
                        "description": desc_map[item.rule_id],
                        "ollama_personalized": True,
                    }
                )
                updated_items.append(updated_item)
            else:
                updated_items.append(item)

        logger.info(
            "Personalised %d/%d strategy descriptions for %s/%s merchant",
            len(desc_map), len(items), persona, vertical,
        )
        return updated_items

    except json.JSONDecodeError as e:
        logger.warning("Strategy personalizer JSON parse failed: %s", e)
    except Exception as e:
        logger.warning("Strategy personalizer failed: %s", e)

    return items  # Fallback: original descriptions
