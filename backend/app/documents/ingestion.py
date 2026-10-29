"""
BUDDY AI 2.0 — Universal Ingestion Entry Point
Maintains backwards compatibility for ingest_text_file and ingest_pdf_file
while connecting to the modular universal processor registry and lifecycle manager.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from ..database.repository import repo
from ..database.models import DocumentMetadataModel
from .processors.registry import processor_registry
from .lifecycle import lifecycle_manager

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def chunk_text(text: str, page_number: int = 1, doc_name: str = "") -> List[Dict[str, Any]]:
    """Chunks text into section-aware passages with page numbers."""
    chunks = []
    lines = text.split("\n")
    current_section = "General"
    buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("SECTION:"):
            if buffer:
                content = " ".join(buffer).strip()
                if len(content) > 30:
                    chunks.append({
                        "page_number": page_number,
                        "section_title": current_section,
                        "content": content
                    })
                buffer = []
            current_section = stripped.replace("SECTION:", "").strip()
        elif stripped:
            buffer.append(stripped)

    if buffer:
        content = " ".join(buffer).strip()
        if len(content) > 20:
            chunks.append({
                "page_number": page_number,
                "section_title": current_section,
                "content": content
            })

    return chunks


def ingest_universal_file(filepath: Path, auto_approve: bool = False, actor: str = "admin") -> Dict[str, Any]:
    """Universal ingestion entry point for any supported document format."""
    return lifecycle_manager.process_and_ingest(filepath, auto_approve=auto_approve, actor=actor)


def ingest_text_file(filepath: Path) -> Tuple[DocumentMetadataModel, List[Dict[str, Any]]]:
    """Ingests a text file and returns metadata and chunks (preserves existing API contract)."""
    res = lifecycle_manager.process_and_ingest(filepath, auto_approve=True)
    doc_id = res.get("document_id")
    raw_doc = repo.get_document_by_id(doc_id) if doc_id else repo.get_document_by_name(filepath.name)

    chunks = []
    if raw_doc:
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT page_number, section_title, content FROM document_chunks WHERE document_name = ?", (filepath.name,))
            chunks = [dict(r) for r in cursor.fetchall()]

    meta = DocumentMetadataModel(
        id=doc_id,
        filename=filepath.name,
        title=filepath.name.replace("_", " ").rsplit(".", 1)[0],
        total_pages=raw_doc["total_pages"] if raw_doc else 1,
        uploaded_at=raw_doc["uploaded_at"] if raw_doc else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chunk_count=len(chunks),
        file_hash=res.get("file_hash", ""),
        status="approved"
    )
    return meta, chunks


def ingest_pdf_file(filepath: Path) -> Tuple[DocumentMetadataModel, List[Dict[str, Any]]]:
    """Ingests a PDF file and returns metadata and chunks (preserves existing API contract)."""
    res = lifecycle_manager.process_and_ingest(filepath, auto_approve=True)
    doc_id = res.get("document_id")
    raw_doc = repo.get_document_by_id(doc_id) if doc_id else repo.get_document_by_name(filepath.name)

    chunks = []
    if raw_doc:
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT page_number, section_title, content FROM document_chunks WHERE document_name = ?", (filepath.name,))
            chunks = [dict(r) for r in cursor.fetchall()]

    meta = DocumentMetadataModel(
        id=doc_id,
        filename=filepath.name,
        title=filepath.name.replace("_", " ").rsplit(".", 1)[0],
        total_pages=raw_doc["total_pages"] if raw_doc else 1,
        uploaded_at=raw_doc["uploaded_at"] if raw_doc else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chunk_count=len(chunks),
        file_hash=res.get("file_hash", ""),
        status="approved"
    )
    return meta, chunks


def ingest_sample_documents(samples_dir: Path):
    """Automatically ingests all sample documents if present."""
    if not samples_dir.exists():
        return
    for file in samples_dir.glob("*.txt"):
        try:
            ingest_text_file(file)
        except Exception as e:
            print(f"Error ingesting sample doc {file.name}: {e}")
