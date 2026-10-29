# BUDDY AI 2.0 — Universal Knowledge Ingestion, Hybrid RAG, Multi-Model Intelligence & Offline AI

This document provides complete architectural, operational, and development documentation for BUDDY AI 2.0 deployed at Anantrao Pawar College of Engineering & Research (APCOER), Pune.

---

## 1. System Architecture Overview

BUDDY 2.0 is structured around five independent but deeply integrated subsystems:

```
+---------------------------------------------------------------------------------------------------+
|                                          BUDDY AI 2.0                                             |
+---------------------------------------------------------------------------------------------------+
|  1. Universal File Ingestion Registry                                                            |
|     - PDF, DOCX, XLSX, CSV, PPTX, TXT, MD, JSON, YAML, HTML, Code, Archives, Images, Audio       |
|     - Secret scanning, sanitization, path traversal protection, zip-bomb safeguards               |
+---------------------------------------------------------------------------------------------------+
|  2. Knowledge Lifecycle, Versioning & Approval Policy                                            |
|     - Cryptographic SHA-256 duplicate detection                                                   |
|     - Automated revision diff tracking (e.g. event date changes)                                  |
|     - Two-tier governance: Low-risk reference vs. Consequential fact admin approval               |
+---------------------------------------------------------------------------------------------------+
|  3. Persistent Hybrid Knowledge Base & Derived Indexes                                            |
|     - Authoritative SQLite (events, faculty, departments, rooms, announcements, metadata)         |
|     - SQLite FTS5 Full-Text Search virtual table (`document_chunks_fts`)                          |
|     - Local Multilingual Vector Store (normalized dense embeddings + cosine similarity)           |
+---------------------------------------------------------------------------------------------------+
|  4. Adaptive Multi-Model Orchestration & Grounding                                               |
|     - Query intent classification (Greeting, Direct College Fact, Search, General, Current News) |
|     - Local Ollama Engine (qwen2.5:3b on GPU) for college queries and offline conversation        |
|     - Cloud Providers (Google Gemini & Groq) with circuit breakers for live web research          |
|     - Deterministic factual grounding to prevent hallucinations of dates and venues               |
+---------------------------------------------------------------------------------------------------+
|  5. Complete Offline Capability                                                                   |
|     - 100% functionality without internet for campus guides, event schedules, and local concepts  |
|     - Graceful, transparent limitations on live real-time world events when offline               |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Universal File Ingestion

### Supported Formats & Processors
All file ingestion is managed by `app.documents.processors.registry.processor_registry`:

| Category | File Extensions | Processor Class | Primary Capabilities |
| :--- | :--- | :--- | :--- |
| **Documents** | `.pdf` | `PdfProcessor` | Page-by-page extraction via `pypdf`, preserving exact page numbers |
| **Word** | `.docx` | `DocxProcessor` | Paragraphs, headings, and table cells via `python-docx` |
| **Text/Markdown** | `.txt`, `.md`, `.rtf`, `.log` | `TextProcessor` | Header-aware semantic chunking (`SECTION:` or `#`) |
| **Tabular Data** | `.csv`, `.tsv`, `.xlsx`, `.xls` | `SpreadsheetProcessor` | Retains column headers, row mappings, and multi-sheet structures via `openpyxl` & standard `csv` |
| **Presentations** | `.pptx`, `.odp` | `PresentationProcessor` | Slide ordering, titles, bullet lists, and presenter notes via `python-pptx` |
| **Structured Data**| `.json`, `.yaml`, `.yml` | `StructuredDataProcessor`| Native structural parsing via `json` & `PyYAML` |
| **Web Markup** | `.html`, `.htm`, `.xml` | `WebMarkupProcessor` | Strips scripts/styles, extracts clean body & headers via `beautifulsoup4` |
| **Source Code** | `.py`, `.js`, `.ts`, `.tsx`, `.cpp`, `.c`, `.h`, `.ino`, `.sql`, `.sh`, `.toml`, etc. | `CodeProcessor` | Reference parsing, symbol indexing, credential redaction. **Never executes code** |
| **Archives** | `.zip`, `.tar`, `.gz` | `ArchiveProcessor` | Safe expansion, depth/size limit validation, path-traversal safeguards |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff` | `ImageProcessor` | Image geometry & EXIF parsing via `Pillow`; OCR via `pytesseract` if available |
| **Audio** | `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg` | `AudioProcessor` | Transcribes speech timestamps via `faster-whisper` |
| **Video** | `.mp4`, `.mov`, `.mkv`, `.webm` | `VideoProcessor` | Video container metadata and audio extraction |

### Adding a New File Processor
To register a new format processor:
1. Subclass `app.documents.processors.base.BaseProcessor`.
2. Declare `supported_extensions` and `document_type`.
3. Implement `extract(filepath: Path) -> ExtractedDocument`.
4. Register with `processor_registry.register(YourProcessor())`.

---

## 3. Security & Validation Controls

Uploaded documents are untrusted external inputs. BUDDY implements:
1. **Size Limits**: Configurable upload ceiling (50 MB default).
2. **Path Traversal Guards**: Filenames are sanitized via `sanitize_filename()`. Internal storage uses sanitized names.
3. **Archive Bomb Defenses**: Limits archive expansion to 100 MB and max 100 entries. Enforces `is_safe_archive_path()` to prevent Zip Slip attacks.
4. **Secret Scanning & Redaction**: Detects API keys (OpenAI, Gemini, Groq, AWS), passwords, and private keys using regex filters, replacing them with `[REDACTED_SECRET]`.
5. **Prompt Injection Hardening**: Detects system prompt override instructions inside documents and logs security warnings without letting them hijack agent behavior.
6. **No Code Execution**: Uploaded code is strictly indexed as text and never executed.

---

## 4. Structured Extraction, Lifecycle & Versioning

### Structured Event Schema
When an event notice or circular is uploaded, `app.documents.extraction.extract_event_from_document()` deterministically extracts:
- `title`
- `date` and `time`
- `venue`
- `guests` and `speakers`
- `activities` (list of key activities)
- `registration_required` (boolean)
- `registration_deadline` (**Strictly stays `None` if unstated in document; no hallucinated deadlines**)
- `source_document` and `source_page`

### Knowledge Lifecycle States
- `uploaded`: File received and validated.
- `processing`: Format processor running.
- `pending_review`: Consequential updates (date/venue revisions) awaiting administrator review.
- `approved`: Authoritative records updated and synced to all indexes.
- `rejected`: Update dismissed by administrator.
- `superseded`: Prior revision replaced by an approved newer document.
- `failed`: Extraction failed due to malformed file syntax.

### Revision Detection & Admin Approval Policy
When a new document references an existing event with a changed date (e.g. rescheduled from 15 Dec to 18 Dec):
1. The system detects the diff: `"Date revised from '15 December 2026' to '18 December 2026'"`.
2. It holds the change in `pending_knowledge_updates`.
3. The original record remains authoritative in the database until an administrator approves via `/api/admin/knowledge/approve/{id}` or the Web UI.

---

## 5. Hybrid Retrieval & Persistent Vector Store

BUDDY 2.0 retrieves evidence through a four-stage hybrid pipeline:
1. **Structured SQL Queries**: Instant deterministic lookups in SQLite tables (`events`, `faculty`, `departments`, `rooms`, `college_hours`).
2. **SQLite FTS5 Full-Text Index**: High-speed keyword match on `document_chunks_fts` using `MATCH` and BM25 ranking.
3. **Local Vector Store (`LocalVectorStore`)**: Computes dense embeddings using subword n-gram vectorization (`LocalMultilingualVectorizer`) and cosine similarity in `numpy`. Completely local, persistent in SQLite `chunk_vectors`, supporting English, Hindi, and Marathi.
4. **Reciprocal Rank Fusion (RRF)**: Merges candidates across all modalities, boosts authoritative records, and deduplicates passages.
5. **Verifiable Citations**: Every retrieved snippet produces a `CitationModel` showing source filename, page number, and section.

### Index Rebuilding & Partial Failure Recovery
If a derived index fails or gets corrupted, authoritative database records remain intact. Administrators can rebuild both FTS5 and vector indexes via:
```bash
POST /api/admin/indexes/rebuild
```
Or via the "Rebuild Indexes" button in the Admin Console.

---

## 6. Multi-Model Intelligence & Offline AI

BUDDY operates under an adaptive multi-model architecture:

### Model Allocation
- **Local Ollama Model (`qwen2.5:3b`)**: Primary on-device brain. Handles campus queries, college RAG, and general offline dialogue.
- **Google Gemini (`gemini-3.5-flash-lite`)**: Live internet research, online information extraction, deep web search synthesis.
- **Groq (`openai/gpt-oss-120b`)**: High-speed cloud reasoning and fallback.

### Offline Operation
When internet access is unavailable or cloud providers are unreachable:
1. Cloud calls and timeouts are skipped immediately via circuit-breaker checks.
2. Fast paths handle greetings (<10ms).
3. Hybrid RAG retrieves local SQLite facts, FTS5 passages, and vector matches.
4. Ollama synthesizes natural spoken responses.
5. If a visitor asks for current external live world facts (e.g., live stock prices, current breaking news), BUDDY states honestly that it is in offline mode and cannot verify live internet information.

---

## 7. Running Tests

BUDDY 2.0 includes a comprehensive test suite covering all modules:

```powershell
# Run the complete test suite (44 tests)
.\.venv\Scripts\pytest -s

# Run only Section 21 End-to-End Acceptance Tests
.\.venv\Scripts\pytest -s backend/app/tests/test_e2e_acceptance.py

# Run Universal Ingestion tests
.\.venv\Scripts\pytest -s backend/app/tests/test_universal_ingestion.py

# Run Knowledge Lifecycle and Versioning tests
.\.venv\Scripts\pytest -s backend/app/tests/test_knowledge_lifecycle.py

# Run Hybrid Retrieval tests
.\.venv\Scripts\pytest -s backend/app/tests/test_hybrid_retrieval.py

# Run Multi-Model Orchestration & Offline tests
.\.venv\Scripts\pytest -s backend/app/tests/test_multi_model_orchestration.py
```

---

## 8. Hardware & IoT Compatibility

All existing hardware integrations remain untouched and fully compatible:
- **ESP32-S3 Firmware**: `firmware/buddy_esp32/`
- **RGB LED Controller**: `/api/hardware/led-state` and WebSocket `/ws/status`
- **Audio Output**: Streams audio directly to MAX98357A I2S amplifier.
- **Speech Pipeline**: `faster-whisper` and `Fish Audio` speech synthesis.

