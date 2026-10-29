"""
Processor for Structured Data: JSON and YAML.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from .text_processor import chunk_document_text
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class StructuredDataProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["json", "yaml", "yml"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.JSON

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        is_yaml = ext in ["yaml", "yml"]
        doc_type = DocumentType.YAML if is_yaml else DocumentType.JSON

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        parsed_data: Any = {}
        try:
            if is_yaml:
                if not YAML_AVAILABLE:
                    return ExtractedDocument(
                        filename=filename,
                        file_hash=file_hash,
                        detected_file_type=DocumentType.YAML,
                        content_type="application/x-yaml",
                        title=filename,
                        status=IngestionStatus.FAILED,
                        warnings=["PyYAML is not installed"],
                        processing_duration_seconds=round(time.time() - start_t, 3)
                    )
                parsed_data = yaml.safe_load(raw_text) or {}
            else:
                parsed_data = json.loads(raw_text)
        except Exception as e:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=doc_type,
                content_type="application/json" if not is_yaml else "application/x-yaml",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=[f"Malformed structured file syntax: {str(e)}"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        redacted_text, sec_w = redact_secrets(raw_text)
        warnings.extend(sec_w)

        # Create structured text representation for retrieval
        formatted_repr = json.dumps(parsed_data, indent=2, ensure_ascii=False) if isinstance(parsed_data, (dict, list)) else str(parsed_data)
        chunks = chunk_document_text(formatted_repr, page_number=1, default_section="Structured Data")
        for idx, ch in enumerate(chunks):
            ch.chunk_index = idx

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=doc_type,
            content_type="application/json" if not is_yaml else "application/x-yaml",
            title=title,
            extracted_text=redacted_text,
            structured_content={"data": parsed_data} if isinstance(parsed_data, dict) else {"items": parsed_data},
            chunks=chunks,
            source_metadata={"file_size": filepath.stat().st_size},
            extraction_method="structured_data_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

