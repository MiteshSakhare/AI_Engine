"""
Chat API — Smart Intent Routing v2.

Two-step routing pipeline:
  1. classify_intent() → fast, low-token call to identify the topic
  2. Inject ONLY the relevant context section into the system prompt
     (prevents context window saturation with irrelevant data)

Routes:
  benchmark  → health_score, gap_flags, funnel_scores
  strategy   → track summaries (rule IDs + descriptions only)
  discovery  → persona, vertical, maturity_score, growth_signals
  feedback   → recent performance_labels, weight trends
  general    → brief merchant overview (4 key stats only)

Also adds:
  - /api/v1/chat/stream  → SSE streaming endpoint
  - Richer merchant-specific system prompt (health score + primary problem)
  - temperature=0.8 for all chat responses (appropriately conversational)

File: backend/api/chat.py
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.ollama_client import ollama_client

logger = logging.getLogger("bravola.api.chat")

router = APIRouter(tags=["chat"])


# ── Request/Response schemas ─────────────────────────────

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    merchant_id: str
    messages: List[ChatMessage]
    context: Optional[Dict[str, Any]] = None   # Engine output data


class ChatResponse(BaseModel):
    merchant_id: str
    reply: str
    intent: str    # The classified intent topic


class ChatStatusResponse(BaseModel):
    ollama_available: bool
    model: str
    base_url: str


# ── Context extractors ───────────────────────────────────

def _extract_benchmark_context(ctx: Dict) -> str:
    """Extract benchmark-relevant fields only."""
    bm = ctx.get("benchmark_output") or ctx
    health     = bm.get("health_score", "N/A")
    funnel     = bm.get("funnel_scores") or {}
    gaps       = bm.get("gap_flags", [])[:3]   # Top 3 gaps only
    cluster    = bm.get("peer_cluster_id", "N/A")
    percentile = bm.get("peer_percentile", "N/A")
    missing    = bm.get("missing_metrics", [])

    funnel_str = ", ".join(f"{k}: {v}/100" for k, v in funnel.items()) if funnel else "N/A"
    gaps_str   = "; ".join(gaps) if gaps else "none identified"
    missing_str = f" (Missing data: {', '.join(missing[:3])})" if missing else ""

    return (
        f"[BENCHMARK] Health score: {health}/100 (vs peers in {cluster}, ~{percentile}th percentile). "
        f"Funnel breakdown: {funnel_str}. "
        f"Top gaps: {gaps_str}."
        f"{missing_str}"
    )


def _extract_strategy_context(ctx: Dict) -> str:
    """Extract strategy track summaries (compact — rule IDs + descriptions only)."""
    strategy = ctx.get("strategy_output") or {}
    tracks   = strategy.get("tracks") or {}

    def _fmt_track(name: str) -> str:
        items = tracks.get(name, [])
        if not items:
            return ""
        top_items = items[:3]  # Limit to top 3 per track to save tokens
        lines = [f"  • [{i['rule_id']}] {i['description'][:80]}..." for i in top_items]
        return f"\n{name.replace('_', ' ').title()} ({len(items)} total):\n" + "\n".join(lines)

    narrative = strategy.get("strategy_narrative", "")
    tracks_str = (
        _fmt_track("quick_wins")
        + _fmt_track("core_growth")
        + _fmt_track("retention_rescue")
        + _fmt_track("crisis_response")
    )

    return f"[STRATEGY]{tracks_str}" + (f"\nNarrative: {narrative}" if narrative else "")


def _extract_discovery_context(ctx: Dict) -> str:
    """Extract discovery profile — merchant identity data."""
    disc = ctx.get("discovery_output") or ctx
    return (
        f"[DISCOVERY] Merchant profile:\n"
        f"  Persona: {disc.get('persona', 'N/A')}\n"
        f"  Vertical: {disc.get('vertical', 'N/A')}\n"
        f"  Maturity: {disc.get('maturity_score', 'N/A')}/100\n"
        f"  Target audience: {disc.get('target_audience', 'N/A')}\n"
        f"  Price tier: {disc.get('price_point_tier', 'N/A')}\n"
        f"  Growth signals: {', '.join(disc.get('growth_signals', [])) or 'N/A'}\n"
        f"  Churn risk: {disc.get('churn_risk_level', 'N/A')}\n"
        f"  Dominant channel: {disc.get('dominant_channel', 'N/A')}"
    )


def _extract_feedback_context(ctx: Dict) -> str:
    """Extract feedback data — recent performance outcomes."""
    fb = ctx.get("feedback_output") or {}
    label    = fb.get("performance_label", "N/A")
    summary  = fb.get("feedback_summary", "")
    updates  = fb.get("weight_updates", [])
    ucb1_info = ""
    if updates:
        top = updates[0]
        ucb1_info = (
            f"Latest rule ({top.get('rule_id', 'N/A')}): "
            f"weight {top.get('old_weight', 'N/A')}→{top.get('new_weight', 'N/A')}, "
            f"UCB1: {top.get('ucb1_score', 'N/A')}, plays: {top.get('total_rule_plays', 'N/A')}."
        )

    return (
        f"[FEEDBACK] Recent performance: {label}. "
        f"{ucb1_info} "
        f"{summary}"
    )


def _extract_general_context(ctx: Dict) -> str:
    """Extract a brief merchant overview — 4 key stats only."""
    disc    = ctx.get("discovery_output") or {}
    bm      = ctx.get("benchmark_output") or {}
    persona = disc.get("persona", "unknown")
    vertical = disc.get("vertical", "unknown")
    health  = bm.get("health_score", "N/A")
    focus   = disc.get("initial_focus", "N/A")

    return (
        f"[OVERVIEW] This is a {vertical} merchant ({persona} customer base). "
        f"Current health score: {health}/100. "
        f"Recommended focus: {focus}."
    )


def _route_context(intent: str, context: Dict) -> str:
    """Route context extraction based on classified intent."""
    extractors = {
        "benchmark": _extract_benchmark_context,
        "strategy":  _extract_strategy_context,
        "discovery": _extract_discovery_context,
        "feedback":  _extract_feedback_context,
    }
    extractor = extractors.get(intent, _extract_general_context)
    try:
        return extractor(context)
    except Exception as exc:
        logger.warning("Context extraction failed for intent '%s': %s", intent, exc)
        return _extract_general_context(context)


def _build_system_prompt(context: Dict, intent: str) -> str:
    """
    Build a merchant-specific system prompt.

    Injects ONLY the context section relevant to the classified intent,
    plus a consistent identity block and merchant overview header.
    """
    disc    = context.get("discovery_output") or {}
    bm      = context.get("benchmark_output") or {}
    health  = bm.get("health_score", "N/A")
    persona = disc.get("persona", "your customer base")
    vertical = disc.get("vertical", "your industry")
    gap_count = len(bm.get("gap_flags", []))

    # Merchant intro paragraph (always included — < 50 tokens)
    intro = (
        f"This merchant is in the {vertical} space with a '{persona}' customer persona. "
        f"Their current health score is {health}/100"
    )
    if gap_count:
        intro += f" with {gap_count} active KPI gap(s) identified"
    intro += "."

    # Intent-specific context
    relevant_context = _route_context(intent, context)

    return (
        "You are Bravola AI — an expert e-commerce growth marketing strategist. "
        "You provide actionable, specific insights for Shopify merchants. "
        "Be concise, confident, and data-driven. Never say you don't know — "
        "use the data provided to give the best possible recommendation.\n\n"
        f"{intro}\n\n"
        "Relevant data for this query:\n"
        f"{relevant_context}"
    )


# ── Endpoints ────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint with 2-step intent routing.

    Step 1: Classify the intent of the last user message.
    Step 2: Inject only the relevant context section.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    # ── Step 1: Intent classification ────────────────────
    last_user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"),
        "",
    )

    intent = "general"
    context = request.context or {}

    if last_user_msg and context:
        intent = await ollama_client.classify_intent(last_user_msg)
        logger.info(
            "merchant=%s intent=%s query='%s...'",
            request.merchant_id, intent, last_user_msg[:60],
        )

    # ── Step 2: Build system prompt with focused context ─
    system_prompt = _build_system_prompt(context, intent) if context else (
        "You are Bravola AI — an expert e-commerce growth marketing strategist. "
        "Help the merchant with their marketing questions."
    )

    # ── Step 3: Multi-turn chat ───────────────────────────
    conv_messages = [{"role": m.role, "content": m.content} for m in request.messages]
    reply = await ollama_client.chat(
        messages=conv_messages,
        system=system_prompt,
        temperature=0.8,
        max_tokens=600,
    )

    if not reply:
        reply = "I wasn't able to generate a response. Please try again."

    return ChatResponse(
        merchant_id=request.merchant_id,
        reply=reply,
        intent=intent,
    )


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Streams tokens progressively for a responsive chat experience.
    Connect with EventSource on the frontend:
      const es = new EventSource('/api/v1/chat/stream', {...})
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    last_user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"),
        "",
    )

    context = request.context or {}
    intent  = "general"
    if last_user_msg and context:
        intent = await ollama_client.classify_intent(last_user_msg)

    system_prompt = _build_system_prompt(context, intent) if context else (
        "You are Bravola AI — an expert e-commerce growth marketing strategist."
    )

    async def sse_generator():
        yield f"data: [INTENT:{intent}]\n\n"
        async for token in ollama_client.generate_streaming(
            prompt=last_user_msg,
            system=system_prompt,
            temperature=0.8,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/chat/status", response_model=ChatStatusResponse)
async def chat_status():
    """
    Check Ollama LLM availability.

    Returns connection status, model name, and base URL.
    Useful for frontend health indicators and debugging.
    """
    available = await ollama_client.check_health()

    return ChatStatusResponse(
        ollama_available=available,
        model=ollama_client._model,
        base_url=ollama_client._base_url,
    )
