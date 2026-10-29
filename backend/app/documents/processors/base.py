"""
Base Processor Interface for Universal Ingestion
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..common import ExtractedDocument, DocumentType


class BaseProcessor(ABC):
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of lower-case file extensions without dot, e.g. ['pdf', 'txt']."""
        pass

    @property
    @abstractmethod
    def document_type(self) -> DocumentType:
        """Standard document type classification."""
        pass

    @property
    def requires_ocr(self) -> bool:
        return False

    @property
    def requires_transcription(self) -> bool:
        return False

    @property
    def can_extract_locally(self) -> bool:
        return True

    @abstractmethod
    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        """Extracts content, sections, and metadata from the given file."""
        pass

