import re
import json
import httpx
from typing import Dict, Any, List, Optional
from ..config import settings


import time

_ollama_cache: Dict[str, Any] = {
    "is_alive": False,
    "last_checked": 0.0,
    "ttl": 5.0
}


async def is_ollama_online() -> bool:
    """Quick cached check to see if Ollama is online without waiting on TCP timeouts."""
    now = time.time()
    if now - _ollama_cache["last_checked"] < _ollama_cache["ttl"]:
        return _ollama_cache["is_alive"]

    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags".replace("localhost", "127.0.0.1")
    try:
        async with httpx.AsyncClient(timeout=0.25) as client:
            resp = await client.get(url)
            _ollama_cache["is_alive"] = (resp.status_code == 200)
    except Exception:
        _ollama_cache["is_alive"] = False

    _ollama_cache["last_checked"] = now
    return _ollama_cache["is_alive"]


async def check_ollama_status() -> Dict[str, Any]:
    """Checks whether the local Ollama server is reachable and if the configured model is downloaded."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags".replace("localhost", "127.0.0.1")
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                _ollama_cache["is_alive"] = True
                _ollama_cache["last_checked"] = time.time()
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                found = any(settings.OLLAMA_MODEL in m for m in models)
                return {
                    "running": True,
                    "models": models,
                    "configured_model": settings.OLLAMA_MODEL,
                    "model_available": found,
                    "message": f"Ollama is running. Configured model '{settings.OLLAMA_MODEL}' {'is installed' if found else 'is NOT downloaded yet.'}"
                }
            _ollama_cache["is_alive"] = False
            return {
                "running": False,
                "models": [],
                "configured_model": settings.OLLAMA_MODEL,
                "model_available": False,
                "message": f"Ollama returned HTTP status {resp.status_code}"
            }
    except Exception as e:
        _ollama_cache["is_alive"] = False
        return {
            "running": False,
            "models": [],
            "configured_model": settings.OLLAMA_MODEL,
            "model_available": False,
            "message": f"Ollama is not running at {settings.OLLAMA_BASE_URL} ({str(e)})"
        }


def mock_ai_response(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Intelligent simulated reception agent used when Ollama is not yet downloaded or running.
    Executes the exact same tool-calling contract as Ollama so all tools, citations,
    and states work out-of-the-box.
    """
    last_msg = messages[-1]
    last_role = last_msg.get("role")
    # If the last message was a tool result, synthesize the final spoken dialogue
    if last_role == "tool":
        tool_content = last_msg.get("content", "").strip()
        # Clean any stray formatting symbols
        clean_facts = tool_content.replace("•", "").replace("*", "").strip()
        dialogue = f"{clean_facts} Please let me know if you would like directions or have any other questions!"
        return {
            "role": "assistant",
            "content": dialogue,
            "is_simulated": True
        }

    # Extract user query
    user_query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_query = m.get("content", "").lower()
            break

    # Look back at context for follow-ups (e.g. "which floor?", "where is it?")
    prev_user_queries = [m.get("content", "") for m in messages if m.get("role") == "user"]
    context_str = " ".join(prev_user_queries).lower()

    # Determine tool to invoke based on query intent
    # 1. Department intent
    dept_matches = {
        "computer science": "Computer Science and Engineering",
        "cse": "CSE",
        "mechanical": "Mechanical Engineering",
        "mech": "MECH",
        "electronics": "Electronics and Communication Engineering",
        "ece": "ECE",
        "civil": "Civil Engineering",
        "mba": "Management Studies (MBA)",
        "management": "Management Studies (MBA)"
    }
    for k, v in dept_matches.items():
        if k in user_query or (("which floor" in user_query or "where" in user_query) and k in context_str):
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "get_department",
                        "arguments": {"name": v}
                    }
                }],
                "is_simulated": True
            }

    # 2. Faculty intent
    if "faculty" in user_query or "professor" in user_query or "hod" in user_query or "doctor" in user_query or "dr." in user_query:
        name_search = "Arvind"
        for candidate in ["arvind", "sharma", "sneha", "patil", "rajeshwari", "nair", "vikram", "deshmukh", "sunita", "kapoor"]:
            if candidate in user_query:
                name_search = candidate
                break
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_faculty",
                    "arguments": {"name": name_search}
                }
            }],
            "is_simulated": True
        }

    # 3. Room / Location intent
    if "room" in user_query or "auditorium" in user_query or "lab" in user_query or "library" in user_query or "office" in user_query:
        room_name = "Auditorium"
        if "lab" in user_query or "robotics" in user_query:
            room_name = "Lab-204"
        elif "102" in user_query or "registrar" in user_query:
            room_name = "102"
        elif "library" in user_query:
            room_name = "LIB-01"
        elif "principal" in user_query or "101" in user_query:
            room_name = "101"
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_room",
                    "arguments": {"room_name": room_name}
                }
            }],
            "is_simulated": True
        }

    # 4. College Hours intent
    if "hour" in user_query or "timing" in user_query or "open" in user_query or "close" in user_query or "when does" in user_query:
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_college_hours",
                    "arguments": {}
                }
            }],
            "is_simulated": True
        }

    # 5. Events intent
    if "event" in user_query or "symposium" in user_query or "hackathon" in user_query or "placement" in user_query:
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_upcoming_events",
                    "arguments": {}
                }
            }],
            "is_simulated": True
        }

    # 6. Announcements intent
    if "announcement" in user_query or "notice" in user_query or "exam" in user_query or "circular" in user_query:
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_announcements",
                    "arguments": {}
                }
            }],
            "is_simulated": True
        }

    # 7. Document search intent (prospectus, eligibility, admission rules, fees, scholarship)
    if any(k in user_query for k in ["eligibility", "prospectus", "scholarship", "anti-ragging", "ragging", "quota", "handbook", "parking", "visitor"]):
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "search_college_documents",
                    "arguments": {"query": user_query}
                }
            }],
            "is_simulated": True
        }

    # 8. General FAQs
    if any(k in user_query for k in ["fee", "admission", "hostel", "bonafide", "medical", "doctor", "card"]):
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "search_faq",
                    "arguments": {"query": user_query}
                }
            }],
            "is_simulated": True
        }

    # Default friendly greeting / reception response
    if any(k in user_query for k in ["hi", "hello", "hey", "who are you", "buddy"]):
        return {
            "role": "assistant",
            "content": "Hello! I'm Buddy, your Smart College Reception AI assistant. How can I assist you today?",
            "is_simulated": True
        }

    # Fallback to document search to look for answers
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "function": {
                "name": "search_college_documents",
                "arguments": {"query": user_query}
            }
        }],
        "is_simulated": True
    }


async def call_ollama_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Sends chat completion request to Ollama.
    Falls back gracefully to simulated agent if Ollama is not running.
    """
    # Fast check: If Ollama is known to be offline, fallback immediately without stalling
    if not await is_ollama_online():
        if settings.MOCK_AI_FALLBACK:
            return mock_ai_response(messages, tools)
        raise RuntimeError(f"Ollama is not running at {settings.OLLAMA_BASE_URL}")

    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat".replace("localhost", "127.0.0.1")
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.15
        }
    }
    if tools:
        payload["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                message = data.get("message", {})
                message["is_simulated"] = False
                return message
            else:
                if settings.MOCK_AI_FALLBACK:
                    return mock_ai_response(messages, tools)
                raise RuntimeError(f"Ollama returned HTTP status {resp.status_code}: {resp.text}")
    except Exception as e:
        _ollama_cache["is_alive"] = False
        if settings.MOCK_AI_FALLBACK:
            return mock_ai_response(messages, tools)
        raise RuntimeError(f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}: {str(e)}")
