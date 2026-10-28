"""
BUDDY AI — Google Gemini Cloud AI Service
High-accuracy cloud LLM reasoning, live web research, and online information extraction
powered by Google Gemini (gemini-3.5-flash-lite / gemini-3.5-flash).
Provides real-time internet data synthesis, web grounding, and multi-turn conversational dialogue.
"""

import re
import json
import time
import httpx
import logging
from typing import Dict, Any, List, Optional
from ..config import settings

logger = logging.getLogger("buddy.gemini")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_gemini_rate_limited_until = 0.0


def is_gemini_available() -> bool:
    """Checks if Gemini is configured, enabled, and not currently cooling down from a rate limit."""
    global _gemini_rate_limited_until
    if time.time() < _gemini_rate_limited_until:
        return False
    return bool(settings.GEMINI_ENABLED and settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 10)


def reset_gemini_quota():
    """Resets the rate limit cooldown."""
    global _gemini_rate_limited_until
    _gemini_rate_limited_until = 0.0


def _clean_reasoning_tags(text: str) -> str:
    """Strips thinking and reasoning tags from final model output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text)
    return cleaned.strip()


def _prepare_messages_for_gemini(messages: List[Dict[str, Any]]) -> tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Transforms OpenAI/Ollama messages into Google Gemini's schema.
    Separates system instructions from alternating user/model conversation turns.
    """
    system_parts = []
    raw_contents: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls")
        name = msg.get("name")

        if role == "system":
            if content:
                system_parts.append(str(content))
        elif role == "user":
            raw_contents.append({
                "role": "user",
                "parts": [{"text": str(content)}]
            })
        elif role == "assistant":
            parts = []
            if content:
                parts.append({"text": str(content)})
            if tool_calls and not content:
                # Describe requested tool calls in text
                tc_names = [tc.get("function", {}).get("name", "tool") for tc in tool_calls]
                parts.append({"text": f"Calling tools: {', '.join(tc_names)}"})
            if parts:
                raw_contents.append({
                    "role": "model",
                    "parts": parts
                })
        elif role == "tool":
            # Pass tool results back to Gemini in user role
            tool_text = f"[Tool Output for {name or 'tool'}]:\n{content}"
            raw_contents.append({
                "role": "user",
                "parts": [{"text": tool_text}]
            })

    # Gemini requires alternating user and model turns. Merge consecutive turns of same role.
    merged_contents: List[Dict[str, Any]] = []
    for item in raw_contents:
        if not merged_contents:
            merged_contents.append(item)
            continue

        prev = merged_contents[-1]
        if prev["role"] == item["role"]:
            # Combine parts into previous message
            prev["parts"].extend(item["parts"])
        else:
            merged_contents.append(item)

    # Gemini contents must start with a user turn
    if merged_contents and merged_contents[0]["role"] != "user":
        merged_contents.insert(0, {
            "role": "user",
            "parts": [{"text": "Hello Buddy!"}]
        })

    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, merged_contents


