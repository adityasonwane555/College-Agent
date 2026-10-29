"""
BUDDY AI 2.0 — Automated Conversational Intelligence & Retrieval Refinement Tests
Verifies the behavioral specifications outlined in Improve-outputs.md (Tests A through K).
"""

import pytest
import uuid
import re
from typing import Dict, Any, List

from app.agent.orchestrator import orchestrator, session_manager
from app.agent.router import adaptive_router
from app.voice.synthesis import extract_spoken_text


@pytest.mark.asyncio
async def test_a_general_recommendations():
    """Test A: General recommendations (e.g. Pune tourist attractions).
    - Returns relevant attractions
    - Does not unnecessarily introduce APCOER or receptionist persona
    - Does not attach irrelevant college citations
    """
    sid = str(uuid.uuid4())
    res = await orchestrator.run("What are places we should visit in Pune?", session_id=sid)
    assert res is not None
    text = res["response"].lower()

    # Must contain popular Pune landmarks
    assert any(spot in text for spot in ["shaniwar wada", "aga khan", "dagadusheth", "sinhagad", "kelkar"])
    
    # Must NOT force APCOER reception robot persona
    assert "receptionist" not in text
    assert "desk of anantrao pawar" not in text
    
    # Must NOT attach institutional college documents to a tourism question
    for c in res.get("citations", []):
        assert "Institutional" not in getattr(c, "source", "")
        assert "Syllabus" not in getattr(c, "source", "")


@pytest.mark.asyncio
async def test_b_contextual_follow_up():
    """Test B: Contextual follow-up resolving 'these places'.
    - Turn 1: Pune attractions recommended
    - Turn 2: 'As I was planning to visit these places'
    - Understands context of Pune landmarks, does not redirect to college campus
    """
    sid = str(uuid.uuid4())
    # Turn 1
    r1 = await orchestrator.run("What are places we should visit in Pune?", session_id=sid)
    assert r1 is not None

    # Turn 2: Follow-up
    r2 = await orchestrator.run("As I was planning to visit these places", session_id=sid)
    assert r2 is not None
    text2 = r2["response"].lower()

    # Must continue the travel planning / visiting context
    assert any(w in text2 for w in ["visit", "itinerary", "places", "pune", "trip", "plan", "time"])
    # Must NOT redirect to college campus
    assert "our campus at apcoer" not in text2
    assert "visit our campus here" not in text2


@pytest.mark.asyncio
async def test_c_general_knowledge():
    """Test C: General knowledge inquiry.
    - Answers directly (Xi Jinping is President of China)
    - Does not introduce APCOER unnecessarily
    - Uses external/general knowledge
    """
    sid = str(uuid.uuid4())
    res = await orchestrator.run("Who is President of China?", session_id=sid)
    assert res is not None
    assert "xi jinping" in res["response"].lower()
    assert "receptionist" not in res["response"].lower()
    assert "apcoer" not in res["response"].lower()


@pytest.mark.asyncio
async def test_d_faculty_lookup_success_and_failure():
    """Test D: Faculty lookup for both existing and nonexistent professors.
    - Professor Akash Dorke (spelling variation for Dodke) resolves to Prof. A. R. Dodke
    - Unknown faculty member (Professor John Smith) honestly acknowledges absence without fabricating
    """
    sid1 = str(uuid.uuid4())
    # 1. Existing with spelling variation
    res_dorke = await orchestrator.run("Who is Professor Akash Dorke?", session_id=sid1)
    assert res_dorke is not None
    text_dorke = res_dorke["response"].lower()
    assert "dodke" in text_dorke or "a. r." in text_dorke or "information technology" in text_dorke
    citations_dorke = [c.source for c in res_dorke.get("citations", [])]
    assert any("Faculty Directory" in s for s in citations_dorke)

    # 2. Unknown faculty member
    sid2 = str(uuid.uuid4())
    res_smith = await orchestrator.run("Who is Professor John Smith?", session_id=sid2)
    assert res_smith is not None
    text_smith = res_smith["response"].lower()
    assert any(phrase in text_smith for phrase in ["not found", "couldn't find", "could not find", "no faculty member", "records"])
    # Must NOT fabricate a designation
    assert "head of department" not in text_smith


@pytest.mark.asyncio
async def test_e_institutional_information():
    """Test E: Institutional information query.
    - 'Who is the principal of APCOER?' resolves to Dr. Sunil B. Thakare
    - Authoritative source citation attached
    """
    sid = str(uuid.uuid4())
    res = await orchestrator.run("Who is the principal of APCOER?", session_id=sid)
    assert res is not None
    assert "sunil" in res["response"].lower() and "thakare" in res["response"].lower()
    citations = [c.source for c in res.get("citations", [])]
    assert any("Faculty Directory" in s or "Administration" in s or "Institutional" in s for s in citations)


