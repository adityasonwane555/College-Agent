import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from ..config import settings

logger = logging.getLogger("buddy.gemini")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


_gemini_quota_exceeded = False


def is_gemini_available() -> bool:
    """Checks if Gemini is configured, enabled, and not quota-exhausted."""
    global _gemini_quota_exceeded
    if _gemini_quota_exceeded:
        return False
    return bool(settings.GEMINI_ENABLED and settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10)


def _convert_tools_to_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts OpenAI/Ollama tool definitions to Google Gemini function declarations."""
    declarations = []
    for t in tools:
        fn = t.get("function", {})
        params = fn.get("parameters", {})
        # Ensure properties and type format conforms to Gemini schema
        declarations.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "parameters": params
        })
    return [{"function_declarations": declarations}] if declarations else []


def _convert_messages_to_gemini(messages: List[Dict[str, Any]]) -> tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Extracts system prompt and maps conversation turns to Gemini contents format.
    Roles in Gemini are strictly 'user' and 'model'.
    """
    system_instruction: Optional[str] = None
    contents: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = content
            continue

        if role == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": str(content)}]
            })
        elif role == "assistant":
            parts: List[Dict[str, Any]] = []
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    fc_dict: Dict[str, Any] = {
                        "functionCall": {
                            "name": fn.get("name", ""),
                            "args": args
                        }
                    }
                    if "thoughtSignature" in tc:
                        fc_dict["thoughtSignature"] = tc["thoughtSignature"]
                    parts.append(fc_dict)
            if content:
                parts.append({"text": str(content)})

            if parts:
                contents.append({
                    "role": "model",
                    "parts": parts
                })
        elif role == "tool":
            # Function execution response returned to model
            try:
                result_payload = json.loads(content) if isinstance(content, str) else content
            except Exception:
                result_payload = {"output": str(content)}

            # Gemini requires functionResponse with the tool name
            tool_name = msg.get("name", "tool_result")
            contents.append({
                "role": "user",
                "parts": [{
                    "functionResponse": {
                        "name": tool_name,
                        "response": result_payload
                    }
                }]
            })

    return system_instruction, contents


async def call_gemini_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Executes a chat generation with Google Gemini using tool declarations.
    Returns a unified assistant message dict compatible with the orchestrator.
    """
    if not is_gemini_available():
        raise RuntimeError("Gemini API key is not configured, disabled, or quota exhausted.")

    system_instruction, contents = _convert_messages_to_gemini(messages)
    gemini_tools = _convert_tools_to_gemini(tools) if tools else []

    url = f"{GEMINI_API_BASE}/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    payload: Dict[str, Any] = {"contents": contents}

    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

    if gemini_tools:
        payload["tools"] = gemini_tools

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            if resp.status_code == 429:
                global _gemini_quota_exceeded
                _gemini_quota_exceeded = True
                logger.warning("Gemini API quota exceeded (429). Disabling Gemini for current runtime session.")
            raise RuntimeError(f"Gemini API returned {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")

        candidate_content = candidates[0].get("content", {})
        parts = candidate_content.get("parts", [])

        # Parse text responses and function calls
        text_chunks: List[str] = []
        parsed_tool_calls: List[Dict[str, Any]] = []

        for p in parts:
            if "text" in p:
                text_chunks.append(p["text"])
            elif "functionCall" in p:
                fc = p["functionCall"]
                call_id = fc.get("id") or f"call_{fc.get('name')}"
                tc_item: Dict[str, Any] = {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": fc.get("name", ""),
                        "arguments": fc.get("args", {})
                    }
                }
                if "thoughtSignature" in p:
                    tc_item["thoughtSignature"] = p["thoughtSignature"]
                elif "thought_signature" in p:
                    tc_item["thoughtSignature"] = p["thought_signature"]
                parsed_tool_calls.append(tc_item)

        final_text = " ".join(text_chunks).strip()

        result: Dict[str, Any] = {
            "role": "assistant",
            "content": final_text,
            "is_gemini": True,
            "is_simulated": False
        }

        if parsed_tool_calls:
            result["tool_calls"] = parsed_tool_calls

        return result
