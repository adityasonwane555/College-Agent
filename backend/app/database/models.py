from typing import Optional, List
from pydantic import BaseModel, Field


class FAQModel(BaseModel):
    id: Optional[int] = None
    question: str
    answer: str
    category: str = "General"


class DepartmentModel(BaseModel):
    id: Optional[int] = None
    name: str
    code: str
    block: str
    floor: str
    hod: str
    contact_email: str
    description: str


class RoomModel(BaseModel):
    id: Optional[int] = None
    room_number: str
    name: str
    building: str
    floor: str
    purpose: str


class FacultyModel(BaseModel):
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
    id: Optional[int] = None
    facility_name: str
    open_time: str
    close_time: str
    days: str
    notes: Optional[str] = ""


class EventModel(BaseModel):
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
    id: Optional[int] = None
    title: str
    content: str
    date_posted: str
    priority: str = "Normal"  # Normal, High, Urgent


class DocumentMetadataModel(BaseModel):
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
    source: str
    page: Optional[int] = None
    section: Optional[str] = None
    relevance_score: Optional[float] = None
    snippet: str


class ChatMessageModel(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    citations: Optional[List[CitationModel]] = None
