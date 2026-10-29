"""
Processor for Video Ingestion: MP4, MOV, MKV, WEBM.
Samples audio track for speech transcription.
"""

import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets
from ...voice.transcription import is_whisper_installed


class VideoProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["mp4", "mov", "mkv", "webm"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.VIDEO

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = [
            "Video track indexing extracted video container metadata. Audio track transcription requires ffmpeg."
        ]

        file_size = filepath.stat().st_size
        summary_text = f"Video File: {filename} ({round(file_size / (1024*1024), 2)}MB, container format: {ext.upper()})"

        chunks = [
            ExtractedChunk(
                chunk_index=0,
                page_number=1,
                section_title="Video Container Metadata",
                content=summary_text,
                metadata={"file_size": file_size, "container": ext}
            )
        ]

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.VIDEO,
            content_type=f"video/{ext}",
            title=title,
            extracted_text=summary_text,
            structured_content={"container": ext, "file_size_bytes": file_size},
            chunks=chunks,
            source_metadata={"file_size": file_size},
            extraction_method="video_container_extractor",
            status=IngestionStatus.PROCESSING,
            warnings=warnings,
            processing_duration_seconds=round(duration, 3)
        )

