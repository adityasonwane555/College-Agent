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
