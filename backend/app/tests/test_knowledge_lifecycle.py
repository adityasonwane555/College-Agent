"""
BUDDY AI 2.0 — Knowledge Lifecycle, Approval & Versioning Tests
Verifies duplicate detection, revision diff tracking, approval policy,
audit trail, and derived index recovery.
"""

from pathlib import Path
from unittest.mock import patch
from app.database.repository import DatabaseRepository
from app.documents.lifecycle import KnowledgeLifecycleManager
from app.documents.vector_store import LocalVectorStore


def test_duplicate_detection(tmp_path: Path):
    test_db = DatabaseRepository(db_path=str(tmp_path / "lifecycle_test.db"))
    test_lifecycle = KnowledgeLifecycleManager(default_auto_approve=True)

    with patch("app.database.repository.repo", test_db), \
         patch("app.documents.lifecycle.repo", test_db):

        doc_path = tmp_path / "synthetic_syllabus.txt"
        doc_path.write_text("Artificial Intelligence and Data Science Syllabus 2026 APCOER.", encoding="utf-8")

        res1 = test_lifecycle.process_and_ingest(doc_path, auto_approve=True)
        assert res1["status"] == "success"

        # Ingest the exact same file again
        res2 = test_lifecycle.process_and_ingest(doc_path, auto_approve=True)
        assert res2["status"] == "duplicate"
        assert "duplicate" in res2["message"].lower()


def test_event_revision_and_approval_workflow(tmp_path: Path):
    test_db = DatabaseRepository(db_path=str(tmp_path / "revision_test.db"))
    test_lifecycle = KnowledgeLifecycleManager(default_auto_approve=False)

    with patch("app.database.repository.repo", test_db), \
         patch("app.documents.lifecycle.repo", test_db):

        # Notice 1: Original date 15 December 2026
        v1_file = tmp_path / "robotics_notice_v1.txt"
        v1_file.write_text("""
APCOER NOTICE
Title: APCOER Robotics Innovation Day 2026
Date: 15 December 2026
Time: 10:00 AM onwards
Venue: Main Auditorium, APCOER
Chief Guest: Dr. Example Guest
""", encoding="utf-8")

        res1 = test_lifecycle.process_and_ingest(v1_file, auto_approve=True)
        assert res1["status"] == "success"

        event_record = test_db.get_event_by_title("APCOER Robotics Innovation Day 2026")
        assert event_record is not None
        assert event_record["date"] == "15 December 2026"

        # Notice 2: Revised date 18 December 2026 (requires review)
        v2_file = tmp_path / "robotics_notice_v2.txt"
        v2_file.write_text("""
APCOER NOTICE (REVISED)
Title: APCOER Robotics Innovation Day 2026
Date: 18 December 2026
Time: 10:00 AM onwards
Venue: Main Auditorium, APCOER
Chief Guest: Dr. Example Guest
""", encoding="utf-8")

        res2 = test_lifecycle.process_and_ingest(v2_file, auto_approve=False)
        assert res2["status"] == "success"
        assert res2["lifecycle_status"] == "pending_review"
        assert "18 December 2026" in res2["diff_summary"]

        # Before approval, original record remains authoritative in database
        ev_before = test_db.get_event_by_title("APCOER Robotics Innovation Day 2026")
        assert ev_before["date"] == "15 December 2026"

        # Admin approves pending update
        update_id = res2["pending_update_id"]
        assert update_id is not None
        approved = test_db.approve_pending_update(update_id, reviewer="admin_tester")
        assert approved is True

        # After approval, authoritative database is updated to revised date
        ev_after = test_db.get_event_by_title("APCOER Robotics Innovation Day 2026")
        assert ev_after["date"] == "18 December 2026"


def test_index_rebuild_and_recovery():
    test_vs = LocalVectorStore()
    res = test_vs.rebuild_all_indexes()
    assert res["status"] in ["success", "partial_success"]
    assert res["fts_indexed_chunks"] >= 0
