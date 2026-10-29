"""
Processor for PDF documents using pypdf.
"""

import time
from pathlib import Path
from typing import List
from .base import BaseProcessor
from .text_processor import chunk_document_text
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class PdfProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["pdf"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.PDF

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        warnings: List[str] = []

        if not PYPDF_AVAILABLE:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.PDF,
                content_type="application/pdf",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["pypdf library is not installed"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        reader = PdfReader(str(filepath))
        total_pages = len(reader.pages)
        full_text_parts = []
        chunks: List[ExtractedChunk] = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page.extract_text() or ""
            redacted_page_text, sec_w = redact_secrets(raw_text)
            warnings.extend(sec_w)
            
            has_inj, inj_msg = check_prompt_injection(redacted_page_text)
            if has_inj and inj_msg:
                warnings.append(f"Page {page_num}: {inj_msg}")

            if redacted_page_text.strip():
                full_text_parts.append(f"--- Page {page_num} ---\n" + redacted_page_text)
                page_chunks = chunk_document_text(redacted_page_text, page_number=page_num, default_section=f"Page {page_num}")
                chunks.extend(page_chunks)

        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]
        extracted_text = "\n\n".join(full_text_parts)

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.PDF,
            content_type="application/pdf",
            title=title,
            extracted_text=extracted_text,
            chunks=chunks,
            source_metadata={"total_pages": total_pages, "file_size": filepath.stat().st_size},
            extraction_method="pdf_pypdf_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

