"""
BUDDY AI — Local Ollama Service & Simulated Reception Intelligence

Architecture & Inference Pipeline:
  - Local Ollama Engine:
      - Interacts with local Ollama daemon via REST (`http://127.0.0.1:11434/api/chat`).
      - Executes quantized local models (e.g. Qwen 2.5:3b) on local GPU with full OpenAI/Ollama tool calling.
  - Cached Liveness Probing:
      - Implements short-lived TTL cache (5.0s) probing `/api/tags` to avoid connection timeout latency
        in high-throughput voice query loops when the service is offline.
  - Deterministic Mock Reception Fallback:
      - Fully mirrors the tool-calling contract of the live model when Ollama is offline or uninstalled.
      - Uses strict regex whole-word boundary matching (`\\b...\\b`) to eliminate false substring triggers.
      - Emulates tool calls (`get_faculty`, `get_department`, `get_room`, `search_college_documents`)
        against institutional SQLite records so all citations and UI states work seamlessly offline.
"""

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


def _word_in_text(word: str, text: str) -> bool:
    """
    Checks if a whole word exists in target text using strict regex word boundaries.
    Prevents false substring matches (e.g. 'it' inside 'Aditya' or 'visit').

    Args:
        word: Target keyword token.
        text: Input string to search.

    Returns:
        bool: True if exact whole word occurs in text.
    """
    return bool(re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE))


def _any_word_in_text(words: List[str], text: str) -> bool:
    """
    Checks if any of the given keywords match as a complete word in text.

    Args:
        words: List of target keyword strings.
        text: Input string to search.

    Returns:
        bool: True if at least one whole word matches.
    """
    pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


