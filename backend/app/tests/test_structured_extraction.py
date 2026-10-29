"""
BUDDY AI 2.0 — Structured Knowledge Extraction Tests
Verifies that event details, activities, guests, and dates are accurately extracted,
and that unspecified registration deadlines remain explicitly None.
"""

from pathlib import Path
from app.documents.processors.registry import processor_registry
from app.documents.extraction import extract_event_from_document, classify_document


def test_robotics_event_extraction_with_null_deadline(tmp_path: Path):
    """
    Synthetic notice for APCOER Robotics Innovation Day 2026.
    Notice states registration is required, but deliberately does NOT state a deadline.
    Must verify deadline remains None.
    """
    notice_file = tmp_path / "synthetic_robotics_notice.txt"
    notice_file.write_text("""
APCOER COLLEGE NOTICE

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
Please register via college portal.
""", encoding="utf-8")

    doc = processor_registry.process_file(notice_file)
    event = extract_event_from_document(doc)

    assert event is not None
    assert event.title == "APCOER Robotics Innovation Day 2026"
    assert event.date == "15 December 2026"
    assert "Main Auditorium" in event.venue
    assert "Dr. Example Guest" in event.guests
    assert len(event.activities) >= 4
    assert "Robotics exhibition" in event.activities
    assert event.registration_required is True
    # CRITICAL: Missing registration deadline must strictly remain None!
    assert event.registration_deadline is None


def test_event_extraction_from_csv(tmp_path: Path):
    csv_file = tmp_path / "synthetic_events.csv"
    csv_file.write_text("""Title,Date,Time,Venue,Chief Guest,Activities
APCOER Robotics Innovation Day 2026,15 December 2026,10:00 AM,Main Auditorium,Dr. Example Guest,Autonomous robot demonstrations; Technical presentations
""", encoding="utf-8")

    doc = processor_registry.process_file(csv_file)
    event = extract_event_from_document(doc)

    assert event is not None
    assert event.title == "APCOER Robotics Innovation Day 2026"
    assert event.date == "15 December 2026"
    assert "Main Auditorium" in event.venue
    assert event.registration_deadline is None


def test_document_classification():
    from app.documents.common import ExtractedDocument, DocumentType
    doc_event = ExtractedDocument(
        filename="hackathon.txt",
        file_hash="123",
        detected_file_type=DocumentType.TXT,
        title="Hackathon Notice",
        extracted_text="Join our annual robotics hackathon and symposium."
    )
    categories = classify_document(doc_event)
    assert "Event Announcement" in categories

    doc_faculty = ExtractedDocument(
        filename="faculty_list.txt",
        file_hash="456",
        detected_file_type=DocumentType.TXT,
        title="Faculty Roster",
        extracted_text="Associate Professor in Computer Engineering department, cabin 204."
    )
    categories_fac = classify_document(doc_faculty)
    assert "Faculty Record" in categories_fac

