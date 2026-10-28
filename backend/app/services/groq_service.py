"""
BUDDY AI — Groq Cloud AI Service
High-speed cloud LLM reasoning and web research powered by Groq LPUs.
Provides ultra-fast inference for external/web questions, deep research,
and fallback when local Ollama models are offline.
"""

import re
import json
import httpx
import logging
from typing import Dict, Any, List, Optional
from ..config import settings

import time

logger = logging.getLogger("buddy.groq")

GROQ_API_BASE = "https://api.groq.com/openai/v1/chat/completions"
_groq_rate_limited_until = 0.0


def is_groq_available() -> bool:
    """Checks if Groq is configured, enabled, and not currently cooling down from a rate limit."""
    global _groq_rate_limited_until
    if time.time() < _groq_rate_limited_until:
        return False
    return bool(settings.GROQ_ENABLED and settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 10)


def reset_groq_quota():
    """Resets the rate limit cooldown."""
    global _groq_rate_limited_until
    _groq_rate_limited_until = 0.0


def _clean_reasoning_tags(text: str) -> str:
    """Strips <think>...</think> reasoning trace blocks from final user output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text)
    return cleaned.strip()


def _prepare_messages_for_groq(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes conversation messages to conform strictly to the OpenAI/Groq API schema.
    Ensures tool responses include tool_call_id and valid roles.
    """
    clean_msgs = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")
        tool_call_id = msg.get("tool_call_id")
        name = msg.get("name")

        item: Dict[str, Any] = {"role": role}

        if role == "tool":
            item["content"] = str(content or "")
            item["tool_call_id"] = tool_call_id or "call_default"
            if name:
                item["name"] = name
        elif role == "assistant":
            item["content"] = content if content is not None else ""
            if tool_calls:
                item["tool_calls"] = tool_calls
        else:
            item["content"] = str(content or "")

        clean_msgs.append(item)
    return clean_msgs


async def call_groq_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> Dict[str, Any]:
    """
    Executes a chat generation with Groq using OpenAI-compatible function calling.
    Returns the assistant message dictionary (with either 'content' or 'tool_calls').
    """
    global _groq_quota_exceeded
    if not is_groq_available():
        raise RuntimeError("Groq API is not configured, disabled, or quota exhausted.")

    clean_messages = _prepare_messages_for_groq(messages)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    model = getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")

    payload: Dict[str, Any] = {
        "model": model,
        "messages": clean_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(GROQ_API_BASE, json=payload, headers=headers)

            if resp.status_code in (429, 404) and "openai/gpt-oss-120b" in model:
                logger.info(f"[Groq] Status {resp.status_code} on primary model. Switching to backup model qwen/qwen3.8-27b...")
                payload["model"] = "qwen/qwen3.8-27b"
                resp = await client.post(GROQ_API_BASE, json=payload, headers=headers)

            if resp.status_code == 429:
                _groq_rate_limited_until = time.time() + 20.0
                logger.warning("[Groq] Rate limit reached (HTTP 429). Cooldown for 20s.")
                raise RuntimeError("Groq API rate limit (cooldown 20s).")

            if resp.status_code != 200:
                err_text = resp.text[:300]
                logger.warning(f"[Groq] API returned HTTP {resp.status_code}: {err_text}")
                raise RuntimeError(f"Groq API returned HTTP {resp.status_code}: {err_text}")

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Groq returned empty choices.")

            msg = choices[0].get("message", {})
            raw_content = msg.get("content") or ""
            clean_content = _clean_reasoning_tags(raw_content)
            tool_calls = msg.get("tool_calls")

            return {
                "role": "assistant",
                "content": clean_content,
                "tool_calls": tool_calls,
                "is_groq": True,
                "is_simulated": False
            }

    except httpx.TimeoutException:
        logger.warning("[Groq] API request timed out after 35s.")
        raise RuntimeError("Groq API timed out.")
    except Exception as e:
        logger.warning(f"[Groq] Unexpected error: {e}")
        raise
