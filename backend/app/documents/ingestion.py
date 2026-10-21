import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from ..database.repository import repo
from ..database.models import DocumentMetadataModel

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


def ingest_text_file(filepath: Path) -> Tuple[DocumentMetadataModel, List[Dict[str, Any]]]:
    """Ingests a text file, parsing optional page markers like '=== PAGE X ==='."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    filename = filepath.name
    title = filename.replace("_", " ").rsplit(".", 1)[0]
    
    # Check for page markers
    page_splits = re.split(r"===\s*PAGE\s*(\d+)\s*===", content, flags=re.IGNORECASE)
    chunks: List[Dict[str, Any]] = []

    if len(page_splits) > 1:
        # Formatted pages: ['', '1', 'page 1 content', '2', 'page 2 content'...]
        total_pages = 0
        for i in range(1, len(page_splits), 2):
            page_num = int(page_splits[i])
            page_content = page_splits[i+1]
            total_pages = max(total_pages, page_num)
            page_chunks = chunk_text(page_content, page_number=page_num, doc_name=filename)
            chunks.extend(page_chunks)
    else:
        # Single page / natural paragraph chunking
        total_pages = 1
        chunks = chunk_text(content, page_number=1, doc_name=filename)

    meta = DocumentMetadataModel(
        filename=filename,
        title=title,
        total_pages=max(1, total_pages),
        uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chunk_count=len(chunks)
    )

    repo.save_document(meta, chunks)
    return meta, chunks


def ingest_pdf_file(filepath: Path) -> Tuple[DocumentMetadataModel, List[Dict[str, Any]]]:
    """Ingests a PDF file page by page using pypdf."""
    if not PYPDF_AVAILABLE:
        raise RuntimeError("pypdf is not installed. PDF ingestion is disabled.")

    reader = PdfReader(str(filepath))
    total_pages = len(reader.pages)
    filename = filepath.name
    title = filename.replace("_", " ").rsplit(".", 1)[0]
    chunks: List[Dict[str, Any]] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        page_text = page.extract_text() or ""
        if page_text.strip():
            page_chunks = chunk_text(page_text, page_number=page_num, doc_name=filename)
            chunks.extend(page_chunks)

    meta = DocumentMetadataModel(
        filename=filename,
        title=title,
        total_pages=total_pages,
        uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        chunk_count=len(chunks)
    )

    repo.save_document(meta, chunks)
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
