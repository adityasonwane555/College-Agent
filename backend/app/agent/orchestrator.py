import json
import uuid
from typing import Dict, Any, List, Optional
from ..config import settings
from .prompts import SYSTEM_PROMPT
from .tool_registry import OLLAMA_TOOLS_SCHEMA, execute_tool
from ..services.ollama_service import call_ollama_chat, is_ollama_online
from ..services.groq_service import is_groq_available, call_groq_chat
from ..database.models import CitationModel
from .fast_path import resolve_fast_path


def is_web_or_research_query(query: str) -> bool:
    """Detects if user is asking for web research, live internet search, or external world facts."""
    q = query.lower().strip()
    web_keywords = [
        "search the web", "search internet", "search online", "look up online",
        "google", "browse the web", "web search", "internet search", "on the web",
        "find online", "research online", "latest news", "current weather", "today's news",
        "who is", "who won", "what happened", "stock price", "current price", "news about",
        "weather in", "latest updates", "recent events"
    ]
    if any(k in q for k in web_keywords):
        return True

    # Check if asking general research / facts without college terms
    college_keywords = [
        "apcoer", "college", "campus", "hod", "principal", "department", "admission",
        "fee", "hostel", "placement", "syllabus", "exam", "room", "faculty",
        "thakare", "kadam", "gaikwad", "totla", "abmsp"
    ]
    has_college_context = any(k in q for k in college_keywords)
    if not has_college_context:
        research_indicators = [
            "research", "explain", "compare", "how does", "what is", "why is",
            "tell me about", "history of", "future of", "technology trends", "who invented"
        ]
        if any(q.startswith(ri) or f" {ri} " in q for ri in research_indicators):
            return True

    return False


class SessionManager:
    """Manages isolated conversation histories by session ID."""
    def __init__(self, max_history: int = 15):
        self.max_history = max_history
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.sessions[session_id]

    def add_message(self, session_id: str, message: Dict[str, Any]):
        history = self.get_history(session_id)
        history.append(message)
        # Keep system prompt at [0] and trim older messages
        if len(history) > self.max_history + 1:
            self.sessions[session_id] = [history[0]] + history[-(self.max_history):]

    def reset_session(self, session_id: str):
        self.sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]


session_manager = SessionManager(max_history=settings.SESSION_MAX_HISTORY)


class AgentOrchestrator:
    """Coordinates Ollama & Groq model calls, tool execution, and citation grounding."""

    async def run(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        status_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
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

        citations: List[CitationModel] = []
        is_simulated = False
        iteration = 0

        use_groq = is_groq_available()
        is_web_research = is_web_or_research_query(user_message)

        while iteration < settings.MAX_TOOL_ITERATIONS:
            iteration += 1
            history = session_manager.get_history(sid)

            if status_callback:
                await status_callback("thinking", f"Processing response (step {iteration})...")

            assistant_msg = None

            # Priority 1: Groq Cloud AI for Web-Based Questions, Deep Research, or when requested
            if use_groq and (is_web_research or not getattr(settings, "USE_LOCAL_LLM_FIRST", True)):
                try:
                    assistant_msg = await call_groq_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Groq web/research error: {e}, attempting Ollama fallback...")
                    assistant_msg = None

            # Priority 2: Local Ollama Model (qwen2.5:3b on GPU) for college campus queries
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

            # Priority 3: Groq Cloud AI Fallback if Ollama was offline or failed on college query
            if not assistant_msg and use_groq:
                try:
                    assistant_msg = await call_groq_chat(
                        messages=history,
                        tools=OLLAMA_TOOLS_SCHEMA
                    )
                except Exception as e:
                    print(f"[Orchestrator] Groq fallback error: {e}")
                    use_groq = False

            # Priority 4: Fallback to call_ollama_chat (handles local execution or smart mock fallback)
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
