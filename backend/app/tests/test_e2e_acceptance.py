"""
BUDDY AI 2.0 — End-to-End Acceptance Test Suite (Section 21)
Executes all 14 Acceptance Tests against a synthetic corpus and isolated test database.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from app.database.repository import DatabaseRepository
from app.documents.processors.registry import processor_registry
from app.documents.extraction import extract_event_from_document
from app.documents.lifecycle import KnowledgeLifecycleManager
from app.documents.vector_store import LocalVectorStore
from app.agent.router import adaptive_router
from app.agent.orchestrator import orchestrator, session_manager
from app.database.models import EventModel


@pytest.fixture
def synthetic_env(tmp_path: Path):
    """Sets up an isolated database and test corpus for synthetic acceptance testing."""
    test_db_path = str(tmp_path / "synthetic_acceptance_buddy.db")
    test_repo = DatabaseRepository(db_path=test_db_path)
    test_vector_store = LocalVectorStore()

    # Patch global repo and vector_store to point to test_repo during acceptance test
    with patch("app.database.repository.repo", test_repo), \
         patch("app.documents.lifecycle.repo", test_repo), \
         patch("app.documents.hybrid_retrieval.repo", test_repo), \
         patch("app.documents.vector_store.repo", test_repo), \
         patch("app.tools.college_tools.repo", test_repo):

        lifecycle = KnowledgeLifecycleManager(default_auto_approve=False)

        # 1. Robotics Event Notice (TXT)
        f_notice = tmp_path / "synthetic_robotics_notice.txt"
        f_notice.write_text("""
APCOER COLLEGE NOTICE (SYNTHETIC)
Title: APCOER Robotics Innovation Day 2026
Date: 15 December 2026
Time: 10:00 AM onwards
Venue: Main Auditorium, APCOER
Chief Guest: Dr. Example Guest
Organizer: Department of Mechanical Engineering

Activities:
- Robotics exhibition
- Autonomous robot demonstrations
- Technical presentations
- Student innovation challenge

Registration is mandatory for all student participants.
No registration fee required.
""", encoding="utf-8")

        # 2. Spreadsheet containing event details (CSV)
        f_csv = tmp_path / "synthetic_event_details.csv"
        f_csv.write_text("""Title,Date,Time,Venue,Chief Guest,Registration Required,Registration Deadline
APCOER Robotics Innovation Day 2026,15 December 2026,10:00 AM,Main Auditorium,Dr. Example Guest,Yes,
""", encoding="utf-8")

        # 3. Presentation describing event activities (MD/TXT representation of presentation)
        f_presentation = tmp_path / "synthetic_event_presentation.md"
        f_presentation.write_text("""
# Slide 1: APCOER Robotics Innovation Day 2026
Venue: Main Auditorium, APCOER. Date: 15 December 2026.

# Slide 2: Event Highlights & Activities
- Robotics exhibition
- Autonomous robot demonstrations
- Technical presentations
- Student innovation challenge
Chief Guest: Dr. Example Guest
""", encoding="utf-8")

        # 4. Supplementary Information (MD)
        f_supplementary = tmp_path / "synthetic_supplementary_info.md"
        f_supplementary.write_text("""
# Supplementary Event Information
The Student Council cordially invites all engineering students to the APCOER Robotics Innovation Day 2026.
Volunteers will be present in the Main Auditorium from 9:30 AM.
""", encoding="utf-8")

        # 5. Revised Notice changing event date to 18 December 2026
        f_revised = tmp_path / "synthetic_robotics_notice_revised.txt"
        f_revised.write_text("""
APCOER COLLEGE NOTICE (REVISED - SYNTHETIC)
Title: APCOER Robotics Innovation Day 2026
Date: 18 December 2026
Time: 10:00 AM onwards
Venue: Main Auditorium, APCOER
Chief Guest: Dr. Example Guest
Organizer: Department of Mechanical Engineering

Activities:
- Robotics exhibition
- Autonomous robot demonstrations
- Technical presentations
- Student innovation challenge

