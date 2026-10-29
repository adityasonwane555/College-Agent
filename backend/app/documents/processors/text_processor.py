"""
Processor for Plain Text, Markdown, and RTF documents.
"""

import time
import re
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection


def chunk_document_text(text: str, page_number: int = 1, default_section: str = "General") -> List[ExtractedChunk]:
    """Splits text into section-aware chunks."""
    chunks: List[ExtractedChunk] = []
    lines = text.split("\n")
    current_section = default_section
    buffer: List[str] = []
    chunk_idx = 0

    def flush_buffer():
        nonlocal buffer, chunk_idx, current_section
        if buffer:
            content = " ".join(buffer).strip()
            if len(content) > 10:
                chunks.append(ExtractedChunk(
                    chunk_index=chunk_idx,
                    page_number=page_number,
                    section_title=current_section,
                    content=content
                ))
                chunk_idx += 1
            buffer = []

    for line in lines:
        stripped = line.strip()
        # Header / Section indicator
        if stripped.startswith("SECTION:") or stripped.startswith("# ") or stripped.startswith("## "):
            flush_buffer()
            current_section = re.sub(r'^(SECTION:|\#{1,3})\s*', '', stripped).strip() or "General"
        elif stripped:
            buffer.append(stripped)
            if len(buffer) >= 8 and len(" ".join(buffer)) >= 500:
                flush_buffer()

    flush_buffer()
    return chunks


class TextProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["txt", "md", "markdown", "rtf", "log"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.TXT

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        doc_type = DocumentType.MARKDOWN if ext in ["md", "markdown"] else DocumentType.TXT

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        redacted_text, sec_warnings = redact_secrets(raw_content)
        warnings = list(sec_warnings)

        has_inj, inj_msg = check_prompt_injection(redacted_text)
        if has_inj and inj_msg:
            warnings.append(inj_msg)

        # Parse page splits if present
        page_splits = re.split(r"===\s*PAGE\s*(\d+)\s*===", redacted_text, flags=re.IGNORECASE)
        chunks: List[ExtractedChunk] = []
        total_pages = 1

        if len(page_splits) > 1:
            for i in range(1, len(page_splits), 2):
                page_num = int(page_splits[i])
                page_content = page_splits[i+1]
                total_pages = max(total_pages, page_num)
                page_chunks = chunk_document_text(page_content, page_number=page_num)
                chunks.extend(page_chunks)
        else:
            chunks = chunk_document_text(redacted_text, page_number=1)

        # Re-index chunks sequentially
        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=doc_type,
            content_type="text/plain" if doc_type == DocumentType.TXT else "text/markdown",
            title=title,
            extracted_text=redacted_text,
            chunks=chunks,
            source_metadata={"total_pages": total_pages, "file_size": filepath.stat().st_size},
            extraction_method="text_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=warnings,
            processing_duration_seconds=round(duration, 3)
        )
