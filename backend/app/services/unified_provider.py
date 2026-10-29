"""
BUDDY AI 2.0 — Unified Multi-Model Provider Interface
Standardizes calls across local Ollama, Google Gemini, and Groq.
Maintains latency tracking, circuit-breaker health, and error normalization.
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
    provider: str
    is_available: bool
    model_name: str
    latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_checked: float = Field(default_factory=time.time)


class UnifiedModelResponse(BaseModel):
    provider: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    is_simulated: bool = False
    latency_seconds: float = 0.0
    citations: List[Any] = Field(default_factory=list)


class UnifiedProviderManager:
    """Manages multi-provider availability, failure tracking, and health checks."""
    def __init__(self):
        self.health_cache: Dict[str, ProviderHealth] = {}
        self.circuit_breakers: Dict[str, float] = {
            "gemini": 0.0,
            "groq": 0.0,
            "ollama": 0.0
        }

    def trip_breaker(self, provider: str, cooldown_seconds: float = 30.0):
        self.circuit_breakers[provider] = time.time() + cooldown_seconds

    def is_breaker_open(self, provider: str) -> bool:
        return time.time() < self.circuit_breakers.get(provider, 0.0)

    async def get_all_health(self) -> Dict[str, ProviderHealth]:
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

