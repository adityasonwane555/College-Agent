"""
BUDDY AI 2.0 — Multi-Model Orchestration & Offline AI Tests
Verifies adaptive routing, offline execution without cloud dependencies,
circuit-breaker tripping, and factual grounding checks.
"""

import pytest
from app.agent.router import adaptive_router, classify_query_intent, QueryIntent
from app.services.unified_provider import provider_manager
from app.agent.grounding import verify_response_grounding


def test_query_intent_classification():
    assert classify_query_intent("Hello Buddy, good morning!") == QueryIntent.GREETING
    assert classify_query_intent("When is the APCOER robotics innovation day event?") == QueryIntent.DIRECT_COLLEGE_FACT
    assert classify_query_intent("What is the current stock price of Apple today?") == QueryIntent.CURRENT_EVENT
    assert classify_query_intent("Explain how a transformer neural network works") == QueryIntent.GENERAL_KNOWLEDGE


@pytest.mark.asyncio
async def test_offline_routing_greeting():
    res = await adaptive_router.route("hello buddy", session_history=[], force_offline=True)
    assert res is not None
    assert "namaste" in res["response"].lower() or "hello" in res["response"].lower() or "welcome" in res["response"].lower()
    assert res["is_offline"] is True


@pytest.mark.asyncio
async def test_offline_current_event_limitation():
    # In offline mode, live current news must acknowledge limitation instead of hallucinating
    res = await adaptive_router.route("What is today's current live news in Pune?", session_history=[], force_offline=True)
    assert res is not None
    assert "offline mode" in res["response"].lower()
    assert res["is_offline"] is True


def test_factual_grounding_contradiction_detection():
    verified_facts = [
        {
            "content": "APCOER Robotics Innovation Day 2026 takes place on 18 December 2026.",
            "metadata": {
                "title": "APCOER Robotics Innovation Day 2026",
                "date": "18 December 2026",
                "venue": "Main Auditorium"
            }
        }
    ]

    # Model hallucinates an old/wrong date "15 December 2026"
    hallucinated_text = "The APCOER Robotics Innovation Day 2026 will be held on 15 December 2026 in the auditorium."
    grounded_text, corrections = verify_response_grounding(hallucinated_text, verified_facts)

    assert len(corrections) >= 1
    assert "18 December 2026" in grounded_text
    assert "15 December 2026" not in grounded_text


def test_circuit_breaker():
    provider_manager.trip_breaker("gemini", cooldown_seconds=10.0)
    assert provider_manager.is_breaker_open("gemini") is True

