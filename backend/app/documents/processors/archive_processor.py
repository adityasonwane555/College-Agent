"""
Processor for Archive Inspection: .zip, .tar, .gz.
Protects against zip bombs, path traversal, and malicious links.
Extracts contained files safely and ingests them.
"""

import os
import tarfile
import zipfile
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseProcessor
from ..common import ExtractedDocument, ExtractedChunk, DocumentType, IngestionStatus
from ...security.file_validation import (
    calculate_file_hash,
    is_safe_archive_path,
    MAX_ARCHIVE_EXPAND_BYTES,
    MAX_ARCHIVE_FILE_COUNT
)


class ArchiveProcessor(BaseProcessor):
    @property
    def supported_extensions(self) -> List[str]:
        return ["zip", "tar", "gz"]

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.ARCHIVE

    def extract(self, filepath: Path, **kwargs) -> ExtractedDocument:
        start_t = time.time()
        file_hash = calculate_file_hash(filepath)
        filename = filepath.name
        ext = filepath.suffix.lower().lstrip(".")
        warnings: List[str] = []

        # Temporary extraction workspace
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            extracted_files: List[Dict[str, Any]] = []
            total_expanded_bytes = 0
            chunks: List[ExtractedChunk] = []
            chunk_idx = 0

            try:
                if ext == "zip":
                    with zipfile.ZipFile(filepath, "r") as zf:
                        infolist = zf.infolist()
                        if len(infolist) > MAX_ARCHIVE_FILE_COUNT:
                            return ExtractedDocument(
                                filename=filename,
                                file_hash=file_hash,
                                detected_file_type=DocumentType.ARCHIVE,
                                content_type="application/zip",
                                title=filename,
                                status=IngestionStatus.FAILED,
                                warnings=[f"Archive contains {len(infolist)} files (maximum allowed is {MAX_ARCHIVE_FILE_COUNT})"],
                                processing_duration_seconds=round(time.time() - start_t, 3)
                            )

                        for info in infolist:
                            # Zip bomb check
                            total_expanded_bytes += info.file_size
                            if total_expanded_bytes > MAX_ARCHIVE_EXPAND_BYTES:
                                return ExtractedDocument(
                                    filename=filename,
                                    file_hash=file_hash,
                                    detected_file_type=DocumentType.ARCHIVE,
                                    content_type="application/zip",
                                    title=filename,
                                    status=IngestionStatus.FAILED,
                                    warnings=[f"Decompressed archive size exceeds safety limit of {MAX_ARCHIVE_EXPAND_BYTES // (1024*1024)}MB"],
                                    processing_duration_seconds=round(time.time() - start_t, 3)
                                )

                            # Path traversal / directory escape check
                            target_file = tmp_dir / info.filename
                            if not is_safe_archive_path(tmp_dir, target_file):
                                warnings.append(f"Skipped unsafe path traversal in archive: {info.filename}")
                                continue

                            if info.is_dir():
                                continue

                            zf.extract(info, tmp_dir)
                            extracted_files.append({"name": info.filename, "size": info.file_size})

                elif ext in ["tar", "gz"]:
                    mode = "r:gz" if ext == "gz" or filename.endswith(".tar.gz") else "r:"
                    with tarfile.open(filepath, mode) as tf:
                        members = tf.getmembers()
                        if len(members) > MAX_ARCHIVE_FILE_COUNT:
                            return ExtractedDocument(
                                filename=filename,
                                file_hash=file_hash,
                                detected_file_type=DocumentType.ARCHIVE,
                                content_type="application/x-tar",
                                title=filename,
                                status=IngestionStatus.FAILED,
                                warnings=[f"Tar contains {len(members)} entries (limit {MAX_ARCHIVE_FILE_COUNT})"],
                                processing_duration_seconds=round(time.time() - start_t, 3)
                            )

                        for m in members:
                            total_expanded_bytes += m.size
                            if total_expanded_bytes > MAX_ARCHIVE_EXPAND_BYTES:
                                return ExtractedDocument(
                                    filename=filename,
                                    file_hash=file_hash,
                                    detected_file_type=DocumentType.ARCHIVE,
                                    content_type="application/x-tar",
                                    title=filename,
                                    status=IngestionStatus.FAILED,
                                    warnings=["Decompressed archive size exceeds limit"],
                                    processing_duration_seconds=round(time.time() - start_t, 3)
                                )

                            target_file = tmp_dir / m.name
                            if not is_safe_archive_path(tmp_dir, target_file):
                                warnings.append(f"Skipped unsafe archive path: {m.name}")
                                continue

                            if m.isfile():
                                tf.extract(m, tmp_dir)
                                extracted_files.append({"name": m.name, "size": m.size})

            except Exception as e:
                return ExtractedDocument(
                    filename=filename,
                    file_hash=file_hash,
                    detected_file_type=DocumentType.ARCHIVE,
                    content_type="application/octet-stream",
                    title=filename,
                    status=IngestionStatus.FAILED,
                    warnings=[f"Archive extraction failed: {str(e)}"],
                    processing_duration_seconds=round(time.time() - start_t, 3)
                )

            # Summarize contents for search chunking
            summary_lines = [
                f"Archive: {filename}",
                f"Contained Files ({len(extracted_files)} files, {round(total_expanded_bytes / 1024, 1)} KB total):"
            ]
            for ef in extracted_files:
                summary_lines.append(f"- {ef['name']} ({ef['size']} bytes)")

            summary_text = "\n".join(summary_lines)
            chunks.append(ExtractedChunk(
                chunk_index=0,
                page_number=1,
                section_title="Archive Manifest",
                content=summary_text,
                metadata={"file_count": len(extracted_files), "total_bytes": total_expanded_bytes}
            ))

            duration = time.time() - start_t
            title = filename.replace("_", " ").rsplit(".", 1)[0]

            return ExtractedDocument(
                filename=filename,
                file_hash=file_hash,
                detected_file_type=DocumentType.ARCHIVE,
                content_type="application/zip" if ext == "zip" else "application/x-tar",
                title=title,
                extracted_text=summary_text,
                structured_content={"files": extracted_files, "total_size_bytes": total_expanded_bytes},
                chunks=chunks,
                source_metadata={"file_count": len(extracted_files), "expanded_bytes": total_expanded_bytes},
                extraction_method="safe_archive_inspector",
                status=IngestionStatus.PROCESSING,
                warnings=warnings,
                processing_duration_seconds=round(duration, 3)
            )

