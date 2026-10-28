"""
BUDDY AI — Legacy Gemini Service Shim
Delegates cloud reasoning and web research directly to Groq Service.
"""

from typing import Dict, Any, List, Optional
from .groq_service import is_groq_available, call_groq_chat


def is_gemini_available() -> bool:
    """Legacy alias: checks if Groq cloud reasoning is available."""
    return is_groq_available()


async def call_gemini_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> Dict[str, Any]:
    """Legacy alias: calls Groq chat engine."""
    return await call_groq_chat(messages, tools, temperature, max_tokens)