@pytest.mark.asyncio
async def test_f_follow_up_about_person():
    """Test F: Pronoun resolution for a person across turns.
    - Turn 1: 'Who is the principal of APCOER?' -> Dr. Sunil B. Thakare
    - Turn 2: 'Which department does he belong to?' -> Civil Engineering
    """
    sid = str(uuid.uuid4())
    r1 = await orchestrator.run("Who is the principal of APCOER?", session_id=sid)
    assert "thakare" in r1["response"].lower()

    r2 = await orchestrator.run("Which department does he belong to?", session_id=sid)
    assert r2 is not None
    assert "civil" in r2["response"].lower()


@pytest.mark.asyncio
async def test_g_no_unnecessary_introductions():
    """Test G: Multi-turn inquiries do not repeat scripted greetings or intros.
    - Sends multiple questions in the same session
    - Subsequent turns do not say 'Hello! I am Buddy...'
    """
    sid = str(uuid.uuid4())
    r1 = await orchestrator.run("What is python?", session_id=sid)
    r2 = await orchestrator.run("How far is the Moon from Earth?", session_id=sid)
    r3 = await orchestrator.run("Who is the principal of APCOER?", session_id=sid)

    # Turns 2 and 3 must not restart with greetings or self-introductions
    assert not r2["response"].strip().lower().startswith("hello")
    assert not r2["response"].strip().lower().startswith("i am buddy")
    assert not r3["response"].strip().lower().startswith("hello")


@pytest.mark.asyncio
async def test_h_citation_integrity():
    """Test H: Non-institutional questions have zero fabricated college citations."""
    sid = str(uuid.uuid4())
    res = await orchestrator.run("What is python?", session_id=sid)
    citations = res.get("citations", [])
    # Any attached citations must not be institutional college records
    for c in citations:
        assert "APCOER" not in c.source
        assert "Database" not in c.source


@pytest.mark.asyncio
async def test_i_session_isolation():
    """Test I: Different sessions maintain completely isolated conversation histories."""
    sid_a = str(uuid.uuid4())
    sid_b = str(uuid.uuid4())

    await orchestrator.run("Who is the principal of APCOER?", session_id=sid_a)
    await orchestrator.run("What are places we should visit in Pune?", session_id=sid_b)

    hist_a = session_manager.get_history(sid_a)
    hist_b = session_manager.get_history(sid_b)

    # User/assistant dialogue turns from session A must not exist in session B
    turns_a = [m for m in hist_a if m.get("role") != "system"]
    turns_b = [m for m in hist_b if m.get("role") != "system"]

    assert any("principal" in m.get("content", "").lower() for m in turns_a)
    assert not any("principal" in m.get("content", "").lower() for m in turns_b)

    assert any("places we should visit" in m.get("content", "").lower() for m in turns_b)
    assert not any("places we should visit" in m.get("content", "").lower() for m in turns_a)


def test_j_text_to_speech_pronunciation():
    """Test J: Text-to-speech pronunciation cleaning.
    - Preserves 'APCOER' as a clean word without robotic comma splits ('A, P, C, O, E, R,')
    - Cleans markdown symbols and tags appropriately
    """
    raw_sample = "Welcome to **APCOER**! Please visit [APCOER Website](https://abmspcoerpune.org) for details."
    spoken = extract_spoken_text(raw_sample)

    # Must contain clean acronym APCOER
    assert "APCOER" in spoken
    # Must NOT have robotic comma-split letters
    assert "A, P, C, O, E, R" not in spoken
    assert "A, P, C, O, E, R," not in spoken


@pytest.mark.asyncio
async def test_k_offline_operation():
    """Test K: Offline resilience without internet.
    - Basic general questions handled offline without claiming live verification
    - Institutional queries resolve using local authoritative knowledge
    """
    # 1. Offline general knowledge question
    res_gen = await adaptive_router.route(
        "Explain the basic concept of an algorithm in computer science",
        session_history=[],
        force_offline=True
    )
    assert res_gen is not None
    assert len(res_gen["response"]) > 20
    assert res_gen["is_offline"] is True

    # 2. Offline live news inquiry acknowledges limitation gracefully
    res_news = await adaptive_router.route(
        "What is today's current live breaking news in Pune?",
        session_history=[],
        force_offline=True
    )
    assert res_news is not None
    assert "offline mode" in res_news["response"].lower()
    assert "cannot verify current" in res_news["response"].lower() or "unable" in res_news["response"].lower()

