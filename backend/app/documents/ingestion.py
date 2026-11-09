"""
BUDDY AI 2.0 — Universal Document Ingestion & Chunking Subsystem

Architecture & Ingestion Pipeline:
  - Unified File Ingestion Gateway:
      - Routes heterogeneous file uploads (PDF, DOCX, TXT, CSV, HTML, Audio, Images) through
        the modular `processor_registry` and `lifecycle_manager`.
      - Maintains backwards-compatible contracts for `ingest_text_file` and `ingest_pdf_file`.
  - Section-Aware Semantic Chunking:
      - `chunk_text` intelligently partitions raw text streams around explicit `SECTION:` headings,
        preserving logical context boundaries and page numbers without fragmenting sentences.
  - Lifecycle Integration:
      - Generates cryptographic SHA-256 file hashes to detect content modifications.
      - Indexes chunks into both SQLite FTS5 for BM25 keyword matching and ChromaDB for vector retrieval.
      - Manages administrative approval workflows and audit version increments.
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
    """
    Partitions raw text into logical section-aware chunks for search indexing.
    Respects explicit `SECTION:` delimiters and preserves page numbering.

    Args:
        text: Raw document text string.
        page_number: Source page index (default: 1).
        doc_name: Filename of the source document.

    Returns:
        List[Dict[str, Any]]: List of chunk dictionaries containing 'page_number',
                              'section_title', and 'content'.
    """
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
    """
    Universal ingestion entry point dispatching files to the appropriate processor.

    Args:
        filepath: Filesystem path to the input document.
        auto_approve: Whether to bypass human review and immediately approve the document.
        actor: Identity of the user or system initiating the ingestion.

    Returns:
        Dict[str, Any]: Ingestion status summary including document ID, file hash, and chunks created.
    """
    return lifecycle_manager.process_and_ingest(filepath, auto_approve=auto_approve, actor=actor)


def ingest_text_file(filepath: Path) -> Tuple[DocumentMetadataModel, List[Dict[str, Any]]]:
    """
    Ingests a plain text file, generating metadata, section chunks, and search index entries.

    Args:
        filepath: Filesystem path to the text file.

    Returns:
        Tuple[DocumentMetadataModel, List[Dict[str, Any]]]: Document metadata model and list of chunk records.
    """
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
    """
    Ingests a PDF document, extracting page text, section headers, and search index entries.

    Args:
        filepath: Filesystem path to the PDF document.

    Returns:
        Tuple[DocumentMetadataModel, List[Dict[str, Any]]]: Document metadata model and list of chunk records.
    """
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
    """
    Automatically scans and ingests all sample college documents (.txt) located in the target directory.
    Executed during backend startup to guarantee out-of-the-box knowledge readiness.

    Args:
        samples_dir: Filesystem directory containing sample documentation.
    """
    if not samples_dir.exists():
        return
    for file in samples_dir.glob("*.txt"):
        try:
            ingest_text_file(file)
        except Exception as e:
            print(f"Error ingesting sample doc {file.name}: {e}")