def mock_ai_response(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Intelligent simulated reception agent for APCOER Pune used when Ollama or Gemini
    are momentarily busy or offline. Executes the exact same tool-calling contract as Ollama
    so all tools, citations, and states work with real institutional records.
    Uses strict regex word boundaries to prevent false substring matches (e.g. 'it' in 'Adityo').
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

    # Extract latest user query
    user_query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_query = m.get("content", "").lower().strip()
            break

    # Look back at context for follow-ups (e.g. "which floor?", "where is it?")
    prev_user_queries = [m.get("content", "") for m in messages if m.get("role") == "user"]
    context_str = " ".join(prev_user_queries).lower()

    # 1. Self-Introduction Detection (e.g., "Hi, my name is Aditya", "I am Aditya")
    intro_match = re.search(r'\b(?:my name is|i am|im|this is|call me)\s+([a-zA-Z]+)', user_query, re.IGNORECASE)
    if intro_match:
        candidate_name = intro_match.group(1).capitalize()
        stop_words = {"looking", "interested", "trying", "here", "a", "an", "the", "just", "asking", "visiting", "calling", "student", "parent", "new"}
        if candidate_name.lower() not in stop_words:
            return {
                "role": "assistant",
                "content": (
                    f"Hello {candidate_name}! It's nice to meet you. I am Buddy, a helpful AI assistant with knowledge of APCOER Pune and general topics. "
                    "How can I help you today?"
                ),
                "is_simulated": True
            }

    # 2. "Why is this college best" / Why Choose APCOER / College Highlights
    why_best_tokens = [
        "why is this college best", "why this college", "why apcoer", "why should i join",
        "why choose this college", "why choose apcoer", "why should i choose", "what makes this college",
        "is this college good", "best college", "college advantages", "speciality of college",
        "features of college", "why study here", "benefits of this college"
    ]
    if any(t in user_query for t in why_best_tokens):
        return {
            "role": "assistant",
            "content": (
                "Anantrao Pawar College of Engineering & Research (APCOER), Pune stands out for several compelling reasons! "
                "First, our legacy under Akhil Bharatiya Maratha Shikshan Parishad (ABMSP) spans over 117 years of educational excellence, founded in 1907 with the guiding motto 'Bahujan Hitay, Bahujan Sukhaya'. "
                "Second, our 10-acre green campus at Parvati Hills features state-of-the-art infrastructure, including Advanced CAD/CAM, Robotics labs, and an active Technology Business Incubator (TBI). "
                "Third, our placement cell achieves outstanding outcomes with premier recruiters like TCS, Infosys, Capgemini, L&T, Tech Mahindra, and Cognizant. "
                "Would you like more details on a specific academic department or the admission process under DTE Code 6794?"
            ),
            "is_simulated": True
        }

    # 3. College Identity & Name intent
    college_name_tokens = [
        "who are you", "what is your name", "what are you", "tell me about yourself",
        "what can you do", "which college", "what college", "what is this college", "college name",
        "name of college", "what is the college name", "where am i", "about college",
        "about apcoer", "our college", "name of our college", "our college name"
    ]
    if any(t in user_query for t in college_name_tokens) or ("college" in user_query and _word_in_text("name", user_query)):
        return {
            "role": "assistant",
            "content": (
                "I am Buddy, a helpful AI assistant with knowledge about APCOER Pune and general topics. "
                "Our college is Anantrao Pawar College of Engineering & Research (APCOER), Pune, run by the Akhil Bharatiya Maratha Shikshan Parishad (A.B.M.S. Parishad, founded in 1907 with the guiding motto 'Bahujan Hitay, Bahujan Sukhaya') and affiliated with SPPU (DTE Code: 6794). "
                "How can I help you today?"
            ),
            "is_simulated": True
        }

    # 4. Institutional History & ABMSP Trust intent
    if _any_word_in_text(["history", "founded", "founder", "trust", "abmsp", "parishad", "bahujan", "motto", "heritage"], user_query):
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

    # Concept / Algorithm queries
    if _word_in_text("algorithm", user_query) or _word_in_text("algorithms", user_query):
        return {
            "role": "assistant",
            "content": (
                "An algorithm in computer science is a finite, step-by-step sequence of well-defined, unambiguous instructions "
                "or mathematical rules designed to solve a specific problem, perform a computation, or process input data to produce a desired output."
            ),
            "is_simulated": True
        }

    # 5. Department intent (STRICT whole-word matching to avoid false substring matches like 'it' in 'adityo')
    has_dept_context = _any_word_in_text(["department", "dept", "branch", "engineering", "course", "hod", "lab", "faculty", "syllabus", "admission", "cutoff", "seats", "curriculum"], user_query)
    dept_target = None

    if _word_in_text("cse", user_query) or _word_in_text("comp", user_query) or (_word_in_text("computer", user_query) and (has_dept_context or "engineering" in user_query)):
        dept_target = "Computer Engineering"
    elif _word_in_text("artificial intelligence", user_query) or _word_in_text("aids", user_query) or "ai & ds" in user_query or _word_in_text("data science", user_query):
        dept_target = "Artificial Intelligence and Data Science"
    elif _word_in_text("ai", user_query) and (has_dept_context or "ds" in user_query):
        dept_target = "Artificial Intelligence and Data Science"
    elif _word_in_text("information technology", user_query):
        dept_target = "Information Technology"
    elif _word_in_text("it", user_query) and (has_dept_context or user_query.strip() in {"it", "it department", "about it", "about it dept"}):
        dept_target = "Information Technology"
    elif _word_in_text("mechanical", user_query) or (_word_in_text("mech", user_query) and has_dept_context):
        dept_target = "Mechanical Engineering"
    elif _word_in_text("civil", user_query):
        dept_target = "Civil Engineering"
    elif _any_word_in_text(["electronics", "entc", "etc", "telecommunication"], user_query):
        dept_target = "Electronics and Telecommunication Engineering"
    elif _word_in_text("mca", user_query):
        dept_target = "Master of Computer Applications"
    elif _word_in_text("first year", user_query) or (_word_in_text("fe", user_query) and has_dept_context):
        dept_target = "First Year Engineering (Applied Science)"

    if dept_target:
        if tools:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "get_department",
                        "arguments": {"name": dept_target}
                    }
                }],
                "is_simulated": True
            }
        else:
            return {
                "role": "assistant",
                "content": (
                    f"The {dept_target} department at APCOER offers high-quality undergraduate engineering programs with state-of-the-art laboratory facilities and experienced faculty."
                ),
                "is_simulated": True
            }

    # 6. Faculty / Principal / Leadership intent
    has_faculty_kw = _any_word_in_text(["faculty", "professor", "professors", "hod", "principal", "director", "vice principal", "tpo", "cabin", "consult", "teacher", "teachers", "staff"], user_query)
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

    matched_faculty = None
    for k, v in candidates.items():
        if _word_in_text(k, user_query):
            matched_faculty = v
            break

    if matched_faculty or has_faculty_kw:
        target_name = matched_faculty or "Dr. Sunil B. Thakare"
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "get_faculty",
                    "arguments": {"name": target_name}
                }
            }],
            "is_simulated": True
        }

    # 7. Room / Location intent
    if _any_word_in_text(["room", "auditorium", "lab", "library", "office", "cabin", "where is", "tbi", "seminar", "workshop", "canteen"], user_query):
        room_name = "Auditorium"
        if _word_in_text("principal", user_query) or "101" in user_query:
            room_name = "Principal Office (Room 101)"
        elif _any_word_in_text(["student", "admin", "admission"], user_query) or "102" in user_query:
            room_name = "Student Administrative Section (Room 102)"
        elif _word_in_text("vice", user_query) or "103" in user_query:
            room_name = "Vice Principal Office (Room 103)"
        elif _any_word_in_text(["library", "reading"], user_query):
            room_name = "Central Library & Digital Reading Hall (LIB-01)"
        elif _any_word_in_text(["tpo", "placement"], user_query):
            room_name = "Training & Placement Cell (TPO-01)"
        elif _any_word_in_text(["tbi", "incubator", "startup"], user_query):
            room_name = "Technology Business Incubator (TBI-01)"
        elif _any_word_in_text(["workshop", "cnc"], user_query):
            room_name = "Mechanical Workshop Complex (WS-01)"
        elif _any_word_in_text(["seminar", "auditorium"], user_query):
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

    # 8. College Hours intent
    if _any_word_in_text(["hours", "timing", "timings", "opening", "closing", "schedule"], user_query):
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

    # 9. Events intent
    if _any_word_in_text(["event", "events", "symposium", "sparktech", "technothon", "ashwamedh", "hackathon"], user_query):
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

    # 10. Announcements intent
    if _any_word_in_text(["announcement", "announcements", "notice", "notices", "circular", "circulars", "circular"], user_query):
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

    # 11. Document search intent (prospectus, eligibility, admission rules, fees, scholarship, syllabus)
    if _any_word_in_text(["eligibility", "prospectus", "scholarship", "ragging", "quota", "handbook", "parking", "cutoff", "cutoffs", "syllabus", "curriculum"], user_query):
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

    # 12. General FAQs (fees, admission, hostel, bonafide, id card)
    if _any_word_in_text(["fee", "fees", "admission", "admissions", "hostel", "bonafide", "medical", "doctor", "card"], user_query):
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

    # 13. Default friendly greeting (STRICT word boundary matching so 'hi' doesn't match 'this')
    if _any_word_in_text(["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"], user_query):
        return {
            "role": "assistant",
            "content": "Hello! I am Buddy. How can I help you today?",
            "is_simulated": True
        }

    if tools:
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

    return {
        "role": "assistant",
        "content": (
            "I am Buddy, an intelligent AI assistant with knowledge of APCOER Pune and general topics. "
            "How can I assist you?"
        ),
        "is_simulated": True
    }


async def call_ollama_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Sends chat completion request to the local Ollama daemon.
    Configures sampling parameters (temperature=0.7, top_p=0.9, repeat_penalty=1.15).
    Falls back gracefully to intelligent simulated agent if Ollama is offline or times out.

    Args:
        messages: Conversation turn list conforming to Ollama/OpenAI schema.
        tools: Optional list of function schemas for agent tool calling.

    Returns:
        Dict[str, Any]: Assistant message dictionary with 'content' or 'tool_calls'.

    Raises:
        RuntimeError: If Ollama is offline and mock fallback is explicitly disabled.
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
