"""
Ollama LLM Client — Bravola AI Engine v2.

Upgrades:
  - temperature parameter on generate() and chat() — JSON calls use 0.1
    (deterministic), reasoning uses 0.7, chat uses 0.8.
  - classify_intent(): fast, low-token call to route queries to the
    correct context section, preventing context window saturation.
  - generate_streaming(): async generator for SSE streaming responses.
  - Configurable timeout from settings.

File: backend/shared/ollama_client.py
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from shared.config import settings

logger = logging.getLogger("bravola.ollama")

# Intent labels the classifier can return
VALID_INTENTS = {"benchmark", "strategy", "discovery", "feedback", "general"}


class OllamaClient:
    """
    Ollama LLM client for AI-powered reasoning, chat, and intent routing.

    Falls back gracefully when Ollama is unavailable.
    """

    def __init__(self) -> None:
        self._base_url   = settings.OLLAMA_BASE_URL
        self._model      = settings.OLLAMA_MODEL
        self._available  = False
        timeout_secs     = getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 60)
        self._timeout    = httpx.Timeout(timeout_secs, connect=10.0)

    @property
    def available(self) -> bool:
        return self._available

    async def check_health(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                self._available = resp.status_code == 200
                if self._available:
                    logger.info("Ollama connected: %s (model: %s)", self._base_url, self._model)
                return self._available
        except Exception as exc:
            logger.warning("Ollama not available: %s", exc)
            self._available = False
            return False

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        """
        Generate a completion from Ollama.

        Args:
            temperature: Lower values (0.1) for structured JSON, higher (0.7-0.8)
                         for creative reasoning and chat.
        Returns empty string on failure for graceful fallback.
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                payload: Dict = {
                    "model":  self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                }
                if system:
                    payload["system"] = system

                resp = await client.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "").strip()

        except Exception as exc:
            logger.warning("Ollama generate failed: %s", exc)
            return ""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 600,
    ) -> str:
        """
        Multi-turn chat with Ollama.

        messages: [{"role": "user"|"assistant", "content": "..."}]
        """
        try:
            chat_messages: List[Dict[str, str]] = []
            if system:
                chat_messages.append({"role": "system", "content": system})
            chat_messages.extend(messages)

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model":    self._model,
                        "messages": chat_messages,
                        "stream":   False,
                        "options":  {"temperature": temperature, "num_predict": max_tokens},
                    },
                )
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "").strip()

        except Exception as exc:
            logger.warning("Ollama chat failed: %s", exc)
            return "I'm unable to process your request right now. Ollama service may be unavailable."

    async def generate_streaming(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.8,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming completion generator for Server-Sent Events (SSE).

        Usage in FastAPI:
            from fastapi.responses import StreamingResponse
            return StreamingResponse(ollama_client.generate_streaming(prompt), media_type="text/event-stream")
        """
        payload: Dict = {
            "model":  self._model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/api/generate", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line:
                            import json
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    yield token
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as exc:
            logger.warning("Ollama streaming failed: %s", exc)
            yield "[Streaming unavailable]"

    async def classify_intent(self, query: str) -> str:
        """
        Classify a merchant query into one of the 5 intent categories.

        Returns one of: benchmark | strategy | discovery | feedback | general

        Uses a very short, fast prompt (< 50 tokens output) to minimise
        latency before the main chat response.
        """
        if not self._available:
            return "general"

        system = (
            "You are an intent classifier. Reply with exactly ONE word from this list: "
            "benchmark, strategy, discovery, feedback, general. No other output."
        )
        prompt = (
            f"Classify this merchant question:\n\"{query}\"\n\n"
            "benchmark = questions about health score, KPIs, gaps, performance vs peers\n"
            "strategy = questions about campaigns, flows, recommendations, marketing tactics\n"
            "discovery = questions about persona, vertical, maturity, who my customers are\n"
            "feedback = questions about past campaigns, what worked, results\n"
            "general = anything else"
        )

        result = await self.generate(prompt, system=system, temperature=0.1, max_tokens=5)
        intent = result.strip().lower().split()[0] if result.strip() else "general"

        # Validate — fall back to "general" if the model hallucinated
        return intent if intent in VALID_INTENTS else "general"

    async def enhance_reasoning(
        self,
        engine_name: str,
        heuristic_reasoning: str,
        context: Dict,
        temperature: float = 0.7,
    ) -> str:
        """
        Enhance heuristic reasoning with AI-generated insights.

        Falls back to the original heuristic reasoning if Ollama fails.
        """
        system_prompt = (
            "You are Bravola's AI Growth Marketing Strategist. "
            "Analyze Shopify merchant data and provide actionable marketing insights. "
            "Keep responses concise (2-3 sentences). Be specific and data-driven. "
            "Do NOT use markdown formatting."
        )
        prompt = (
            f"Engine: {engine_name}\n"
            f"Initial Analysis: {heuristic_reasoning}\n"
            f"Context: {context}\n\n"
            "Enhance this analysis with a brief, actionable insight. "
            "Keep the same tone and be concise."
        )
        enhanced = await self.generate(prompt, system=system_prompt, temperature=temperature)
        return enhanced or heuristic_reasoning


# Singleton
ollama_client = OllamaClient()
