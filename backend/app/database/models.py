"""
BUDDY AI 2.0 — Relational Knowledge & Agent Domain Schemas

Architecture & Data Layer:
  - Strongly-Typed Pydantic Models:
      - Validates and serializes database entities, REST payloads, and internal agent state transitions.
  - Relational Entity Schemas:
      - FAQModel: Curated frequently asked questions with categorization.
      - DepartmentModel: Academic and administrative departments with HOD, code, and location.
      - RoomModel: Campus rooms, laboratories, and physical spaces with floor and building mapping.
      - FacultyModel: Academic profiles, designations, office hours, and research expertise.
      - CollegeHoursModel: Operational schedules and opening/closing intervals across facilities.
      - EventModel: Verified campus events, symposiums, hackathons, and registration metadata.
      - AnnouncementModel: Campus circulars with prioritized broadcast levels (Normal, High, Urgent).
  - Document Lifecycle & Knowledge Staging:
      - DocumentMetadataModel: Multi-format document tracking with SHA-256 integrity hashes and status.
      - DocumentVersionModel: Audit logs for tracked document revisions and diff summaries.
      - PendingKnowledgeModel: Unapproved extracted knowledge entities queued for administrative review.
  - Conversational Grounding:
      - CitationModel: Source attribution passages containing page, section, and relevance metrics.
      - ChatMessageModel: Multi-turn dialog turns including roles, tool calls, and citations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FAQModel(BaseModel):
    """
    Schema for curated campus frequently asked questions and official answers.
    """
    id: Optional[int] = None
    question: str
    answer: str
    category: str = "General"


class DepartmentModel(BaseModel):
    """
    Schema for academic and administrative department records in the campus directory.
    """
    id: Optional[int] = None
    name: str
    code: str
    block: str
    floor: str
    hod: str
    contact_email: str
    description: str


class RoomModel(BaseModel):
    """
    Schema for campus classrooms, research laboratories, auditoriums, and administrative offices.
    """
    id: Optional[int] = None
    room_number: str
    name: str
    building: str
    floor: str
    purpose: str


class FacultyModel(BaseModel):
    """
    Schema for faculty member academic profiles, consultation hours, and contact details.
    """
    id: Optional[int] = None
    name: str
    department: str
    designation: str
    cabin: str
    email: str
    office_hours: str
    qualification: Optional[str] = ""
    experience: Optional[str] = ""
    area_of_interest: Optional[str] = ""
    research_profile: Optional[str] = ""


class CollegeHoursModel(BaseModel):
    """
    Schema for operational schedules across campus departments, libraries, and laboratories.
    """
    id: Optional[int] = None
    facility_name: str
    open_time: str
    close_time: str
    days: str
    notes: Optional[str] = ""


class EventModel(BaseModel):
    """
    Schema for official college events, conferences, symposiums, and placement drives.
    """
    id: Optional[int] = None
    title: str
    date: str
    time: str
    venue: str
    description: str
    organizer: str
    activities: Optional[str] = ""
    guests: Optional[str] = ""
    eligibility: Optional[str] = ""
    registration_required: Optional[bool] = False
    registration_deadline: Optional[str] = None
    registration_url: Optional[str] = None
    contact_info: Optional[str] = ""
    document_id: Optional[int] = None
    version: Optional[int] = 1
    status: Optional[str] = "approved"


class AnnouncementModel(BaseModel):
    """
    Schema for official circulars and campus broadcasts with priority classification.
    """
    id: Optional[int] = None
    title: str
    content: str
    date_posted: str
    priority: str = "Normal"  # Normal, High, Urgent


class DocumentMetadataModel(BaseModel):
    """
    Schema for tracked knowledge documents, versioning counters, and SHA-256 integrity hashes.
    """
    id: Optional[int] = None
    filename: str
    title: str
    total_pages: int
    uploaded_at: str
    chunk_count: int
    file_hash: Optional[str] = ""
    content_type: Optional[str] = "application/octet-stream"
    detected_type: Optional[str] = "unknown"
    status: Optional[str] = "approved"
    version: Optional[int] = 1
    warnings: Optional[str] = ""
    metadata_json: Optional[str] = "{}"


class DocumentVersionModel(BaseModel):
    """
    Schema for document version history, revision diff summaries, and modification audits.
    """
    id: Optional[int] = None
    document_id: int
    version: int
    file_hash: str
    filename: str
    action: str  # created, updated, revised, approved, rejected, superseded
    timestamp: str
    diff_summary: Optional[str] = ""
    actor: Optional[str] = "system"


class PendingKnowledgeModel(BaseModel):
    """
    Schema for staged entities awaiting administrator verification before active indexing.
    """
    id: Optional[int] = None
    document_id: Optional[int] = None
    entity_type: str  # event, faculty, department, general
    entity_id: Optional[int] = None
    extracted_data: str  # JSON
    status: str = "pending"  # pending, approved, rejected
    confidence: Optional[float] = 1.0
    created_at: str
    reviewed_at: Optional[str] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = ""


class CitationModel(BaseModel):
    """
    Schema for verifiable knowledge attribution citations attached to agent responses.
    """
    source: str
    page: Optional[int] = None
    section: Optional[str] = None
    relevance_score: Optional[float] = None
    snippet: str


class ChatMessageModel(BaseModel):
    """
    Schema for multi-turn dialog history turns including roles, tool calls, and citations.
    """
    role: str  # user, assistant, system, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    citations: Optional[List[CitationModel]] = None
