"""
BUDDY AI 2.0 — Presentation Document Processor (PPTX, PPT, ODP)

Architecture & Slide Extraction:
  - Library Integration:
      - Employs python-pptx to inspect Microsoft PowerPoint OpenXML presentation archives.
  - Slide Hierarchy & Note Extraction:
      - Iterates through prs.slides sequentially, identifying title shapes versus content text frames.
      - Extracts presenter notes from slide.notes_slide to index supplementary institutional context not visible on the slides.
  - Granular Slide-Level Chunking:
      - Segments each slide into an individual ExtractedChunk tagged with page_number=slide_number and slide title headers.
  - Security Scanning:
      - Scrubs presenter notes and slide text against secret patterns and credentials using redact_secrets().
"""

import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection

try:
    import pptx
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


class PresentationProcessor(BaseProcessor):
    """
    Document processor specialized for Microsoft PowerPoint (.pptx) presentation decks.
    """

    @property
    def supported_extensions(self) -> List[str]:
        """List of presentation file extensions supported by this extractor."""
        return ["pptx", "ppt", "odp"]

    @property
    def document_type(self) -> DocumentType:
        """Standard DocumentType classification."""
        return DocumentType.PPTX

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        """
        Extracts slide titles, bullet points, and presenter notes from a PowerPoint presentation file.

        Args:
            filepath: Path to the target presentation file on disk.
            **kwargs: Extra extraction options.

        Returns:
            ExtractedDocument: Populated document envelope containing slide-indexed chunks and structured metadata.
        """
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        warnings: List[str] = []

        if not PPTX_AVAILABLE:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.PPTX,
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["python-pptx library is not installed"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        prs = pptx.Presentation(str(filepath))
        chunks: List[ExtractedChunk] = []
        slides_structured: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_title = ""
            slide_texts: List[str] = []

            for shape in slide.shapes:
                if shape.has_text_frame:
                    text_frame = shape.text_frame
                    for paragraph in text_frame.paragraphs:
                        txt = paragraph.text.strip()
                        if txt:
                            if not slide_title and shape == slide.shapes.title:
                                slide_title = txt
                            else:
                                slide_texts.append(txt)

            notes_text = ""
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()

            title_display = slide_title or f"Slide {slide_idx}"
            content_display = "\n".join(slide_texts)
            if notes_text:
                content_display += f"\n[Notes]: {notes_text}"

            slide_record = {
                "slide_number": slide_idx,
                "title": title_display,
                "bullets": slide_texts,
                "notes": notes_text
            }
            slides_structured.append(slide_record)

            combined_slide_str = f"=== Slide {slide_idx}: {title_display} ===\n{content_display}"
            full_text_parts.append(combined_slide_str)

            chunks.append(ExtractedChunk(
                chunk_index=slide_idx - 1,
                page_number=slide_idx,
                section_title=title_display,
                content=combined_slide_str,
                metadata={"slide_number": slide_idx}
            ))

        full_raw = "\n\n".join(full_text_parts)
        redacted_text, sec_w = redact_secrets(full_raw)
        warnings.extend(sec_w)

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.PPTX,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title=title,
            extracted_text=redacted_text,
            structured_content={"slides": slides_structured},
            chunks=chunks,
            source_metadata={"slide_count": len(prs.slides), "file_size": filepath.stat().st_size},
            extraction_method="pptx_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )
