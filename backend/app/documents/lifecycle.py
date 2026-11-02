"""
BUDDY AI 2.0 — Knowledge Lifecycle, Versioning & Approval Policy
Handles document uploads, duplicate detection, version history,
diff tracking, pending update reviews, and derived index synchronization.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .common import ExtractedDocument, IngestionStatus
from .processors.registry import processor_registry
from .extraction import extract_event_from_document, EventSchema
from .vector_store import vector_store
from ..database.repository import repo
from ..database.models import DocumentMetadataModel, EventModel
from ..security.file_validation import calculate_file_hash, sanitize_filename, validate_file_size


class KnowledgeLifecycleManager:
    """
    Orchestrates document ingestion pipelines, duplicate detection, content diffing,
    and human-in-the-loop review approvals for authoritative college knowledge bases.
    """
    def __init__(self, default_auto_approve: bool = False):
        self.default_auto_approve = default_auto_approve

    def process_and_ingest(
        self,
        filepath: Path,
        auto_approve: Optional[bool] = None,
        actor: str = "admin"
    ) -> Dict[str, Any]:
        """
        Full lifecycle processing for an uploaded file:
        1. Validates size & path safety.
        2. Detects exact duplicates via SHA-256 hash.
        3. Parses format via appropriate processor.
        4. Extracts structured knowledge (events, policies).
        5. Tracks revisions / date changes if existing record exists.
        6. Enforces approval policy (requires review for consequential changes).
        7. Synchronizes FTS5 and vector indexes.
        """
        validate_file_size(filepath)
        file_hash = calculate_file_hash(filepath)
        filename = sanitize_filename(filepath.name)

        # 1. Exact Duplicate Detection
        existing_doc = repo.get_document_by_hash(file_hash)
        if existing_doc:
            return {
                "status": "duplicate",
                "message": f"Exact duplicate file already exists in knowledge base: '{existing_doc['filename']}'. Skipping redundant processing.",
                "document_id": existing_doc["id"],
                "file_hash": file_hash,
                "version": existing_doc["version"]
            }

        # 2. Extract content with format-specific processor
        extracted_doc = processor_registry.process_file(filepath)
        if extracted_doc.status == IngestionStatus.FAILED:
            return {
                "status": "failed",
                "message": "File extraction failed.",
                "warnings": extracted_doc.warnings,
                "document_type": extracted_doc.detected_file_type
            }

        # 3. Detect revisions of an existing named document
        existing_named_doc = repo.get_document_by_name(filename)
        version = (existing_named_doc["version"] + 1) if existing_named_doc else 1
        extracted_doc.version = version

        should_auto_approve = self.default_auto_approve if auto_approve is None else auto_approve

        # 4. Save document metadata & chunks into SQLite authoritative repository
        meta = DocumentMetadataModel(
            filename=filename,
            title=extracted_doc.title,
            total_pages=extracted_doc.source_metadata.get("total_pages", 1),
            uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chunk_count=len(extracted_doc.chunks),
            file_hash=file_hash,
            content_type=extracted_doc.content_type,
            detected_type=extracted_doc.detected_file_type.value,
            status="approved" if should_auto_approve else "pending_review",
            version=version,
            warnings="; ".join(extracted_doc.warnings),
            metadata_json=json.dumps(extracted_doc.source_metadata)
        )

        raw_chunks = [
            {
                "page_number": ch.page_number,
                "section_title": ch.section_title,
                "content": ch.content
            }
            for ch in extracted_doc.chunks
        ]
        doc_id = repo.save_document(meta, raw_chunks)
        extracted_doc.document_id = doc_id

        # 5. Extract structured event knowledge
        extracted_event = extract_event_from_document(extracted_doc)
        diff_summary = ""
        pending_update_id = None

        if extracted_event:
            # Check for existing event with same title
            existing_event = repo.get_event_by_title(extracted_event.title)
            if existing_event:
                # Track revision diff
                diffs = []
                if existing_event["date"] != extracted_event.date:
                    diffs.append(f"Date revised from '{existing_event['date']}' to '{extracted_event.date}'")
                if existing_event["venue"] != extracted_event.venue:
                    diffs.append(f"Venue revised from '{existing_event['venue']}' to '{extracted_event.venue}'")
                diff_summary = "; ".join(diffs) if diffs else "Event details updated"

                # Consequential change: require review unless explicitly auto-approved
                pending_update_id = repo.add_pending_update(
                    entity_type="event",
                    extracted_data=extracted_event.model_dump(),
                    document_id=doc_id,
                    entity_id=existing_event["id"],
                    notes=f"Revision: {diff_summary}"
                )
                if should_auto_approve:
                    repo.approve_pending_update(pending_update_id, reviewer=actor)
            else:
                # Brand new event
                pending_update_id = repo.add_pending_update(
                    entity_type="event",
                    extracted_data=extracted_event.model_dump(),
                    document_id=doc_id,
                    notes="New event discovered from uploaded document"
                )
                if should_auto_approve:
                    repo.approve_pending_update(pending_update_id, reviewer=actor)

        # 6. Audit trail & version tracking
        action = "revised" if version > 1 else "created"
        repo.add_document_version(
            document_id=doc_id,
            version=version,
            file_hash=file_hash,
            filename=filename,
            action=action,
            diff_summary=diff_summary,
            actor=actor
        )

        # 7. Derived Indexing: FTS5 and Vector Store
        vector_errors: List[str] = []
        try:
            repo.sync_fts_index()
        except Exception as e:
            extracted_doc.warnings.append(f"FTS5 indexing failure: {str(e)}")

        try:
            vector_store.index_document_chunks(filename)
        except Exception as e:
            vector_errors.append(str(e))
            extracted_doc.warnings.append(f"Vector indexing failure: {str(e)}")

        final_status = "approved" if should_auto_approve else "pending_review"

        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "version": version,
            "lifecycle_status": final_status,
            "file_hash": file_hash,
            "chunk_count": len(extracted_doc.chunks),
            "event_extracted": extracted_event.model_dump() if extracted_event else None,
            "diff_summary": diff_summary,
            "pending_update_id": pending_update_id,
            "warnings": extracted_doc.warnings,
            "vector_errors": vector_errors,
            "processing_duration": extracted_doc.processing_duration_seconds
        }


lifecycle_manager = KnowledgeLifecycleManager(default_auto_approve=False)

