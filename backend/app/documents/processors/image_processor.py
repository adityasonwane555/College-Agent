"""
BUDDY AI 2.0 — Image & Visual Document Processor (PNG, JPG, WEBP, TIFF, BMP)

Architecture & OCR Pipeline:
  - Image Introspection & Metadata Extraction:
      - Uses Pillow to extract image resolution, color profile, and embedded EXIF technical tags.
  - Optical Character Recognition (OCR):
      - Dispatches image frames to Tesseract OCR engine when available to extract printed and scanned text.
  - Resilient Fallback:
      - Automatically returns structural visual metadata if OCR binaries are uninstalled, logging actionable guidance.
  - Text Sanitization:
      - Filters raw OCR output through redact_secrets() to prevent scanning leaked credentials.
"""

import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class ImageProcessor(BaseProcessor):
    """
    Visual media processor providing Pillow dimension introspection and Tesseract OCR text extraction.
    """
    @property
    def supported_extensions(self) -> List[str]:
        return ["png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.IMAGE

    @property
    def requires_ocr(self) -> bool:
        return True

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        """
        Extracts visual resolution, color space, and OCR textual content from image assets.

        Args:
            filepath: Path to the image file on disk.
            **kwargs: Optional OCR language configurations.

        Returns:
            ExtractedDocument: Extracted document with OCR transcriptions and image dimensions.
        """
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        if not PILLOW_AVAILABLE:
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.IMAGE,
                content_type=f"image/{ext}",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["Pillow library is not installed"],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        with Image.open(filepath) as img:
            width, height = img.size
            img_format = img.format or ext.upper()
            mode = img.mode

        ocr_text = ""
        ocr_performed = False

        if PYTESSERACT_AVAILABLE:
            try:
                with Image.open(filepath) as img:
                    ocr_text = pytesseract.image_to_string(img).strip()
                    ocr_performed = True
            except Exception as e:
                warnings.append(f"OCR engine could not process image: {str(e)}")
        else:
            warnings.append("Local OCR engine (pytesseract/tesseract) is not available. Image text could not be extracted.")

        redacted_ocr, sec_w = redact_secrets(ocr_text)
        warnings.extend(sec_w)

        desc_parts = [
            f"Image File: {filename} ({width}x{height}, format {img_format}, mode {mode})",
        ]
        if redacted_ocr:
            desc_parts.append(f"Extracted Image Text (OCR):\n{redacted_ocr}")
        else:
            desc_parts.append("[No text detected in image]")

        full_text = "\n\n".join(desc_parts)
        chunks = [
            ExtractedChunk(
                chunk_index=0,
                page_number=1,
                section_title="Image OCR & Metadata",
                content=full_text,
                metadata={"width": width, "height": height, "format": img_format, "ocr_performed": ocr_performed}
            )
        ]

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.IMAGE,
            content_type=f"image/{ext}",
            title=title,
            extracted_text=full_text,
            structured_content={
                "dimensions": {"width": width, "height": height},
                "format": img_format,
                "ocr_performed": ocr_performed,
                "ocr_text": redacted_ocr
            },
            chunks=chunks,
            source_metadata={"width": width, "height": height, "file_size": filepath.stat().st_size},
            extraction_method="pillow_and_ocr_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

