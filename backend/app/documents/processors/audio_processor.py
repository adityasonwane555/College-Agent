"""
Processor for Audio Ingestion: WAV, MP3, M4A, FLAC, OGG.
Transcribes speech using faster-whisper pipeline.
"""

import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import calculate_file_hash, redact_secrets
from ...voice.transcription import transcribe_audio_file, is_whisper_installed


class AudioProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["wav", "mp3", "m4a", "flac", "ogg"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.AUDIO

    @property
    def requires_transcription(self) -> bool:
        return True

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        if not is_whisper_installed():
            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.AUDIO,
                content_type=f"audio/{ext}",
                title=filename,
                status=IngestionStatus.FAILED,
                warnings=["Speech transcription engine (faster-whisper) is not available."],
                processing_duration_seconds=round(time.time() - start_t, 3)
            )

        transcription_res = transcribe_audio_file(filepath)
        transcribed_text = transcription_res.get("text", "").strip()

        redacted_transcript, sec_w = redact_secrets(transcribed_text)
        warnings.extend(sec_w)

        summary_lines = [
            f"Audio Recording: {filename}",
            f"Transcript:\n{redacted_transcript if redacted_transcript else '[No speech detected in audio file]'}"
        ]
        full_text = "\n\n".join(summary_lines)

        chunks = [
            ExtractedChunk(
                chunk_index=0,
                page_number=1,
                section_title="Audio Transcription",
                content=full_text,
                metadata={"transcription_detected": bool(redacted_transcript)}
            )
        ]

        duration = time.time() - start_t
        title = filename.replace("_", " ").rsplit(".", 1)[0]

        return ExtractedDocument(
            filename=filename,
            file_hash=file_hash,
            detected_file_type=DocumentType.AUDIO,
            content_type=f"audio/{ext}",
            title=title,
            extracted_text=full_text,
            structured_content={"transcript": redacted_transcript},
            chunks=chunks,
            source_metadata={"file_size": filepath.stat().st_size},
            extraction_method="whisper_audio_transcriber",
            status=IngestionStatus.PROCESSING,
            warnings=list(set(warnings)),
            processing_duration_seconds=round(duration, 3)
        )

