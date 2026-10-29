"""
BUDDY AI 2.0 — Modular Document Processor Registry
Dispatches files to format-specific extractors with clear status for unsupported formats.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseProcessor
from .text_processor import TextProcessor
from .pdf_processor import PdfProcessor
from .docx_processor import DocxProcessor
from .spreadsheet_processor import SpreadsheetProcessor
from .presentation_processor import PresentationProcessor
from .structured_processor import StructuredDataProcessor
from .web_processor import WebMarkupProcessor
from .code_processor import CodeProcessor
from .archive_processor import ArchiveProcessor
from .image_processor import ImageProcessor
from .audio_processor import AudioProcessor
from .video_processor import VideoProcessor
from ..common import ExtractedDocument, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, sanitize_filename


class ProcessorRegistry:
    def __init__(self):
        self._processors: List[BaseProcessor] = []
        self._extension_map: Dict[str, BaseProcessor] = {}
        self._register_default_processors()

    def register(self, processor: BaseProcessor):
        self._processors.append(processor)
        for ext in processor.supported_extensions:
            self._extension_map[ext.lower().strip()] = processor

    def _register_default_processors(self):
        self.register(TextProcessor())
        self.register(PdfProcessor())
        self.register(DocxProcessor())
        self.register(SpreadsheetProcessor())
        self.register(PresentationProcessor())
        self.register(StructuredDataProcessor())
        self.register(WebMarkupProcessor())
        self.register(CodeProcessor())
        self.register(ArchiveProcessor())
        self.register(ImageProcessor())
        self.register(AudioProcessor())
        self.register(VideoProcessor())

    def get_processor(self, filepath_or_ext: str | Path) -> Optional[BaseProcessor]:
        ext = filepath_or_ext.suffix.lower().lstrip(".") if isinstance(filepath_or_ext, Path) else filepath_or_ext.lower().lstrip(".")
        return self._extension_map.get(ext)

    def is_supported(self, filepath_or_ext: str | Path) -> bool:
        return self.get_processor(filepath_or_ext) is not None

    def list_supported_extensions(self) -> List[str]:
        return sorted(list(self._extension_map.keys()))

    def process_file(self, filepath: Path) -> ExtractedDocument:
        """Processes any file using the suitable format extractor or returns clear unsupported status."""
        ext = filepath.suffix.lower().lstrip(".")
        processor = self.get_processor(ext)
        file_hash = calculate_file_hash(filepath)
        filename = sanitize_filename(filepath.name)

        if not processor:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.UNKNOWN,
                content_type="application/octet-stream",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=[
                    f"Unsupported file format '.{ext}'. Supported formats are: {', '.join(self.list_supported_extensions()[:15])}..."
                ],
                processing_duration_seconds=0.0
            )

        try:
            return processor.extract(filepath)
        except Exception as e:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=processor.document_type,
                content_type="application/octet-stream",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=[f"Extractor {processor.__class__.__name__} failed: {str(e)}"],
                processing_duration_seconds=0.0
            )


processor_registry = ProcessorRegistry()

