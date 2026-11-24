"""
BUDDY AI 2.0 — Common Document Ingestion Models & Status Types

Architecture & Document Canonical Model:
  - Universal Intermediate Representation (IR):
      - Normalizes diverse file formats (PDF, DOCX, TXT, CSV, XLSX, PPTX, JSON, YAML, HTML, code) into a unified ExtractedDocument envelope.
  - Chunk Data Contracts:
      - Breaks large documents into serialized ExtractedChunk objects retaining original page numbers, section headers, and relational metadata.
  - Lifecycle State Enumeration:
      - Tracks document progression through UPLOADED, PROCESSING, PENDING_REVIEW, APPROVED, REJECTED, SUPERSEDED, and ARCHIVED.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentType(str, Enum):
    """
    Supported document format classifications handled by the processor registry.
    """
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
    """
    Lifecycle milestones for knowledge documents entering the repository.
    """
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    ARCHIVED = "archived"


class ExtractedChunk(BaseModel):
    """
    A segmented passage of text derived from a document, enriched with page and section anchors for RAG attribution.
    """
    chunk_index: int
    page_number: int = 1
    section_title: str = "General"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """
    Canonical document envelope containing extracted full-text, structured JSON metadata,
    and segmented chunk collections produced by format-specific processors.
    """
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

    def get_total_character_count(self) -> int:
        """
        Calculates the aggregate character length across the extracted document.

        Returns:
            int: Total character count of extracted full-text or chunk passages.
        """
        if self.extracted_text:
            return len(self.extracted_text)
        return sum(len(c.content) for c in self.chunks)

    def has_processing_warnings(self) -> bool:
        """
        Predicate indicating whether extraction warnings were flagged during processing.

        Returns:
            bool: True if warnings list is non-empty, False otherwise.
        """
        return len(self.warnings) > 0


TERMINAL_INGESTION_STATUSES = {
    IngestionStatus.APPROVED,
    IngestionStatus.REJECTED,
    IngestionStatus.SUPERSEDED,
    IngestionStatus.FAILED,
    IngestionStatus.ARCHIVED,
}


def is_terminal_ingestion_status(status: IngestionStatus) -> bool:
    """
    Determines whether a document ingestion milestone is in a settled/terminal state.

    Args:
        status: Current IngestionStatus enum value.

    Returns:
        bool: True if document processing has finished (approved/rejected/archived), False if in-flight.
    """
    return status in TERMINAL_INGESTION_STATUSES


def get_active_ingestion_statuses() -> List[IngestionStatus]:
    """
    Returns an enumeration list of all active (non-terminal) document processing states.

    Returns:
        List[IngestionStatus]: Ingestion statuses that represent work in progress.
    """
    return [s for s in IngestionStatus if s not in TERMINAL_INGESTION_STATUSES]

