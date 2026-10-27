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
        async with httpx.AsyncClient(timeout=2.0) as client:
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
        async with httpx.AsyncClient(timeout=2.0) as client:
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
    Intelligent simulated reception agent for APCOER Pune used when Ollama or Gemini
    are momentarily busy or offline. Executes the exact same tool-calling contract as Ollama
    so all tools, citations, and states work with real institutional records.
    """
    last_msg = messages[-1]
    last_role = last_msg.get("role")
    # If the last message was a tool result, synthesize the final spoken dialogue
    if last_role == "tool":
        tool_content = last_msg.get("content", "").strip()
        # Clean any stray formatting symbols
        clean_facts = tool_content.replace("•", "").replace("*", "").strip()
        dialogue = f"{clean_facts} Please let me know if you would like directions or have any further questions!"
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

    # 1. College Identity & Name intent
    if any(k in user_query for k in ["college name", "name of college", "our college", "which college", "what college", "what is this college", "apcoer", "who are you", "what is your name"]) or ("college" in user_query and "name" in user_query):
        return {
            "role": "assistant",
            "content": (
                "Hello and welcome! Our college is Anantrao Pawar College of Engineering & Research (APCOER), Pune. "
                "Our parent trust is Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad, founded in 1907 with the guiding motto 'Bahujan Hitay, Bahujan Sukhaya') and we are affiliated with Savitribai Phule Pune University (DTE Code: 6794). "
                "I am Buddy, your AI Receptionist. How may I assist you today?"
            ),
            "is_simulated": True
        }

    # 1b. Institutional History & ABMSP Trust intent
    if any(k in user_query for k in ["history", "founded", "founder", "trust", "abmsp", "parishad", "bahujan", "motto"]):
        return {
            "role": "assistant",
            "content": (
                "Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad), our parent educational trust, was founded in 1907 by a team of renowned educationists and social reformers with the noble thought 'Bahujan Hitay, Bahujan Sukhaya'—for the welfare and happiness of the masses. "
                "In the first half of the 20th century, A.B.M.S. Parishad made a commendable contribution of awakening and inspiring the masses who were deprived of education for generations, establishing educational institutions throughout Maharashtra and beyond. "
                "The Parishad draws its enduring inspiration from Mahatma Jyotirao Phule, Rajarshi Chhatrapati Shahu Maharaj (the Ruler of Kolhapur), and Dr. Babasaheb Ambedkar, who fought for economic, social, and political justice and advocated the empowerment of disadvantaged sections of society. "
                "Anantrao Pawar College of Engineering & Research (APCOER) was established in 2012 on a 10-acre campus near Parvati Hills to carry forward this mission."
            ),
            "is_simulated": True
        }

    # 2. Department intent
    dept_matches = {
        "computer": "Computer Engineering",
        "comp": "Computer Engineering",
        "cse": "Computer Engineering",
        "artificial intelligence": "Artificial Intelligence and Data Science",
        "ai": "Artificial Intelligence and Data Science",
        "data science": "Artificial Intelligence and Data Science",
        "information technology": "Information Technology",
        "it": "Information Technology",
        "mechanical": "Mechanical Engineering",
        "mech": "Mechanical Engineering",
        "civil": "Civil Engineering",
        "electronics": "Electronics and Telecommunication Engineering",
        "entc": "Electronics and Telecommunication Engineering",
        "telecommunication": "Electronics and Telecommunication Engineering",
        "mca": "Master of Computer Applications",
        "first year": "First Year Engineering (Applied Science)",
        "fe": "First Year Engineering (Applied Science)"
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

    # 3. Faculty / Principal / Leadership intent
    if any(k in user_query for k in ["faculty", "professor", "hod", "principal", "director", "vice principal", "tpo", "cabin", "consult"]):
        name_search = "Dr. Sunil B. Thakare"
        candidates = {
            "principal": "Dr. Sunil B. Thakare",
            "thakare": "Dr. Sunil B. Thakare",
            "sunil": "Dr. Sunil B. Thakare",
            "vice principal": "Prof. Shrikant B. Jagtap",
            "jagtap": "Prof. Shrikant B. Jagtap",
            "shrikant": "Prof. Shrikant B. Jagtap",
            "gaikwad": "Dr. Rama B. Gaikwad",
            "rama": "Dr. Rama B. Gaikwad",
            "kadam": "Dr. Amit Ashokrao Kadam",
            "amit": "Dr. Amit Ashokrao Kadam",
            "rankhambe": "Prof. D. P. Rankhambe",
            "devika": "Prof. D. P. Rankhambe",
            "lavhe": "Prof. R. S. Lavhe",
            "ramesh": "Prof. R. S. Lavhe",
            "kokane": "Prof. S. R. Kokane",
            "sayali": "Prof. S. R. Kokane",
            "kalal": "Prof. A. N. Kalal",
            "ashok": "Prof. A. N. Kalal",
            "nikam": "Prof. Rajshri Nikam",
            "rajshri": "Prof. Rajshri Nikam",
            "dodke": "Prof. A. R. Dodke",
            "akash": "Prof. A. R. Dodke",
            "dipalee": "Prof. Dipalee Shah",
            "shah": "Prof. Dipalee Shah",
            "khaire": "Prof. Prajakta G. Khaire",
            "prajakta": "Prof. Prajakta G. Khaire",
            "khote": "Prof. Shital S. Khote",
            "shital": "Prof. Shital S. Khote",
            "patil": "Mr. Ajinkya Patil",
            "ajinkya": "Mr. Ajinkya Patil",
            "musale": "Dr. Jitendra Musale",
            "jitendra": "Dr. Jitendra Musale",
            "deshmukh": "Dr. Amar Deshmukh",
            "amar": "Dr. Amar Deshmukh",
            "sorate": "Dr. Raviraj Ramesh Sorate",
            "raviraj": "Dr. Raviraj Ramesh Sorate",
            "kamble": "Dr. Dattatray P. Kamble",
            "dattatray": "Dr. Dattatray P. Kamble",
            "newase": "Dr. Atul D. Newase",
            "atul": "Dr. Atul D. Newase",
            "selukar": "Dr. Balaji S. Selukar",
            "balaji": "Dr. Balaji S. Selukar",
            "totla": "Prof. Nilesh S. Totla",
            "nilesh": "Prof. Nilesh S. Totla",
            "tpo": "Prof. Nilesh S. Totla",
            "placement": "Prof. Nilesh S. Totla"
        }
        for k, v in candidates.items():
            if k in user_query:
                name_search = v
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

    # 4. Room / Location intent
    if any(k in user_query for k in ["room", "auditorium", "lab", "library", "office", "cabin", "where is", "tbi", "seminar"]):
        room_name = "Auditorium"
        if "principal" in user_query or "101" in user_query:
            room_name = "Principal Office (Room 101)"
        elif "student" in user_query or "admin" in user_query or "admission" in user_query or "102" in user_query:
            room_name = "Student Administrative Section (Room 102)"
        elif "vice" in user_query or "103" in user_query:
            room_name = "Vice Principal Office (Room 103)"
        elif "library" in user_query or "reading" in user_query:
            room_name = "Central Library & Digital Reading Hall (LIB-01)"
        elif "tpo" in user_query or "placement" in user_query:
            room_name = "Training & Placement Cell (TPO-01)"
        elif "tbi" in user_query or "incubator" in user_query or "startup" in user_query:
            room_name = "Technology Business Incubator (TBI-01)"
        elif "workshop" in user_query or "cnc" in user_query:
            room_name = "Mechanical Workshop Complex (WS-01)"
        elif "seminar" in user_query or "auditorium" in user_query:
            room_name = "Central Auditorium (AUD-01)"
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

    # 5. College Hours intent
    if any(k in user_query for k in ["hour", "timing", "timings", "open", "close", "when does", "schedule"]):
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

    # 6. Events intent
    if any(k in user_query for k in ["event", "symposium", "sparktech", "technothon", "ashwamedh", "hackathon"]):
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

    # 7. Announcements intent
    if any(k in user_query for k in ["announcement", "notice", "circular", "dte", "sppu", "exam"]):
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

    # 8. Document search intent (prospectus, eligibility, admission rules, fees, scholarship, syllabus)
    if any(k in user_query for k in ["eligibility", "prospectus", "scholarship", "anti-ragging", "ragging", "quota", "handbook", "parking", "visitor", "cap", "dte code", "syllabus", "curriculum", "cutoff"]):
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

    # 9. General FAQs (fees, admission, hostel, bonafide, id card)
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
    if any(k in user_query for k in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]):
        return {
            "role": "assistant",
            "content": "Hello and welcome! I am Buddy, the AI Receptionist at Anantrao Pawar College of Engineering & Research (APCOER), Pune. How may I assist you today?",
            "is_simulated": True
        }

    # Fallback to document search to look for answers in official APCOER documents
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