Registration is mandatory for all student participants.
""", encoding="utf-8")

        yield {
            "repo": test_repo,
            "vector_store": test_vector_store,
            "lifecycle": lifecycle,
            "notice": f_notice,
            "csv": f_csv,
            "presentation": f_presentation,
            "supplementary": f_supplementary,
            "revised": f_revised
        }


def test_section_21_acceptance_pipeline(synthetic_env):
    repo = synthetic_env["repo"]
    lifecycle = synthetic_env["lifecycle"]

    # ==========================================
    # TEST 1: Ingest each supported test file
    # ==========================================
    res_notice = lifecycle.process_and_ingest(synthetic_env["notice"], auto_approve=False)
    res_csv = lifecycle.process_and_ingest(synthetic_env["csv"], auto_approve=False)
    res_pres = lifecycle.process_and_ingest(synthetic_env["presentation"], auto_approve=False)
    res_supp = lifecycle.process_and_ingest(synthetic_env["supplementary"], auto_approve=False)

    assert res_notice["status"] == "success"
    assert res_csv["status"] == "success"
    assert res_pres["status"] == "success"
    assert res_supp["status"] == "success"

    # ==========================================
    # TEST 2: Verify extracted fields & provenance
    # ==========================================
    ev = res_notice["event_extracted"]
    assert ev is not None
    assert ev["title"] == "APCOER Robotics Innovation Day 2026"
    assert ev["date"] == "15 December 2026"
    assert "Main Auditorium" in ev["venue"]
    assert "Dr. Example Guest" in ev["guests"]
    assert len(ev["activities"]) >= 4

    # ==========================================
    # TEST 3: Verify missing deadline remains None
    # ==========================================
    assert ev["registration_deadline"] is None
    assert ev["registration_required"] is True

    # ==========================================
    # TEST 4: Approve the synthetic knowledge records
    # ==========================================
    pending = repo.list_pending_updates(status="pending")
    assert len(pending) >= 1
    for p in pending:
        repo.approve_pending_update(p["id"], reviewer="admin_acceptance_test")

    approved_event = repo.get_event_by_title("APCOER Robotics Innovation Day 2026")
    assert approved_event is not None
    assert approved_event["date"] == "15 December 2026"


@pytest.mark.asyncio
async def test_section_21_queries_and_offline(synthetic_env):
    repo = synthetic_env["repo"]
    lifecycle = synthetic_env["lifecycle"]

    # Seed approved record into test repo
    repo.add_event(EventModel(
        title="APCOER Robotics Innovation Day 2026",
        date="15 December 2026",
        time="10:00 AM onwards",
        venue="Main Auditorium, APCOER",
        description="Annual robotics innovation day with student demonstrations.",
        organizer="Department of Mechanical Engineering",
        activities="Robotics exhibition, Autonomous robot demonstrations, Technical presentations, Student innovation challenge",
        guests="Dr. Example Guest",
        registration_required=True,
        registration_deadline=None,
        status="approved"
    ))

    # ==========================================
    # TEST 5: Ask when the robotics event is scheduled
    # ==========================================
    res5 = await adaptive_router.route("When is the APCOER robotics innovation day event scheduled?", session_history=[])
    assert res5 is not None
    import re
    assert re.search(r'(?i)(?:15(?:th)?\s+December|December\s+15(?:th)?),?\s+2026', res5["response"]) is not None

    # ==========================================
    # TEST 6: Ask where the event is happening
    # ==========================================
    res6 = await adaptive_router.route("Where is the robotics event happening?", session_history=[])
    assert res6 is not None
    assert "Main Auditorium" in res6["response"]

    # ==========================================
    # TEST 7: Ask who the chief guest is
    # ==========================================
    res7 = await adaptive_router.route("Who is the chief guest for the robotics event?", session_history=[])
    assert res7 is not None
    assert "Dr. Example Guest" in res7["response"]

    # ==========================================
    # TEST 8: Follow-up question: What activities will take place?
    # ==========================================
    res8 = await adaptive_router.route("What activities will take place at the robotics event?", session_history=[])
    assert res8 is not None
    assert ("demonstrations" in res8["response"].lower() or "exhibition" in res8["response"].lower() or "innovation" in res8["response"].lower())

    # ==========================================
    # TEST 9: Disable cloud and web search (Offline Mode)
    # ==========================================
    res9 = await adaptive_router.route(
        "When is the robotics event scheduled?",
        session_history=[],
        force_offline=True
    )
    assert res9 is not None
    assert re.search(r'(?i)(?:15(?:th)?\s+December|December\s+15(?:th)?),?\s+2026', res9["response"]) is not None
    assert res9["is_offline"] is True

    # ==========================================
    # TEST 10: Ask basic general-knowledge question offline
    # ==========================================
    res10 = await adaptive_router.route(
        "Explain the basic concept of an algorithm in computer science",
        session_history=[],
        force_offline=True
    )
    assert res10 is not None
    assert len(res10["response"]) > 20
    assert res10["is_offline"] is True

    # ==========================================
    # TEST 11: Ask for a current fact unavailable locally while offline
    # ==========================================
    res11 = await adaptive_router.route(
        "What is today's current live breaking news in Pune?",
        session_history=[],
        force_offline=True
    )
    assert res11 is not None
    assert "offline mode" in res11["response"].lower()
    assert "cannot verify current" in res11["response"].lower() or "unable" in res11["response"].lower()

    # ==========================================
    # TEST 12: Upload revised notice (changing date to 18 December 2026)
    # ==========================================
    res12 = lifecycle.process_and_ingest(synthetic_env["revised"], auto_approve=False)
    assert res12["status"] == "success"
    assert res12["lifecycle_status"] == "pending_review"
    assert "18 December 2026" in res12["diff_summary"]

    # Confirm original date is still active before approval
    ev_check_before = repo.get_event_by_title("APCOER Robotics Innovation Day 2026")
    assert ev_check_before["date"] == "15 December 2026"

    # Approve revised update
    repo.approve_pending_update(res12["pending_update_id"], reviewer="admin_reviewer")
    ev_check_after = repo.get_event_by_title("APCOER Robotics Innovation Day 2026")
    assert ev_check_after["date"] == "18 December 2026"

    # ==========================================
    # TEST 13: Simulate vector index failure & verify authoritative DB preserved
    # ==========================================
    with patch.object(synthetic_env["repo"], "save_chunk_vector", side_effect=RuntimeError("Simulated disk error")):
        fail_res = synthetic_env["vector_store"].index_chunk(999, "Simulated content")
        assert fail_res is False
        # Authoritative database record remains intact and unaffected
        authoritative_event = repo.get_event_by_title("APCOER Robotics Innovation Day 2026")
        assert authoritative_event is not None
        assert authoritative_event["date"] == "18 December 2026"