async def call_gemini_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> Dict[str, Any]:
    """
    Executes a chat generation with Google Gemini REST API.
    Returns the assistant message dictionary compatible with the orchestrator.
    """
    global _gemini_rate_limited_until
    if not is_gemini_available():
        raise RuntimeError("Google Gemini API is not configured, disabled, or cooling down.")

    system_instruction, contents = _prepare_messages_for_gemini(messages)
    api_key = settings.GEMINI_API_KEY.strip()
    model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite"

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    # Format tools for Gemini if provided
    if tools:
        gemini_funcs = []
        for t in tools:
            if isinstance(t, dict):
                fn = t.get("function") if "function" in t else t
                if isinstance(fn, dict) and "name" in fn:
                    gemini_funcs.append(fn)
        if gemini_funcs:
            payload["tools"] = [{"function_declarations": gemini_funcs}]

    candidate_models = [model, "gemini-3.1-flash-lite", "gemini-3.5-flash"]
    last_error = ""

    for target_model in candidate_models:
        url = f"{GEMINI_API_BASE}/{target_model}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)

                if resp.status_code == 429:
                    _gemini_rate_limited_until = time.time() + 20.0
                    logger.warning(f"[Gemini] Rate limit hit (HTTP 429) on {target_model}. Cooling down for 20s.")
                    raise RuntimeError("Gemini API rate limit reached (cooldown 20s).")

                if resp.status_code == 404:
                    logger.info(f"[Gemini] Model {target_model} returned 404, trying next candidate...")
                    continue

                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:250]}"
                    logger.warning(f"[Gemini] {target_model} error: {last_error}")
                    continue

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini returned empty candidates.")

                candidate = candidates[0]
                content_obj = candidate.get("content", {})
                parts = content_obj.get("parts", [])

                text_parts = []
                tool_calls = []

                for p in parts:
                    if "text" in p:
                        text_parts.append(p["text"])
                    elif "functionCall" in p:
                        fc = p["functionCall"]
                        fn_name = fc.get("name", "")
                        fn_args = fc.get("args", {})
                        tool_calls.append({
                            "id": fc.get("id") or f"call_{int(time.time()*1000)}",
                            "type": "function",
                            "function": {
                                "name": fn_name,
                                "arguments": json.dumps(fn_args) if isinstance(fn_args, dict) else str(fn_args)
                            }
                        })

                clean_text = _clean_reasoning_tags("\n".join(text_parts))

                return {
                    "role": "assistant",
                    "content": clean_text,
                    "tool_calls": tool_calls if tool_calls else None,
                    "is_gemini": True,
                    "is_simulated": False
                }

        except httpx.TimeoutException:
            logger.warning(f"[Gemini] Timeout contacting model {target_model}.")
            last_error = "Gemini request timed out after 30s."
            continue
        except RuntimeError:
            raise
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[Gemini] Unexpected exception on {target_model}: {e}")
            continue

    raise RuntimeError(f"All Gemini candidate models failed. Last error: {last_error}")


async def perform_gemini_web_research(query: str, system_prompt: str = "") -> Dict[str, Any]:
    """
    High-accuracy real-time web research & online data extraction.
    1. Fetches live, fresh search results from the web via web_tools.
    2. Sends the live data to Google Gemini to synthesize a natural, spoken APCOER receptionist response.
    3. Returns the synthesized text along with grounded source citations and URLs.
    """
    from ..tools.web_tools import search_internet

    # Step 1: Live Web Search Retrieval
    search_data = await search_internet(query, num_results=4)
    snippets = search_data.get("content", "")
    citations = search_data.get("citations", [])
    sources = search_data.get("sources", [])

    if not snippets or search_data.get("status") == "not_found":
        snippets = "No real-time web results found for this specific query."

    # Step 2: Build Grounded Synthesis Prompt for Gemini
    synthesis_prompt = f"""User Inquiry: "{query}"

=== LIVE WEB RESEARCH & REAL-TIME INTERNET DATA ===
{snippets}
===================================================

INSTRUCTIONS:
1. You are BUDDY, the warm and intelligent AI Receptionist at Anantrao Pawar College of Engineering & Research (APCOER), Pune.
2. Synthesize the above live web search data to directly and accurately answer the user's question.
3. Speak in natural, friendly conversational dialogue (2 to 4 sentences).
4. Do NOT use bullet points, markdown bold headers, or database keys.
5. Pronounce college acronyms letter-by-letter as initialisms (e.g., A, P, C, O, E, R).
6. End with a helpful, friendly closing question.
"""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": synthesis_prompt})

    res = await call_gemini_chat(messages=messages, temperature=0.3, max_tokens=600)
    final_text = res.get("content", "").strip()

    return {
        "response": final_text,
        "citations": citations,
        "sources": sources,
        "is_gemini": True,
        "is_web_research": True
    }
