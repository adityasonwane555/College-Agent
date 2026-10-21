import pytest
from app.database.repository import DatabaseRepository
from app.database.models import FAQModel, DepartmentModel, RoomModel
from app.tools.college_tools import (
    search_faq, get_department, get_room, get_faculty, get_college_hours
)


def test_database_initialization(tmp_path):
    test_db = str(tmp_path / "test_buddy.db")
    repo = DatabaseRepository(test_db)
    assert repo is not None
    # Verify tables created
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "faqs" in tables
        assert "departments" in tables
        assert "rooms" in tables
        assert "faculty" in tables
        assert "document_chunks" in tables


def test_faq_retrieval(tmp_path):
    test_db = str(tmp_path / "test_buddy.db")
    repo = DatabaseRepository(test_db)
    faq_id = repo.add_faq(FAQModel(
        question="Where is the library located?",
        answer="Central Library is in Building 3, 1st Floor.",
        category="Facilities"
    ))
    assert faq_id > 0
    results = repo.search_faq("library")
    assert len(results) == 1
    assert "Central Library" in results[0]["answer"]


def test_department_lookup_and_missing_info(tmp_path):
    test_db = str(tmp_path / "test_buddy.db")
    repo = DatabaseRepository(test_db)
    repo.add_department(DepartmentModel(
        name="Aerospace Engineering",
        code="AERO",
        block="Aero Block",
        floor="Ground Floor",
        hod="Dr. Vikram",
        contact_email="aero@college.edu",
        description="Aviation and aerodynamics."
    ))

    # Existing department
    dept = repo.get_department("Aerospace")
    assert dept is not None
    assert dept["code"] == "AERO"

    # Missing department
    missing = repo.get_department("Astrophysics Nonexistent")
    assert missing is None
