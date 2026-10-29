import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..config import settings
from .models import (
    FAQModel, DepartmentModel, RoomModel, FacultyModel,
    CollegeHoursModel, EventModel, AnnouncementModel, DocumentMetadataModel
)


class DatabaseRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # FAQs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT DEFAULT 'General'
            )
            """)

            # Departments Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE,
                block TEXT NOT NULL,
                floor TEXT NOT NULL,
                hod TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """)

            # Rooms Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                building TEXT NOT NULL,
                floor TEXT NOT NULL,
                purpose TEXT NOT NULL
            )
            """)

            # Faculty Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                designation TEXT NOT NULL,
                cabin TEXT NOT NULL,
                email TEXT NOT NULL,
                office_hours TEXT NOT NULL,
                qualification TEXT DEFAULT '',
                experience TEXT DEFAULT '',
                area_of_interest TEXT DEFAULT '',
                research_profile TEXT DEFAULT ''
            )
            """)

            # Migration check for existing databases
            cursor.execute("PRAGMA table_info(faculty)")
            existing_cols = [col[1] for col in cursor.fetchall()]
            for col_name in ["qualification", "experience", "area_of_interest", "research_profile"]:
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE faculty ADD COLUMN {col_name} TEXT DEFAULT ''")

            # College Hours Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS college_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_name TEXT NOT NULL UNIQUE,
                open_time TEXT NOT NULL,
                close_time TEXT NOT NULL,
                days TEXT NOT NULL,
                notes TEXT
            )
            """)

            # Events Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                venue TEXT NOT NULL,
                description TEXT NOT NULL,
                organizer TEXT NOT NULL
            )
            """)

            cursor.execute("PRAGMA table_info(events)")
            existing_event_cols = [col[1] for col in cursor.fetchall()]
            event_cols_to_add = [
                ("activities", "TEXT DEFAULT ''"),
                ("guests", "TEXT DEFAULT ''"),
                ("eligibility", "TEXT DEFAULT ''"),
                ("registration_required", "INTEGER DEFAULT 0"),
                ("registration_deadline", "TEXT DEFAULT NULL"),
                ("registration_url", "TEXT DEFAULT NULL"),
                ("contact_info", "TEXT DEFAULT ''"),
                ("document_id", "INTEGER DEFAULT NULL"),
                ("version", "INTEGER DEFAULT 1"),
                ("status", "TEXT DEFAULT 'approved'")
            ]
            for col_name, col_def in event_cols_to_add:
                if col_name not in existing_event_cols:
                    cursor.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_def}")

            # Announcements Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date_posted TEXT NOT NULL,
                priority TEXT DEFAULT 'Normal'
            )
            """)

            # Documents Metadata Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                total_pages INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                chunk_count INTEGER NOT NULL
            )
            """)

            cursor.execute("PRAGMA table_info(documents)")
            existing_doc_cols = [col[1] for col in cursor.fetchall()]
            doc_cols_to_add = [
                ("file_hash", "TEXT DEFAULT ''"),
                ("content_type", "TEXT DEFAULT 'application/octet-stream'"),
                ("detected_type", "TEXT DEFAULT 'unknown'"),
                ("status", "TEXT DEFAULT 'approved'"),
                ("version", "INTEGER DEFAULT 1"),
                ("warnings", "TEXT DEFAULT ''"),
                ("metadata_json", "TEXT DEFAULT '{}'")
            ]
            for col_name, col_def in doc_cols_to_add:
                if col_name not in existing_doc_cols:
                    cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_def}")

            # Document Chunks Table for Search & Citations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                document_name TEXT NOT NULL,
                page_number INTEGER,
                section_title TEXT,
                content TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
            """)

            # Document Versions Table (Audit Trail & Versioning)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                filename TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                diff_summary TEXT DEFAULT '',
                actor TEXT DEFAULT 'system'
            )
            """)

            # Pending Knowledge Updates Table (Admin Approval Workflow)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_knowledge_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                extracted_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewer TEXT,
                notes TEXT DEFAULT ''
            )
            """)

            # Full-Text Search FTS5 Virtual Table for chunks
            cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                document_name,
                section_title,
                content
            )
            """)

            # Chunk Vectors Table for Semantic Hybrid Retrieval
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunk_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id INTEGER UNIQUE,
                embedding_json TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            conn.commit()

    # --- FAQ Operations ---
    def search_faq(self, query: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            wildcard = f"%{query}%"
            cursor.execute("""
                SELECT * FROM faqs 
                WHERE question LIKE ? OR answer LIKE ? OR category LIKE ?
                LIMIT 5
            """, (wildcard, wildcard, wildcard))
            return [dict(row) for row in cursor.fetchall()]

    def list_faqs(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faqs ORDER BY category, id")
            return [dict(row) for row in cursor.fetchall()]

    def add_faq(self, faq: FAQModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
                (faq.question, faq.answer, faq.category)
            )
            conn.commit()
            return cursor.lastrowid

    # --- Department Operations ---
    def get_department(self, name_or_code: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            wildcard = f"%{name_or_code.strip()}%"
            cursor.execute("""
                SELECT * FROM departments 
                WHERE LOWER(name) LIKE LOWER(?) OR LOWER(code) LIKE LOWER(?)
                LIMIT 1
            """, (wildcard, wildcard))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_departments(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def add_department(self, dept: DepartmentModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO departments (name, code, block, floor, hod, contact_email, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dept.name, dept.code, dept.block, dept.floor, dept.hod, dept.contact_email, dept.description))
            conn.commit()
            return cursor.lastrowid

    # --- Room Operations ---
    def get_room(self, room_query: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            wildcard = f"%{room_query.strip()}%"
            cursor.execute("""
                SELECT * FROM rooms 
                WHERE LOWER(room_number) LIKE LOWER(?) OR LOWER(name) LIKE LOWER(?) OR LOWER(purpose) LIKE LOWER(?)
                LIMIT 1
            """, (wildcard, wildcard, wildcard))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_rooms(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rooms ORDER BY building, floor, room_number")
            return [dict(row) for row in cursor.fetchall()]

    def add_room(self, room: RoomModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO rooms (room_number, name, building, floor, purpose)
                VALUES (?, ?, ?, ?, ?)
            """, (room.room_number, room.name, room.building, room.floor, room.purpose))
            conn.commit()
            return cursor.lastrowid

    # --- Faculty Operations ---
    def get_faculty(self, name_query: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            wildcard = f"%{name_query.strip()}%"
            cursor.execute("""
                SELECT * FROM faculty 
                WHERE LOWER(name) LIKE LOWER(?) 
                   OR LOWER(department) LIKE LOWER(?) 
                   OR LOWER(designation) LIKE LOWER(?) 
                   OR LOWER(area_of_interest) LIKE LOWER(?)
                   OR LOWER(email) LIKE LOWER(?)
                LIMIT 15
            """, (wildcard, wildcard, wildcard, wildcard, wildcard))
            return [dict(row) for row in cursor.fetchall()]

    def list_faculty(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faculty ORDER BY department, name")
            return [dict(row) for row in cursor.fetchall()]

    def add_faculty(self, fac: FacultyModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO faculty (name, department, designation, cabin, email, office_hours, qualification, experience, area_of_interest, research_profile)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fac.name, fac.department, fac.designation, fac.cabin, fac.email, fac.office_hours,
                fac.qualification or "", fac.experience or "", fac.area_of_interest or "", fac.research_profile or ""
            ))
            conn.commit()
            return cursor.lastrowid

    # --- Hours Operations ---
    def get_college_hours(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM college_hours ORDER BY facility_name")
            return [dict(row) for row in cursor.fetchall()]

    def add_college_hours(self, hours: CollegeHoursModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO college_hours (facility_name, open_time, close_time, days, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (hours.facility_name, hours.open_time, hours.close_time, hours.days, hours.notes))
            conn.commit()
            return cursor.lastrowid

    # --- Events Operations ---
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE status != 'rejected' ORDER BY date ASC LIMIT 10")
            return [dict(row) for row in cursor.fetchall()]

    def get_event_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE LOWER(title) = LOWER(?) LIMIT 1", (title.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_event(self, event: EventModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (
                    title, date, time, venue, description, organizer,
                    activities, guests, eligibility, registration_required,
                    registration_deadline, registration_url, contact_info,
                    document_id, version, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.title, event.date, event.time, event.venue, event.description, event.organizer,
                event.activities or "", event.guests or "", event.eligibility or "",
                1 if event.registration_required else 0,
                event.registration_deadline, event.registration_url, event.contact_info or "",
                event.document_id, event.version or 1, event.status or "approved"
            ))
            conn.commit()
            return cursor.lastrowid

    def update_event(self, event_id: int, event: EventModel) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events SET
                    title = ?, date = ?, time = ?, venue = ?, description = ?, organizer = ?,
                    activities = ?, guests = ?, eligibility = ?, registration_required = ?,
                    registration_deadline = ?, registration_url = ?, contact_info = ?,
                    version = ?, status = ?
                WHERE id = ?
            """, (
                event.title, event.date, event.time, event.venue, event.description, event.organizer,
                event.activities or "", event.guests or "", event.eligibility or "",
                1 if event.registration_required else 0,
                event.registration_deadline, event.registration_url, event.contact_info or "",
                event.version or 1, event.status or "approved",
                event_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    # --- Announcements Operations ---
    def get_announcements(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC LIMIT 10")
            return [dict(row) for row in cursor.fetchall()]

    def add_announcement(self, ann: AnnouncementModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO announcements (title, content, date_posted, priority)
                VALUES (?, ?, ?, ?)
            """, (ann.title, ann.content, ann.date_posted, ann.priority))
            conn.commit()
            return cursor.lastrowid

    # --- Document & Chunks Operations ---
    def save_document(self, meta: DocumentMetadataModel, chunks: List[Dict[str, Any]]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    filename, title, total_pages, uploaded_at, chunk_count,
                    file_hash, content_type, detected_type, status, version, warnings, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.filename, meta.title, meta.total_pages, meta.uploaded_at, meta.chunk_count,
                meta.file_hash or "", meta.content_type or "application/octet-stream",
                meta.detected_type or "unknown", meta.status or "approved",
                meta.version or 1, meta.warnings or "", meta.metadata_json or "{}"
            ))
            doc_id = cursor.lastrowid

            # Remove previous chunks and FTS entries if overwriting
            cursor.execute("SELECT id FROM document_chunks WHERE document_name = ?", (meta.filename,))
            old_chunk_ids = [r[0] for r in cursor.fetchall()]
            for oc_id in old_chunk_ids:
                cursor.execute("DELETE FROM document_chunks_fts WHERE chunk_id = ?", (oc_id,))
                cursor.execute("DELETE FROM chunk_vectors WHERE chunk_id = ?", (oc_id,))

            cursor.execute("DELETE FROM document_chunks WHERE document_name = ?", (meta.filename,))

            for ch in chunks:
                cursor.execute("""
                    INSERT INTO document_chunks (document_id, document_name, page_number, section_title, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, meta.filename, ch.get("page_number", 1), ch.get("section_title", ""), ch["content"]))
                chunk_id = cursor.lastrowid

                # Index chunk in FTS5
                cursor.execute("""
                    INSERT INTO document_chunks_fts (chunk_id, document_name, section_title, content)
                    VALUES (?, ?, ?, ?)
                """, (chunk_id, meta.filename, ch.get("section_title", ""), ch["content"]))

            conn.commit()
            return doc_id

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE file_hash = ? LIMIT 1", (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_document_by_name(self, filename: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE filename = ? LIMIT 1", (filename,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ? LIMIT 1", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_document_status(self, doc_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))
            conn.commit()

    def list_documents(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_chunks(self, keywords: List[str], limit: int = 4) -> List[Dict[str, Any]]:
        if not keywords:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Simple keyword matching across chunks
            conditions = " OR ".join(["content LIKE ?" for _ in keywords])
            params = [f"%{k}%" for k in keywords]
            query = f"""
                SELECT id, document_name, page_number, section_title, content
                FROM document_chunks
                WHERE {conditions}
                LIMIT ?
            """
            cursor.execute(query, (*params, limit))
            return [dict(row) for row in cursor.fetchall()]

    # --- FTS5 Operations ---
    def sync_fts_index(self) -> int:
        """Synchronizes FTS5 virtual table with all document chunks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_chunks_fts")
            cursor.execute("""
                INSERT INTO document_chunks_fts (chunk_id, document_name, section_title, content)
                SELECT id, document_name, section_title, content FROM document_chunks
            """)
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM document_chunks_fts")
            return cursor.fetchone()[0]

    def search_chunks_fts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches document chunks using SQLite FTS5 MATCH with ranking."""
        clean_q = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
        if not clean_q:
            return []
        tokens = [t for t in clean_q.split() if len(t) > 2]
        if not tokens:
            return []
        fts_query = " OR ".join(tokens)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT chunk_id, document_name, section_title, content, rank
                    FROM document_chunks_fts
                    WHERE document_chunks_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit))
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "chunk_id": r["chunk_id"],
                        "document_name": r["document_name"],
                        "section_title": r["section_title"],
                        "content": r["content"],
                        "rank": float(r["rank"]) if r["rank"] is not None else 0.0
                    })
                return results
            except Exception as e:
                # Fallback to like search if fts match encounters an unexpected token
                return self.search_chunks(tokens, limit=limit)

    # --- Document Versioning Operations ---
    def add_document_version(
        self,
        document_id: int,
        version: int,
        file_hash: str,
        filename: str,
        action: str,
        diff_summary: str = "",
        actor: str = "system"
    ) -> int:
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO document_versions (
                    document_id, version, file_hash, filename, action, timestamp, diff_summary, actor
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, version, file_hash, filename, action,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                diff_summary, actor
            ))
            conn.commit()
            return cursor.lastrowid

    def list_document_versions(self, document_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if document_id is not None:
                cursor.execute("SELECT * FROM document_versions WHERE document_id = ? ORDER BY version DESC, timestamp DESC", (document_id,))
            else:
                cursor.execute("SELECT * FROM document_versions ORDER BY timestamp DESC LIMIT 50")
            return [dict(row) for row in cursor.fetchall()]

    # --- Pending Knowledge Updates Operations ---
    def add_pending_update(
        self,
        entity_type: str,
        extracted_data: Dict[str, Any],
        document_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        confidence: float = 1.0,
        notes: str = ""
    ) -> int:
        import json
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pending_knowledge_updates (
                    document_id, entity_type, entity_id, extracted_data, status,
                    confidence, created_at, notes
                )
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
            """, (
                document_id, entity_type, entity_id, json.dumps(extracted_data),
                confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes
            ))
            conn.commit()
            return cursor.lastrowid

    def list_pending_updates(self, status: str = "pending") -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_knowledge_updates WHERE status = ? ORDER BY created_at DESC", (status,))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_update(self, update_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_knowledge_updates WHERE id = ? LIMIT 1", (update_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def approve_pending_update(self, update_id: int, reviewer: str = "admin") -> bool:
        import json
        from datetime import datetime
        pending = self.get_pending_update(update_id)
        if not pending or pending["status"] != "pending":
            return False

        data = json.loads(pending["extracted_data"])
        entity_type = pending["entity_type"]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if entity_type == "event":
                existing = self.get_event_by_title(data.get("title", ""))
                new_ver = (existing.get("version", 1) + 1) if existing else 1
                event_date = data.get("date") or (existing.get("date") if existing else "")
                event_venue = data.get("venue") or (existing.get("venue") if existing else "")
                event_time = data.get("time") or (existing.get("time") if existing else "")

                ev = EventModel(
                    title=data["title"],
                    date=event_date,
                    time=event_time,
                    venue=event_venue,
                    description=data.get("description") or (existing.get("description") if existing else ""),
                    organizer=data.get("organizer") or (existing.get("organizer") if existing else "APCOER"),
                    activities=", ".join(data.get("activities", [])) if isinstance(data.get("activities"), list) else str(data.get("activities") or (existing.get("activities") if existing else "")),
                    guests=", ".join(data.get("guests", [])) if isinstance(data.get("guests"), list) else str(data.get("guests") or (existing.get("guests") if existing else "")),
                    eligibility=data.get("eligibility") or (existing.get("eligibility") if existing else ""),
                    registration_required=data.get("registration_required", existing.get("registration_required", False) if existing else False),
                    registration_deadline=data.get("registration_deadline", existing.get("registration_deadline") if existing else None),
                    registration_url=data.get("registration_url", existing.get("registration_url") if existing else None),
                    contact_info=data.get("contact_info") or (existing.get("contact_info") if existing else ""),
                    document_id=pending.get("document_id"),
                    version=new_ver,
                    status="approved"
                )
                if existing:
                    self.update_event(existing["id"], ev)
                else:
                    self.add_event(ev)

            # Mark update as approved
            cursor.execute("""
                UPDATE pending_knowledge_updates
                SET status = 'approved', reviewed_at = ?, reviewer = ?
                WHERE id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reviewer, update_id))

            # Mark associated document as approved if exists
            if pending.get("document_id"):
                cursor.execute("UPDATE documents SET status = 'approved' WHERE id = ?", (pending["document_id"],))

            conn.commit()
            return True

    def reject_pending_update(self, update_id: int, reviewer: str = "admin", notes: str = "") -> bool:
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pending_knowledge_updates
                SET status = 'rejected', reviewed_at = ?, reviewer = ?, notes = notes || ' ' || ?
                WHERE id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reviewer, notes, update_id))
            conn.commit()
            return cursor.rowcount > 0

    # --- Chunk Vector Operations ---
    def save_chunk_vector(self, chunk_id: int, embedding: List[float], model_name: str = "local_vectorizer"):
        import json
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO chunk_vectors (chunk_id, embedding_json, dimensions, model_name, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                chunk_id, json.dumps(embedding), len(embedding), model_name,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_all_chunk_vectors(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cv.chunk_id, cv.embedding_json, cv.dimensions, cv.model_name,
                       dc.document_name, dc.page_number, dc.section_title, dc.content
                FROM chunk_vectors cv
                JOIN document_chunks dc ON cv.chunk_id = dc.id
            """)
            return [dict(row) for row in cursor.fetchall()]


repo = DatabaseRepository()
