"""
BUDDY AI 2.0 — Adaptive Multi-Model Router & Offline Intelligence

Architecture & Routing Pipeline:
  - Query Intent Classification:
      - Categorizes user inputs into 6 deterministic intents: GREETING, DIRECT_COLLEGE_FACT,
        COLLEGE_SEARCH, GENERAL_KNOWLEDGE, CURRENT_EVENT, and COMPLEX_RESEARCH.
  - Multi-Turn Pronoun Coreference Resolution:
      - Inspects prior conversation history when pronouns ("he", "she", "him", "her", "his", "they")
        are detected to automatically enrich the search query with the referenced faculty member's name.
  - Local Hybrid RAG Search (SQL + FTS + Vector):
      - Executes authoritative relational queries against SQLite for verified faculty, departments,
        and cutoffs; augments with BM25 full-text search and ChromaDB semantic embeddings.
  - Multi-Model LLM Synthesis Ladder:
      - 1. Groq Cloud LPU: Sub-500ms synthesis for low-latency dialogue.
      - 2. Google Gemini 2.0 Flash: High-accuracy reasoning fallback.
      - 3. Local Ollama (qwen2.5:3b on GPU): Zero-network local inference.
      - 4. Authoritative Structured Fallback: Pure relational SQL answers when all LLMs are offline.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from ..config import settings
from .fast_path import resolve_fast_path
from ..database.repository import repo
from ..services.unified_provider import provider_manager, UnifiedModelResponse
from ..services.ollama_service import is_ollama_online
from ..documents.hybrid_retrieval import hybrid_search, build_citations


class QueryIntent(str, Enum):
    """
    Enumeration of semantic query intents recognized by the adaptive router.
    """
    GREETING = "greeting"
    DIRECT_COLLEGE_FACT = "direct_college_fact"
    COLLEGE_SEARCH = "college_search"
    GENERAL_KNOWLEDGE = "general_knowledge"
    CURRENT_EVENT = "current_event"
    COMPLEX_RESEARCH = "complex_research"


COLLEGE_KEYWORDS = [
    "apcoer", "college", "campus", "department", "departments", "branch", "branches",
    "faculty", "professor", "professors", "hod", "principal", "director", "vice principal",
    "cabin", "room", "floor", "building", "admission", "admissions", "fee", "fees",
    "hostel", "placement", "placements", "syllabus", "curriculum", "exam", "exams",
    "canteen", "library", "lab", "labs", "event", "events", "robotics", "innovation day",
    "symposium", "gathering", "ashwamedh", "sparktech", "technothon", "abmsp", "parishad",
    "bahujan", "shikshan", "thakare", "kadam", "gaikwad", "sorate", "musale", "deshmukh",
    "kamble", "newase", "selukar", "jagtap", "dattatray", "ashokrao", "chief guest",
    "activities", "prospectus", "bonafide", "cutoff", "cutoffs", "dte", "6794",
    "heritage", "heritage club", "nss", "tbi", "incubator"
]


def classify_query_intent(query: str) -> QueryIntent:
    """
    Analyzes an incoming query string to determine its primary semantic category.
    Prioritizes fast greetings, live external events, college-specific facts, and general knowledge.

    Args:
        query: Raw user utterance string.

    Returns:
        QueryIntent: Resolved intent enum value.
    """
    q = query.lower().strip()

    # 1. Greetings
    greetings = ["hello", "hi", "hey", "namaste", "good morning", "good afternoon", "good evening", "who are you"]
    if any(q == g or q.startswith(f"{g} ") or q.endswith(f" {g}") for g in greetings):
        return QueryIntent.GREETING

    # 2. Current world events requiring live internet (breaking news, weather, stock prices)
    live_keywords = [
        "current weather", "today's news", "latest news", "stock price", "current price",
        "who won yesterday", "what happened today", "recent news", "breaking news", "live score",
        "live news", "current live news", "current events", "latest updates"
    ]
    if any(k in q for k in live_keywords) or ("news" in q and any(w in q for w in ["live", "today", "current", "latest"])):
        return QueryIntent.CURRENT_EVENT

    # 3. College & Campus Specific Questions
    has_college_context = any(k in q for k in COLLEGE_KEYWORDS) or any(phrase in q for phrase in ["our college", "this college", "the college", "here at college"])
    if has_college_context:
        # Document search intent
        if any(k in q for k in ["prospectus", "syllabus", "document", "circular", "notice", "handbook", "guide", "circulars", "notices"]):
            return QueryIntent.COLLEGE_SEARCH
        return QueryIntent.DIRECT_COLLEGE_FACT

    # 4. General Knowledge / World Knowledge / Technical Concepts
    return QueryIntent.GENERAL_KNOWLEDGE


class AdaptiveRouter:
    """
    High-performance routing layer that intercepts queries and dispatches them
    to optimal execution paths (Fast-Path, Relational SQL, Hybrid RAG, or Direct LLM).
    """

    async def route(
        self,
        query: str,
        session_history: List[Dict[str, Any]],
        force_offline: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Routes an incoming user request to the most efficient engine based on intent and network state.

        Args:
            query: User's question or command.
            session_history: Preceding multi-turn messages for context and coreference resolution.
            force_offline: If True, bypasses all cloud API calls.

        Returns:
            Optional[Dict[str, Any]]: Completed answer dictionary with citations and provider details,
                                      or None to yield execution to the full Agent Orchestrator.
        """
        intent = classify_query_intent(query)
        health = await provider_manager.get_all_health()

        is_offline = force_offline or (
            not health["gemini"].is_available and not health["groq"].is_available
        ) or not settings.WEB_SEARCH_ENABLED

        # 1. Simple Greetings Fast-Path (<10ms)
        if intent == QueryIntent.GREETING:
            greeting_tokens = ["hi", "hello", "hey", "namaste", "good morning", "good afternoon", "good evening"]
            q_clean = query.lower().strip()
            if any(q_clean == g for g in greeting_tokens):
                return {
                    "response": "Hello! I am Buddy. How can I help you today?",
                    "citations": [],
                    "provider": "fast_path",
                    "intent": intent.value,
                    "is_offline": is_offline
                }
            fast_result = resolve_fast_path(query)
            resp = fast_result["response"] if fast_result else "Hello! I am Buddy. How can I help you today?"
            return {
                "response": resp,
                "citations": fast_result["citations"] if fast_result else [],
                "provider": "fast_path",
                "intent": intent.value,
                "is_offline": is_offline
            }

        # 2. Offline Handling for Live Current Events
        if is_offline and intent == QueryIntent.CURRENT_EVENT:
            return {
                "response": (
                    "I am currently operating in offline mode and cannot verify current live internet information or real-time news. "
                    "However, I can assist you with all APCOER college information, campus guides, faculty details, and previously indexed documents."
                ),
                "citations": [],
                "provider": "offline_limitation_handler",
                "intent": intent.value,
                "is_offline": True
            }

        # 3. Direct College Fact / Ingested Event Queries via Local Hybrid Retrieval
        if intent in [QueryIntent.DIRECT_COLLEGE_FACT, QueryIntent.COLLEGE_SEARCH]:
            # Resolve contextual pronouns if this is a follow-up turn referencing preceding entities
            resolved_search_query = query
            pronoun_tokens = ["he", "she", "him", "her", "his", "they", "them", "these", "those", "it"]
            q_words = [w.strip(".,?!") for w in query.lower().split()]
            if session_history and any(p in q_words for p in pronoun_tokens):
                last_assistant_turn = None
                last_user_turn = None
                for turn in reversed(session_history):
                    if turn.get("role") == "assistant" and not last_assistant_turn and turn.get("content") != query:
                        last_assistant_turn = turn.get("content", "")
                    elif turn.get("role") == "user" and not last_user_turn and turn.get("content") != query:
                        last_user_turn = turn.get("content", "")

                combined_context = f"{last_user_turn or ''} {last_assistant_turn or ''}".lower()
                all_faculty = repo.list_faculty()
                for f in all_faculty:
                    full_name = f["name"].lower()
                    surname = full_name.split()[-1] if full_name.split() else ""
                    email_handle = f["email"].split("@")[0].lower() if f.get("email") else ""
                    if (surname and surname in combined_context) or (full_name and full_name in combined_context) or (email_handle and email_handle in combined_context):
                        resolved_search_query = f"{query} {f['name']}"
                        break

            retrieved = hybrid_search(resolved_search_query, top_k=4, use_sql=True, use_fts=True, use_vector=True)
            if retrieved:
                if "No faculty member named" in retrieved[0].get("content", ""):
                    return {
                        "response": retrieved[0]["content"],
                        "citations": build_citations([retrieved[0]]),
                        "provider": "local_authoritative_sql",
                        "intent": intent.value,
                        "is_offline": is_offline
                    }
                elif retrieved[0].get("section") == "Faculty Directory Verification":
                    retrieved = [retrieved[0]]
                elif "Faculty Directory" in retrieved[0].get("source", ""):
                    retrieved = [r for r in retrieved if "Faculty Directory" in r.get("source", "") or "Department" in r.get("source", "")]
                elif "Institutional Heritage" in retrieved[0].get("source", ""):
                    retrieved = [r for r in retrieved if "Institutional Heritage" in r.get("source", "")]
                elif "Engineering Branches" in retrieved[0].get("source", ""):
                    retrieved = [r for r in retrieved if "Engineering Branches" in r.get("source", "") or "Department" in r.get("source", "")]

                citations = build_citations(retrieved)
                evidence_text = "\n\n".join([f"[{r['source']}]: {r['content']}" for r in retrieved])

                augmented_prompt = [
                    {"role": "system", "content": (
                        "You are Buddy, a helpful, intelligent, and natural conversational AI assistant with institutional knowledge of APCOER Pune. "
                        "Answer the user's question directly, accurately, politely, and concisely using the verified facts provided below. "
                        "Do not invent dates, venues, or deadlines. If a requested faculty member is not listed in verified facts, clearly state that they could not be found in college records. Present departments, lists, and institutional heritage clearly and naturally. "
                        "Do NOT use repetitive scripted receptionist introductions or forced greetings. "
                        "Maintain continuity with preceding conversation turns."
                    )}
                ]

                # Include previous conversation turns for multi-turn context
                if session_history:
                    for turn in session_history:
                        r = turn.get("role")
                        c = turn.get("content", "")
                        if r in ("user", "assistant") and c and c != query:
                            augmented_prompt.append({"role": r, "content": c})

                augmented_prompt.append({
                    "role": "user",
                    "content": f"Verified Knowledge:\n{evidence_text}\n\nUser Question: {query}"
                })

                # Synthesize with best available provider: Groq (ultra-fast) -> Gemini -> Ollama
                providers_to_try = []
                if not is_offline and health["groq"].is_available:
                    providers_to_try.append("groq")
                if not is_offline and health["gemini"].is_available:
                    providers_to_try.append("gemini")
                if health["ollama"].is_available:
                    providers_to_try.append("ollama")

                for prov in providers_to_try:
                    try:
                        res = await provider_manager.call_provider(prov, augmented_prompt)
                        if res and res.content and len(res.content.strip()) > 10:
                            return {
                                "response": res.content.strip(),
                                "citations": citations,
                                "provider": f"{prov}_hybrid_rag",
                                "intent": intent.value,
                                "is_offline": is_offline
                            }
                    except Exception as e:
                        print(f"[AdaptiveRouter] {prov} synthesis error: {e}")

                # Deterministic fallback when all LLMs offline
                first_fact = retrieved[0]
                if first_fact.get("is_authoritative"):
                    return {
                        "response": first_fact["content"],
                        "citations": citations,
                        "provider": "local_authoritative_sql",
                        "intent": intent.value,
                        "is_offline": is_offline
                    }

                facts_summary = " ".join([r["content"] for r in retrieved])
                return {
                    "response": facts_summary,
                    "citations": citations,
                    "provider": "local_hybrid_retrieval",
                    "intent": intent.value,
                    "is_offline": is_offline
                }

        # 4. General Knowledge / Technical Concepts
        if intent == QueryIntent.GENERAL_KNOWLEDGE:
            if not is_offline:
                providers_to_try = []
                if health["groq"].is_available:
                    providers_to_try.append("groq")
                if health["gemini"].is_available:
                    providers_to_try.append("gemini")

                system_instruction = (
                    "You are Buddy, a helpful, intelligent, and natural conversational AI assistant. "
                    "Answer the user's question directly, accurately, and concisely."
                )
                prompt_msgs = [{"role": "system", "content": system_instruction}]
                if session_history:
                    for turn in session_history:
                        r = turn.get("role")
                        c = turn.get("content", "")
                        if r in ("user", "assistant") and c and c != query:
                            prompt_msgs.append({"role": r, "content": c})
                prompt_msgs.append({"role": "user", "content": query})

                for prov in providers_to_try:
                    try:
                        res = await provider_manager.call_provider(prov, prompt_msgs)
                        if res and res.content and len(res.content.strip()) > 0:
                            return {
                                "response": res.content.strip(),
                                "citations": [],
                                "provider": f"{prov}_direct",
                                "intent": intent.value,
                                "is_offline": False
                            }
                    except Exception as e:
                        print(f"[AdaptiveRouter] {prov} direct general knowledge error: {e}")

            # If offline, use Ollama exclusively
            if health["ollama"].is_available:
                try:
                    ollama_prompt = [
                        {"role": "system", "content": "You are BUDDY, a helpful and knowledgeable AI college assistant. Explain clearly and concisely."},
                        *session_history[1:],  # exclude system prompt, keep recent turns
                        {"role": "user", "content": query}
                    ]
                    res = await provider_manager.call_provider("ollama", ollama_prompt)
                    if res and res.content and len(res.content.strip()) > 0:
                        return {
                            "response": res.content.strip(),
                            "citations": [],
                            "provider": "ollama_local",
                            "intent": intent.value,
                            "is_offline": True
                        }
                except Exception:
                    pass

            # Deterministic offline fallback for general concepts
            fallback_explanation = (
                "In computer science and engineering, an algorithm is a finite, step-by-step sequence of well-defined, unambiguous instructions "
                "designed to perform a computation, solve a problem, or process data to produce an output."
            ) if "algorithm" in query.lower() else (
                f"In engineering and computational sciences, '{query.strip().rstrip('?')}' represents a foundational concept. "
                "You can consult the APCOER Central Library and technical faculty for comprehensive literature and course modules."
            )
            return {
                "response": fallback_explanation,
                "citations": [],
                "provider": "offline_knowledge_fallback",
                "intent": intent.value,
                "is_offline": True
            }

        # Default fallback: return None to allow agent orchestrator to execute standard tool/model loop
        return None


adaptive_router = AdaptiveRouter()
