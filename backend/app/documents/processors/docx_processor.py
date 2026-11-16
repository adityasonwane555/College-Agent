"""
BUDDY AI 2.0 — Microsoft Word (.docx) Document Processor

Architecture & Document Extraction:
  - Library Integration:
      - Uses python-docx to parse OpenXML Word processing packages without requiring Microsoft Office installed.
  - Multi-Element Extraction:
      - Traverses body paragraphs, discarding empty lines.
      - Iterates through embedded tables, flattening cell values into pipe-separated (`|`) row representations
        to preserve relational schema for tabular inquiries (e.g. fee tables, exam schedules).
  - Security Sanitization:
      - Masks detected API keys, tokens, and credentials via redact_secrets().
      - Evaluates document content against adversarial prompt injection attacks via check_prompt_injection().
"""

import time
from pathlib import Path
from typing import List
from .base import BaseProcessor
from .text_processor import chunk_document_text
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocxProcessor(BaseProcessor):
    """
    Document processor specialized for Microsoft Word (.docx) OpenXML documents.
    """

    @property
    def supported_extensions(self) -> List[str]:
        """List of lower-case file extensions supported by this extractor."""
        return ["docx"]

    @property
    def document_type(self) -> DocumentType:
        """Standard DocumentType classification."""
        return DocumentType.DOCX

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        """
        Extracts paragraphs and linearized tables from a Word document with security scanning.

        Args:
            filepath: Path to the target DOCX file on disk.
            **kwargs: Additional runtime extraction options.

        Returns:
            ExtractedDocument: Populated document envelope containing body paragraphs and table chunks.
        """
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        warnings: List[str] = []

        if not DOCX_AVAILABLE:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.DOCX,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["python-docx library is not installed"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        doc = docx.Document(str(filepath))
        paragraphs = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs.append(text)

        # Also extract table text
        table_texts = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_texts.append(" | ".join(row_cells))

        full_raw = "\n".join(paragraphs)
        if table_texts:
            full_raw += "\n\nTables:\n" + "\n".join(table_texts)

        redacted_text, sec_w = redact_secrets(full_raw)
        warnings.extend(sec_w)

        has_inj, inj_msg = check_prompt_injection(redacted_text)
        if has_inj and inj_msg:
            warnings.append(inj_msg)

        chunks = chunk_document_text(redacted_text, page_number=1, default_section="Document Body")
        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.DOCX,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            title=title,
            extracted_text=redacted_text,
            chunks=chunks,
            source_metadata={"paragraph_count": len(paragraphs), "table_count": len(doc.tables)},
            extraction_method="docx_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )
