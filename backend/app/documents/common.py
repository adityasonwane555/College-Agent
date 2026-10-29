"""
BUDDY AI 2.0 — Common Document Ingestion Models & Status Types
Defines the standard internal representation for all ingested and processed documents.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    JSON = "json"
    YAML = "yaml"
    HTML = "html"
    XML = "xml"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class IngestionStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    ARCHIVED = "archived"


class ExtractedChunk(BaseModel):
    chunk_index: int
    page_number: int = 1
    section_title: str = "General"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    document_id: Optional[int] = None
    filename: str
    file_hash: str
    detected_file_type: DocumentType
    content_type: str = "application/octet-stream"
    title: str
    extracted_text: str = ""
    structured_content: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[ExtractedChunk] = Field(default_factory=list)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str = "standard"
    status: IngestionStatus = IngestionStatus.PROCESSING
    warnings: List[str] = Field(default_factory=list)
    processing_duration_seconds: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    version: int = 1

