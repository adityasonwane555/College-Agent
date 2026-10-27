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
            cursor.execute("SELECT * FROM events ORDER BY date ASC LIMIT 10")
            return [dict(row) for row in cursor.fetchall()]

    def add_event(self, event: EventModel) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (title, date, time, venue, description, organizer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event.title, event.date, event.time, event.venue, event.description, event.organizer))
            conn.commit()
            return cursor.lastrowid

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
                INSERT OR REPLACE INTO documents (filename, title, total_pages, uploaded_at, chunk_count)
                VALUES (?, ?, ?, ?, ?)
            """, (meta.filename, meta.title, meta.total_pages, meta.uploaded_at, meta.chunk_count))
            doc_id = cursor.lastrowid

            # Remove previous chunks if overwriting
            cursor.execute("DELETE FROM document_chunks WHERE document_name = ?", (meta.filename,))

            for ch in chunks:
                cursor.execute("""
                    INSERT INTO document_chunks (document_id, document_name, page_number, section_title, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, meta.filename, ch.get("page_number", 1), ch.get("section_title", ""), ch["content"]))
            conn.commit()
            return doc_id

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
                SELECT document_name, page_number, section_title, content
                FROM document_chunks
                WHERE {conditions}
                LIMIT ?
            """
            cursor.execute(query, (*params, limit))
            return [dict(row) for row in cursor.fetchall()]


repo = DatabaseRepository()
