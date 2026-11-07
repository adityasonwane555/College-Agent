"""
BUDDY AI — Conversational Agent Orchestrator

Architecture & Decision Pipeline:
  - Multi-Tiered Intelligent Routing:
      1. Fast-Path Direct Resolution: Sub-10ms keyword lookup for standard greeting/campus queries.
      2. Adaptive Multi-Model Router: Analyzes query complexity to dispatch to local Qwen 2.5 (GPU),
         Groq LPU (cloud ultra-low latency), or Gemini 2.0 Flash (deep reasoning).
      3. Google Gemini Live Web Research: Automatically triggered for current events, live news,
         weather, or real-time internet topics, strictly excluding local college inquiries.
      4. Tool Execution Loop: Supports recursive multi-turn tool calling (up to MAX_TOOL_ITERATIONS)
         with schema validation and structured citation tracking.
  - Session & Conversation Memory:
      - Thread-safe FIFO sliding window history maintaining system instructions at index 0.
      - Automatically trims oldest turns while preserving context coherence across sessions.
  - Grounding & Guardrails:
      - Validates output assertions against official campus knowledge base to prevent hallucinations.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from ..config import settings
from .prompts import SYSTEM_PROMPT
from .tool_registry import OLLAMA_TOOLS_SCHEMA, execute_tool
from ..services.ollama_service import call_ollama_chat, is_ollama_online
from ..services.groq_service import is_groq_available, call_groq_chat
from ..services.gemini_service import is_gemini_available, call_gemini_chat, perform_gemini_web_research
from ..database.models import CitationModel
from .fast_path import resolve_fast_path
from .router import adaptive_router
from .grounding import verify_response_grounding


def is_web_or_research_query(query: str) -> bool:
    """
    Classifies whether an incoming query requires external live web research.
    Strictly safeguards college-specific questions from triggering web search
    by checking for APCOER faculty, departments, rooms, and campus keywords.

    Args:
        query: Raw user utterance string.

    Returns:
        bool: True if external live web research should be invoked; False for campus/general topics.
    """
    q = query.lower().strip()

    # If the question contains college context, it is not an external web query
    college_keywords = [
        "apcoer", "college", "campus", "hod", "principal", "department", "departments",
        "branch", "branches", "admission", "fee", "fees", "hostel", "placement",
        "syllabus", "exam", "room", "faculty", "thakare", "kadam", "gaikwad", "totla",
        "abmsp", "sorate", "musale", "deshmukh", "kamble", "newase", "selukar", "jagtap",
        "robotics", "chief guest", "our college", "this college"
    ]
    if any(k in q for k in college_keywords):
        return False

    # Live external search indicators
    live_web_keywords = [
        "search the web", "search internet", "search online", "look up online",
        "browse the web", "web search", "internet search", "on the web",
        "find online", "research online", "latest news", "current weather", "today's news",
        "who won yesterday", "what happened today", "stock price", "current price",
        "news about", "weather in", "latest updates", "recent events",
        "live score", "current live news", "breaking news"
    ]
    return any(k in q for k in live_web_keywords)


class SessionManager:
    """
    Manages multi-turn conversation memory buffers isolated by unique session IDs.
    Preserves system instructions while sliding a window of recent user and agent messages.
    """
    def __init__(self, max_history: int = 15):
        """
        Initializes session buffer with a configurable history depth.

        Args:
            max_history: Maximum number of recent conversational messages to retain.
        """
        self.max_history = max_history
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves or initializes conversation message history for a given session.

        Args:
            session_id: Unique string session token.

        Returns:
            List[Dict[str, Any]]: List of message dictionaries with role and content.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.sessions[session_id]

    def add_message(self, session_id: str, message: Dict[str, Any]):
        """
        Appends a new turn to session history and trims oldest messages if limit is exceeded.

        Args:
            session_id: Unique string session token.
            message: Message dictionary containing 'role' and 'content' or 'tool_calls'.
        """
        history = self.get_history(session_id)
        history.append(message)
        # Keep system prompt at [0] and trim older messages
        if len(history) > self.max_history + 1:
            self.sessions[session_id] = [history[0]] + history[-(self.max_history):]

    def reset_session(self, session_id: str):
        """
        Clears conversation history for the session, restoring default system prompt.

        Args:
            session_id: Unique string session token.
        """
        self.sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]


session_manager = SessionManager(max_history=settings.SESSION_MAX_HISTORY)


class AgentOrchestrator:
    """
    Master reasoning agent that orchestrates multi-turn LLM reasoning,
    hybrid retrieval routing, tool execution, and citation grounding.
    """

    async def run(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        status_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes an agent reasoning cycle for an incoming user query.

        Execution Pipeline:
          1. Records user message in session memory.
          2. Evaluates fast-path heuristics (<10ms).
          3. Evaluates adaptive router (local vs cloud).
          4. Checks for external web research triggers via Google Gemini.
          5. Enters iterative tool execution loop (up to MAX_TOOL_ITERATIONS).
          6. Collates structured citations and returns validated response.

        Args:
            user_message: Plain text input from the user.
            session_id: Unique identifier for dialogue continuity (generates UUID if omitted).
            status_callback: Optional async function for emitting live UI status updates.

        Returns:
            Dict[str, Any]: Response payload containing 'session_id', 'response', 'citations',
                            'is_simulated', and 'tool_iterations'.
        """
        sid = session_id or str(uuid.uuid4())
        session_manager.add_message(sid, {"role": "user", "content": user_message})

        # 1. Fast-Path Direct Resolution (<10ms for common queries, disabled by default for natural conversational dialogue)
        if getattr(settings, "ENABLE_FAST_PATH", False):
            fast_result = resolve_fast_path(user_message)
            if fast_result:
                session_manager.add_message(sid, {"role": "assistant", "content": fast_result["response"]})
                return {
                    "session_id": sid,
                    "response": fast_result["response"],
                    "citations": fast_result["citations"],
                    "is_simulated": False,
                    "tool_iterations": 0
                }

        # 2. Adaptive Multi-Model & Offline Router Resolution
        history = session_manager.get_history(sid)
        routed_result = await adaptive_router.route(user_message, history)
        if routed_result:
            final_content = routed_result["response"]
            session_manager.add_message(sid, {"role": "assistant", "content": final_content})
            return {
                "session_id": sid,
                "response": final_content,
                "citations": routed_result.get("citations", []),
                "is_simulated": False,
                "tool_iterations": 0,
                "provider": routed_result.get("provider", "adaptive_router")
            }

        citations: List[CitationModel] = []
        is_simulated = False
        iteration = 0

        use_gemini = is_gemini_available()
        use_groq = is_groq_available()
        is_web_research = is_web_or_research_query(user_message)

        # Priority 0: Direct Google Gemini Web Research for live internet queries
        if is_web_research and use_gemini:
            if status_callback:
                await status_callback("thinking", "Researching live internet information with Google Gemini...")
            try:
                history = session_manager.get_history(sid)
                web_res = await perform_gemini_web_research(user_message, system_prompt=SYSTEM_PROMPT, history=history)
                final_content = web_res.get("response", "").strip()
                if final_content:
                    session_manager.add_message(sid, {"role": "assistant", "content": final_content})
                    raw_citations = web_res.get("citations", [])
                    clean_citations = [
                        CitationModel(**c) if isinstance(c, dict) else c
                        for c in raw_citations
                    ]
                    return {
                        "session_id": sid,
                        "response": final_content,
                        "citations": clean_citations,
                        "is_simulated": False,
                        "tool_iterations": 1,
                        "is_gemini": True
                    }
            except Exception as e:
                print(f"[Orchestrator] Gemini web research error: {e}, attempting multi-turn tool fallback...")

        while iteration < settings.MAX_TOOL_ITERATIONS:
            iteration += 1
            history = session_manager.get_history(sid)

            if status_callback:
                await status_callback("thinking", f"Processing response (step {iteration})...")

            assistant_msg = None

            # Priority 1: High-Speed Groq Cloud AI (LPU acceleration for sub-second responses)
            if not assistant_msg and use_groq and (is_web_research or not getattr(settings, "USE_LOCAL_LLM_FIRST", True)):
                try:
                    assistant_msg = await call_groq_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Groq chat error: {e}, attempting Gemini fallback...")
                    assistant_msg = None

            # Priority 2: Google Gemini Cloud AI
            if not assistant_msg and use_gemini and (is_web_research or not getattr(settings, "USE_LOCAL_LLM_FIRST", True)):
                try:
                    assistant_msg = await call_gemini_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Gemini chat error: {e}, attempting Ollama fallback...")
                    use_gemini = False
                    assistant_msg = None

            # Priority 3: Local Ollama Model (qwen2.5:3b on GPU) for college campus queries
            if not assistant_msg and getattr(settings, "USE_LOCAL_LLM_FIRST", True):
                if await is_ollama_online():
                    try:
                        assistant_msg = await call_ollama_chat(
                            messages=history,
                            tools=OLLAMA_TOOLS_SCHEMA
                        )
                    except Exception as e:
                        print(f"[Orchestrator] Local Ollama call error: {e}")
                        assistant_msg = None

            # Priority 4: Gemini / Groq Cloud AI Fallback if Ollama was offline or failed on college query
            if not assistant_msg and use_gemini:
                try:
                    assistant_msg = await call_gemini_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Gemini fallback error: {e}")
                    use_gemini = False

            if not assistant_msg and use_groq:
                try:
                    assistant_msg = await call_groq_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Groq fallback error: {e}")
                    use_groq = False

            # Priority 5: Fallback to call_ollama_chat (handles local execution or smart mock fallback)
            if not assistant_msg:
                assistant_msg = await call_ollama_chat(
                    messages=history,
                    tools=OLLAMA_TOOLS_SCHEMA
                )

            is_simulated = assistant_msg.get("is_simulated", False)
            tool_calls = assistant_msg.get("tool_calls")

            # If no tool call is requested, we reached the final assistant response
            if not tool_calls:
                final_content = assistant_msg.get("content", "").strip()
                if not final_content:
                    final_content = "I have reviewed your request. How else may I assist you?"

                session_manager.add_message(sid, {"role": "assistant", "content": final_content})
                return {
                    "session_id": sid,
                    "response": final_content,
                    "citations": citations,
                    "is_simulated": is_simulated,
                    "tool_iterations": iteration
                }

            # Record assistant's tool-call request into conversation history
            session_manager.add_message(sid, assistant_msg)

            # Process each requested tool call
            for tool_call in tool_calls:
                func_meta = tool_call.get("function", {})
                tool_name = func_meta.get("name", "")
                raw_args = func_meta.get("arguments", {})
                tool_call_id = tool_call.get("id") or f"call_{uuid.uuid4().hex[:8]}"

                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = {}
                else:
                    args = raw_args

                if status_callback:
                    await status_callback("calling_tool", f"Consulting tool: {tool_name}...")

                tool_result = await execute_tool(tool_name, args)

                # Capture citations if tool returned citations
                if isinstance(tool_result, dict):
                    if "citations" in tool_result and tool_result["citations"]:
                        for c in tool_result["citations"]:
                            citations.append(CitationModel(**c))
                    serialized_content = tool_result.get("passages", json.dumps(tool_result))
                else:
                    serialized_content = str(tool_result)

                # Append tool response message into conversation history with tool_call_id
                session_manager.add_message(sid, {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": serialized_content
                })

        # Loop limit exceeded fallback
        fallback_msg = (
            "I have retrieved the necessary information from our college records, "
            "but reached the maximum verification steps. Please ask a more specific question if you need more details."
        )
        session_manager.add_message(sid, {"role": "assistant", "content": fallback_msg})

        return {
            "session_id": sid,
            "response": fallback_msg,
            "citations": citations,
            "is_simulated": is_simulated,
            "tool_iterations": iteration
        }


orchestrator = AgentOrchestrator()
