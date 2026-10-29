"""
Processor for Web Markup documents: HTML, HTM, and XML.
Extracts headings, paragraphs, and tables using BeautifulSoup.
"""

import time
from pathlib import Path
from typing import List
from .base import BaseProcessor
from .text_processor import chunk_document_text
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets, check_prompt_injection

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebMarkupProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["html", "htm", "xml"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.HTML

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        is_xml = ext == "xml"
        doc_type = DocumentType.XML if is_xml else DocumentType.HTML

        if not BS4_AVAILABLE:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=doc_type,
                content_type="text/html" if not is_xml else "application/xml",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["beautifulsoup4 library is not installed"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        parser = "xml" if is_xml else "html.parser"
        soup = BeautifulSoup(raw_content, parser)

        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.extract()

        title_elem = soup.find("title")
        extracted_title = title_elem.get_text().strip() if title_elem else filename.replace("_", " ").rsplit(".", 1)[0]

        # Extract text content
        text_lines = []
        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr"]):
            t = elem.get_text().strip()
            if t:
                if elem.name in ["h1", "h2", "h3", "h4"]:
                    text_lines.append(f"SECTION: {t}")
                else:
                    text_lines.append(t)

        clean_text = "\n".join(text_lines) if text_lines else soup.get_text(separator="\n").strip()

        redacted_text, sec_w = redact_secrets(clean_text)
        warnings.extend(sec_w)

        has_inj, inj_msg = check_prompt_injection(redacted_text)
        if has_inj and inj_msg:
            warnings.append(inj_msg)

        chunks = chunk_document_text(redacted_text, page_number=1, default_section="Web Page Body")
        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=doc_type,
            content_type="text/html" if not is_xml else "application/xml",
            title=extracted_title,
            extracted_text=redacted_text,
            chunks=chunks,
            source_metadata={"file_size": filepath.stat().st_size},
            extraction_method="beautifulsoup_markup_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

