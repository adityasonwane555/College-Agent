"""
BUDDY AI 2.0 — Unified Multi-Model Provider Interface

Architecture & Multi-Model Orchestration:
  - Unified Interface Abstraction:
      - Normalizes chat requests and tool-calling invocations across diverse AI backends:
        1. Local Ollama: On-device Qwen2.5:3b (offline privacy & sub-second latency).
        2. Cloud Google Gemini: Gemini 3.5 Flash Lite (online grounding & live web extraction).
        3. Cloud Groq: Fast LPU inference running open-weight large models (gpt-oss-120b).
  - Circuit Breaker & Health Tracking:
      - Tracks per-provider availability, ping latency, and failure rates in a real-time health cache.
      - Automatically trips circuit breakers upon network timeouts or API rate-limit errors (429/503),
        preventing cascading stalls and facilitating instant failover to local or secondary models.
  - Standardized UnifiedModelResponse:
      - Encapsulates generated text, parsed tool call payloads, simulation fallback indicators, and round-trip execution latency.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from ..config import settings
from .ollama_service import call_ollama_chat, is_ollama_online, check_ollama_status
from .gemini_service import is_gemini_available, call_gemini_chat, perform_gemini_web_research
from .groq_service import is_groq_available, call_groq_chat


class ProviderHealth(BaseModel):
    """
    Telemetry and operational health record for an AI model provider.
    """
    provider: str
    is_available: bool
    model_name: str
    latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_checked: float = Field(default_factory=time.time)


class UnifiedModelResponse(BaseModel):
    """
    Standardized response envelope returned by all AI inference providers.
    """
    provider: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    is_simulated: bool = False
    latency_seconds: float = 0.0
    citations: List[Any] = Field(default_factory=list)


class UnifiedProviderManager:
    """
    Manages multi-provider availability, circuit-breaker fault tolerance, and health tracking.
    Automatically trips circuit breakers on repeated cloud failures and coordinates failover
    between Google Gemini, Groq Cloud AI, and local GPU-accelerated Ollama.
    """
    def __init__(self):
        """
        Initializes the provider manager with empty health caches and reset circuit breakers.
        """
        self.health_cache: Dict[str, ProviderHealth] = {}
        self.circuit_breakers: Dict[str, float] = {
            "gemini": 0.0,
            "groq": 0.0,
            "ollama": 0.0
        }

    def trip_breaker(self, provider: str, cooldown_seconds: float = 30.0):
        """
        Opens the circuit breaker for a provider, blocking further calls during cooldown.

        Args:
            provider: Identifier of the provider ("gemini", "groq", "ollama").
            cooldown_seconds: Duration in seconds to keep the breaker open (default: 30.0).
        """
        self.circuit_breakers[provider] = time.time() + cooldown_seconds

    def is_breaker_open(self, provider: str) -> bool:
        """
        Checks whether the circuit breaker is currently open (cooling down) for a provider.

        Args:
            provider: Identifier of the provider ("gemini", "groq", "ollama").

        Returns:
            bool: True if circuit breaker is open (disallowing calls), False if closed (normal).
        """
        return time.time() < self.circuit_breakers.get(provider, 0.0)

    async def get_all_health(self) -> Dict[str, ProviderHealth]:
        """
        Audits live connectivity and circuit breaker status across all configured providers.

        Returns:
            Dict[str, ProviderHealth]: Dictionary mapping provider names to their health status records.
        """
        # Ollama check
        ollama_on = await is_ollama_online()
        ollama_health = ProviderHealth(
            provider="ollama",
            is_available=ollama_on,
            model_name=settings.OLLAMA_MODEL
        )

        # Gemini check
        gemini_on = is_gemini_available() and not self.is_breaker_open("gemini")
        gemini_health = ProviderHealth(
            provider="gemini",
            is_available=gemini_on,
            model_name=settings.GEMINI_MODEL
        )

        # Groq check
        groq_on = is_groq_available() and not self.is_breaker_open("groq")
        groq_health = ProviderHealth(
            provider="groq",
            is_available=groq_on,
            model_name=settings.GROQ_MODEL
        )

        self.health_cache = {
            "ollama": ollama_health,
            "gemini": gemini_health,
            "groq": groq_health
        }
        return self.health_cache

    async def call_provider(
        self,
        provider: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None
    ) -> UnifiedModelResponse:
        """
        Routes a conversational inference query to the specified provider with circuit-breaker protection.

        Args:
            provider: Target provider name ("gemini", "groq", "ollama").
            messages: List of chat messages with role and content keys.
            tools: Optional schema definitions of available functions/tools.
            timeout: Optional override for request timeout in seconds.

        Returns:
            UnifiedModelResponse: Standardized response object with text, tool calls, and latency.

        Raises:
            RuntimeError: If provider circuit breaker is open or provider is unavailable.
            ValueError: If unknown provider name is supplied.
        """
        start_t = time.time()

        if provider == "gemini":
            if self.is_breaker_open("gemini") or not is_gemini_available():
                raise RuntimeError("Gemini is currently unavailable or circuit breaker open.")
            try:
                res = await call_gemini_chat(messages, tools=tools)
                return UnifiedModelResponse(
                    provider="gemini",
                    content=res.get("content", ""),
                    tool_calls=res.get("tool_calls"),
                    is_simulated=False,
                    latency_seconds=round(time.time() - start_t, 3)
                )
            except Exception as e:
                self.trip_breaker("gemini", cooldown_seconds=60.0)
                raise e

        elif provider == "groq":
            if self.is_breaker_open("groq") or not is_groq_available():
                raise RuntimeError("Groq is currently unavailable or circuit breaker open.")
            try:
                res = await call_groq_chat(messages, tools=tools)
                return UnifiedModelResponse(
                    provider="groq",
                    content=res.get("content", ""),
                    tool_calls=res.get("tool_calls"),
                    is_simulated=False,
                    latency_seconds=round(time.time() - start_t, 3)
                )
            except Exception as e:
                self.trip_breaker("groq", cooldown_seconds=60.0)
                raise e

        elif provider == "ollama":
            res = await call_ollama_chat(messages, tools=tools)
            return UnifiedModelResponse(
                provider="ollama",
                content=res.get("content", ""),
                tool_calls=res.get("tool_calls"),
                is_simulated=res.get("is_simulated", False),
                latency_seconds=round(time.time() - start_t, 3)
            )

        raise ValueError(f"Unknown provider: {provider}")


provider_manager = UnifiedProviderManager()
