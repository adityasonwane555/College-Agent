"""
BUDDY AI 2.0 — Base Document Processor Abstract Interface

Architecture & Extensibility Pattern:
  - Polymorphic Extractor Design:
      - Defines the abstract contract implemented by all format-specific document extractors (PDF, DOCX, CSV, PPTX, JSON, etc.).
  - Capability Introspection:
      - Exposes property flags for OCR prerequisites (requires_ocr), transcription requirements (requires_transcription),
        and on-device execution feasibility (can_extract_locally).
  - Canonical Envelope Generation:
      - Mandates that all extractors parse raw files on disk into standardized ExtractedDocument structures.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..common import ExtractedDocument, DocumentType


class BaseProcessor(ABC):
    """
    Abstract base class establishing the contract for all document parsing modules.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        List of lower-case file extensions without leading dots supported by this extractor (e.g. ['pdf', 'txt']).
        """
        pass

    @property
    @abstractmethod
    def document_type(self) -> DocumentType:
        """
        Standard DocumentType classification identifier mapped to this processor.
        """
        pass

    @property
    def requires_ocr(self) -> bool:
        """
        Whether this document format requires optical character recognition for scanned content.
        """
        return False

    @property
    def requires_transcription(self) -> bool:
        """
        Whether this processor requires audio speech-to-text transcription models.
        """
        return False

    @property
    def can_extract_locally(self) -> bool:
        """
        Whether this processor can execute entirely offline without calling external cloud APIs.
        """
        return True

    @abstractmethod
    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        """
        Extracts textual passages, logical sections, and structured metadata from the target file.

        Args:
            filepath: Path to the target document on disk.
            **kwargs: Additional runtime arguments passed from the processor registry.

        Returns:
            ExtractedDocument: Populated canonical document envelope.
        """
        pass

    def supports_extension(self, extension: str) -> bool:
        """
        Checks whether this processor explicitly supports the given file extension.

        Args:
            extension: Lowercase file extension with or without leading dot.

        Returns:
            bool: True if extension is in supported_extensions list, False otherwise.
        """
        clean_ext = extension.strip().lstrip(".").lower()
        return clean_ext in [e.lower() for e in self.supported_extensions]

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Summarizes the execution capabilities and requirements of this processor.

        Returns:
            Dict[str, Any]: Capability flags dictionary.
        """
        return {
            "supported_extensions": self.supported_extensions,
            "document_type": self.document_type.value,
            "requires_ocr": self.requires_ocr,
            "requires_transcription": self.requires_transcription,
            "can_extract_locally": self.can_extract_locally
        }


def clean_file_extension(filename: str) -> str:
    """
    Extracts and standardizes the lowercase file extension from a filename or path.

    Args:
        filename: Filename or path string.

    Returns:
        str: Normalized extension without leading dot (e.g. 'pdf', 'docx').
    """
    if not filename or not isinstance(filename, str):
        return ""
    clean = filename.strip().lower()
    if "." in clean:
        return clean.rsplit(".", 1)[-1].strip()
    return clean


