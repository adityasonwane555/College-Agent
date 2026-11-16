"""
BUDDY AI 2.0 — Modular Document Processor Registry

Architecture & Dispatch Engine:
  - Extensible Registry Pattern:
      - Maintains an active catalog of 12 format-specific document processors (Text, PDF, DOCX, Spreadsheets,
        Presentations, Structured Data, Web Markup, Code, Archives, Images, Audio, Video).
  - Fast Extension Lookup:
      - Maps lowercase file extensions to processor instances for O(1) resolution during upload.
  - Graceful Fallback & Unsupported Format Handling:
      - Yields a structured ExtractedDocument with IngestionStatus.FAILED and actionable diagnostic warnings
        rather than raising unhandled exceptions on unsupported file types.
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
    """
    Central dispatch registry that routes document files to their respective format processors.
    """

    def __init__(self):
        """
        Initializes the registry and registers default extractors for all supported document types.
        """
        self._processors: List[BaseProcessor] = []
        self._extension_map: Dict[str, BaseProcessor] = {}
        self._register_default_processors()

    def register(self, processor: BaseProcessor):
        """
        Registers an extractor instance and populates extension mappings for all supported formats.

        Args:
            processor: BaseProcessor instance to register.
        """
        self._processors.append(processor)
        for ext in processor.supported_extensions:
            self._extension_map[ext.lower().strip()] = processor

    def _register_default_processors(self):
        """Initializes and registers standard processors for PDF, Office, Text, Web, and Media formats."""
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
        """
        Resolves the appropriate BaseProcessor instance for a given file path or extension string.

        Args:
            filepath_or_ext: File path or raw extension string (e.g. 'pdf' or Path('doc.docx')).

        Returns:
            Optional[BaseProcessor]: Matching processor instance, or None if format is unsupported.
        """
        ext = filepath_or_ext.suffix.lower().lstrip(".") if isinstance(filepath_or_ext, Path) else filepath_or_ext.lower().lstrip(".")
        return self._extension_map.get(ext)

    def is_supported(self, filepath_or_ext: str | Path) -> bool:
        """
        Checks whether an extractor exists for the given file path or extension.

        Args:
            filepath_or_ext: Target file path or extension.

        Returns:
            bool: True if supported, False otherwise.
        """
        return self.get_processor(filepath_or_ext) is not None

    def list_supported_extensions(self) -> List[str]:
        """
        Returns a sorted list of all file extensions supported by currently registered processors.

        Returns:
            List[str]: Sorted list of lowercase file extensions.
        """
        return sorted(list(self._extension_map.keys()))

    def process_file(self, filepath: Path) -> ExtractedDocument:
        """
        Processes any file on disk using the appropriate format extractor with error containment.

        Args:
            filepath: Path to the target document.

        Returns:
            ExtractedDocument: Extracted document envelope, marked FAILED with diagnostic warnings if unsupported.
        """
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
