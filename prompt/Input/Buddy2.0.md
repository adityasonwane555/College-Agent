# BUDDY AI 2.0 — UNIVERSAL KNOWLEDGE INGESTION, HYBRID RAG, MULTI-MODEL INTELLIGENCE, AND OFFLINE AI
#hi
## 1. YOUR ROLE

Act as a senior AI architect, Python/FastAPI engineer, RAG engineer, local inference specialist, database architect, full-stack developer, IoT integration engineer, and production reliability engineer.

You are modifying an existing project named BUDDY AI, an intelligent college reception robot intended for deployment at Anantrao Pawar College of Engineering & Research (APCOER), Pune, Maharashtra, India.

The existing project uses a combination of:

* Python and FastAPI.
* SQLite and an existing institutional knowledge base.
* Ollama for local AI inference.
* Gemini for cloud AI inference.
* Groq for cloud AI inference.
* Existing web-search capabilities.
* Faster-Whisper for speech recognition.
* Text-to-speech services.
* React, TypeScript, and Vite.
* ESP32-S3 hardware.
* An ST7789 TFT display.
* An INMP441 microphone.
* A MAX98357A amplifier and speaker.
* An RGB status LED.

These components and paths are based on the project's existing architectural documentation. Verify the actual repository before relying on any assumption.

Your objective is to upgrade BUDDY into a robust, intelligent, continuously updateable, multimodal knowledge system with reliable offline capabilities.

The final system must:

1. Ingest many supported file formats, not just PDFs.
2. Automatically extract and organize useful information from uploaded files.
3. Store approved knowledge in a persistent, searchable knowledge base.
4. Update knowledge when documents change.
5. Answer questions using hybrid retrieval and relevant evidence.
6. Combine Ollama, Gemini, and Groq intelligently.
7. Remain useful when the internet and cloud AI providers are unavailable.
8. Support natural, low-latency spoken interaction.
9. Preserve existing working functionality.
10. Remain maintainable as models and technologies change.

This is an existing application.

DO NOT rebuild the project from scratch.

DO NOT replace working components without a demonstrated technical reason.

DO NOT rewrite the ESP32 firmware, voice pipeline, or frontend unnecessarily.

Inspect the actual codebase before deciding how to implement each feature.

Do not claim that a feature is complete unless it has actually been implemented and tested.

---

# 2. MANDATORY GIT SAFETY: CREATE A NEW BRANCH FIRST

This requirement must be completed before any source code modification.

Use this branch name:

feature/buddy-universal-rag-offline-ai

Perform the following steps:

1. Inspect the current Git repository.
2. Identify the current branch and baseline commit.
3. Inspect the working-tree status.
4. Identify staged and unstaged modifications.
5. Check for untracked user files that could be affected.
6. Preserve all existing user work.
7. If the working tree is clean, create the new feature branch from the current development baseline.
8. If the working tree contains uncommitted changes that could be mixed with the new work or endangered by branch creation, stop and ask the user how to proceed.
9. If the requested branch already exists, inspect it and do not overwrite it. Ask before choosing another branch name if necessary.
10. Confirm that the new branch is active.

Do not reset, clean, stash, discard, or overwrite user changes without authorization.

Do not modify main or another protected branch.

Do not commit, push, merge, or deploy without explicit user permission.

After completing this phase, report the branch name, original branch, baseline commit, and working-tree status.

Only then inspect and implement the feature.

---

# 3. INSPECT THE EXISTING APPLICATION

Before coding, inspect:

* Backend entry point and configuration.
* Agent orchestrator and fast-path routing.
* Existing Ollama service.
* Existing Gemini integration.
* Existing Groq integration.
* Existing web-search integration.
* Tool registry and function-calling implementation.
* SQLite schema and repository.
* Existing FTS5 indexes.
* Existing document ingestion and administration endpoints.
* Existing frontend administration interface.
* Existing authentication and authorization.
* Existing session management.
* Existing voice-processing pipeline.
* Existing hardware communication.
* Existing test suite.
* Dependency and environment configuration.
* Logging, caching, timeout, and retry mechanisms.

Determine which capabilities already exist and extend them instead of creating duplicate implementations.

Check whether the current Gemini integration is already functional.

Inspect the actual configured model IDs. Do not invent model identifiers or assume a provider's model is available.

Create a concise implementation plan based on the repository.

After reporting the plan, continue with implementation unless a genuine blocker requires user input.

---

# 4. CORE ARCHITECTURAL PRINCIPLES

Build BUDDY around five independent but integrated systems.

## A. Universal Knowledge Ingestion

Accept supported files, extract information using suitable processing tools, and prepare structured knowledge records.

## B. Persistent Knowledge Storage

Store original files, extracted content, structured facts, source metadata, and document versions.

## C. Hybrid Retrieval

Use structured database queries, keyword search, semantic search, and live web research where appropriate.

## D. Adaptive Multi-Model Intelligence

Use Ollama, Gemini, and Groq according to the task, measured quality, latency, and availability.

## E. Offline Intelligence

Ensure the local Ollama model and local knowledge base can handle ordinary conversations and previously indexed information without requiring internet access.

The knowledge base must remain independent of the AI providers.

Changing the model must not require rebuilding the entire knowledge base.

Do not train or fine-tune an LLM every time a new file is uploaded.

Use retrieval-augmented generation, persistent storage, and suitable local inference.

---

# 5. UNIVERSAL FILE INGESTION

This is a major requirement.

BUDDY must not be limited to PDFs.

Implement a modular ingestion framework that supports many useful file types through format-specific extractors.

Do not attempt to process every file using one universal extraction function.

Select an appropriate parser or processor for each supported format.

## 5.1 Initial supported formats

### Documents

Support, where practical:

* PDF: .pdf
* Plain text: .txt
* Markdown: .md
* Word documents: .docx
* Legacy Word documents: .doc, where safe and technically feasible
* Rich Text Format: .rtf
* OpenDocument Text: .odt
* HTML: .html, .htm
* XML: .xml
* JSON: .json
* YAML: .yaml, .yml

### Spreadsheets and tabular data

Support:

* Excel workbooks: .xlsx
* Legacy Excel workbooks: .xls, where feasible
* CSV: .csv
* TSV: .tsv
* OpenDocument spreadsheets: .ods

Extract sheet names, column names, tabular values, and relevant metadata.

Preserve relationships between headers and values.

Do not flatten a complex spreadsheet into an unstructured text blob if its tabular structure can be preserved.

### Presentations

Support:

* PowerPoint: .pptx
* Legacy PowerPoint: .ppt, where feasible
* OpenDocument presentations: .odp

Extract slide text, titles, notes where available, and slide ordering.

### Images

Support common image formats:

* .png
* .jpg
* .jpeg
* .webp
* .tif
* .tiff
* .bmp

Use OCR for images containing text.

Use an image-understanding model only when visual interpretation is necessary and a suitable local or cloud model is available.

Examples include extracting a poster's event date, reading a notice photographed on a phone, or interpreting a diagram.

OCR and image understanding must not invent illegible text.

### Source code and technical files

Support appropriate text-based formats, including:

* .py
* .js
* .ts
* .tsx
* .jsx
* .java
* .cpp
* .c
* .h
* .ino
* .html
* .css
* .sql
* .sh
* .ps1
* .toml
* .ini
* .env.example
* .log

Treat source code as reference material unless the user explicitly requests a separate, authorized code-execution workflow.

NEVER execute uploaded code merely to ingest or index it.

Never ingest actual secrets into ordinary searchable knowledge records. Detect and redact likely credentials where appropriate.

### Archives

Support safe inspection of:

* .zip
* .tar
* .gz
* .7z, if a suitable safe parser is available

Extract supported contained files through the same ingestion pipeline.

Enforce limits on archive size, expanded size, file count, nesting, and processing time.

Protect against archive bombs, path traversal, symbolic-link abuse, and decompression attacks.

Never execute archived contents.

### Audio

Support suitable audio formats, such as:

* .wav
* .mp3
* .m4a
* .flac
* .ogg

Use an appropriate transcription engine to extract speech where available.

Prefer existing local speech-processing infrastructure when it is suitable.

Preserve timestamps or segment boundaries when the transcription engine supports them.

For recordings containing multiple speakers, support speaker labels only when a suitable diarization capability exists and is enabled.

Do not claim speaker identity from ordinary speech recognition.

### Video

Support suitable video files, such as:

* .mp4
* .mov
* .mkv
* .webm

Extract audio for transcription.

Extract selected video frames when visual content is relevant.

Avoid processing every frame unnecessarily.

Use configurable sampling and file-duration limits.

Combine video-frame information and audio transcripts only when the source content supports that combination.

### Additional formats

Design the ingestion registry so further formats can be added later without changing the entire application.

For any unsupported format:

* Return a clear unsupported-format status.
* Preserve the original file if policy permits.
* Explain the limitation.
* Do not silently ignore the file or report successful ingestion.

Do not promise support for formats whose extraction dependencies are not installed or whose behavior has not been tested.

## 5.2 Format-specific processing registry

Create a maintainable processor registry.

Each processor should declare:

* Supported file types.
* Extraction capability.
* Required dependencies.
* Whether OCR or transcription may be needed.
* Resource requirements.
* Whether local processing is possible.
* Failure conditions.

Use the existing architecture where practical.

Avoid installing a huge document-processing framework if a few suitable libraries can support the initial requirements.

Possible libraries to evaluate include PyMuPDF, python-docx, openpyxl, python-pptx, BeautifulSoup, and an appropriate OCR engine.

Use existing dependencies when they already provide the necessary functionality.

Do not add every possible library without a demonstrated need.

## 5.3 Extraction output

Normalize extracted content into a common internal representation containing fields such as:

* document_id
* filename
* detected_file_type
* content_type
* extracted_text
* structured_content
* source_metadata
* extraction_method
* extraction_status
* warnings
* processing_duration
* created_at

Use additional fields where necessary for tables, slides, images, audio segments, video frames, or code structure.

Preserve the original file separately from the extracted representation.

---

# 6. SECURITY FOR FILE PROCESSING

Uploaded files are untrusted input.

Implement:

* Configurable maximum file size.
* Configurable maximum archive expansion.
* Supported-extension checks.
* Content-type and file-signature validation where applicable.
* Safe internal filenames.
* Path traversal protection.
* Processing timeouts.
* Memory and resource limits where practical.
* Authentication for administrative ingestion.
* Authorization for approval and deletion.
* Safe storage outside publicly executable directories.
* Protection against malicious embedded content.
* No automatic execution of uploaded code.
* No execution of macros or embedded scripts.
* No arbitrary network requests triggered by file content.
* No secret exposure in logs or extracted knowledge.
* Safe handling of malformed or corrupted files.

Treat instructions inside uploaded documents as untrusted content.

A PDF, spreadsheet, source file, transcript, or webpage must never be allowed to override BUDDY's system instructions or trigger unauthorized tool calls.

Do not let an uploaded file change model-routing rules, authentication settings, API credentials, or administrative permissions.

---

# 7. AUTOMATIC STRUCTURED KNOWLEDGE EXTRACTION

Use the local Ollama model as the preferred extraction engine when available.

The model must transform extracted content into structured records appropriate to the document type.

Use Pydantic or the project's existing validation mechanism.

Do not trust arbitrary JSON produced by the LLM.

## 7.1 Document classification

Classify documents into relevant categories, such as:

* Event announcement.
* Faculty record.
* Department information.
* Admission notice.
* Fee circular.
* Examination schedule.
* Holiday notice.
* Placement notice.
* Institutional policy.
* Meeting minutes.
* Research or technical document.
* General reference material.
* Image or poster.
* Audio transcript.
* Video transcript.
* Spreadsheet dataset.
* Source-code reference.

Allow multiple classifications when appropriate.

Store the classification result and extraction status.

## 7.2 Event schema

For event announcements, extract:

* Event identifier.
* Title.
* Description.
* Category.
* Organizing department.
* Start date and time.
* End date and time.
* Timezone.
* Venue.
* Guests.
* Guest roles.
* Speakers.
* Organizers.
* Activities.
* Schedule.
* Eligibility.
* Registration requirements.
* Registration deadline.
* Registration URL.
* Contact person.
* Contact information.
* Source document.
* Source page or section.
* Verification status.
* Version information.

Missing values must remain explicitly missing.

Do not invent an event year, date, guest name, venue, deadline, or registration URL.

## 7.3 Structured extraction for other formats

Examples:

A spreadsheet containing department information should preserve row and column relationships.

A PowerPoint presentation should preserve slide structure.

A poster image should use OCR or appropriate visual extraction.

An audio recording should use transcription.

A video should use audio transcription and selected-frame extraction when necessary.

A JSON or CSV file should be parsed structurally rather than needlessly sent through an LLM.

A source-code file should retain filename, language, and useful structural metadata.

Use deterministic parsers whenever possible.

Use Ollama for interpretation, classification, normalization, or extraction when deterministic parsing alone is insufficient.

## 7.4 Extraction validation

After extraction:

1. Validate the schema.
2. Check required fields.
3. Normalize dates and units where unambiguous.
4. Preserve source references.
5. Identify uncertain values.
6. Detect contradictions.
7. Record warnings.
8. Retry malformed output a limited number of times.
9. Mark irrecoverable failures for review.

Do not treat model-generated confidence values as proof of correctness.

Where possible, verify critical extracted values against the original text, table, image, or source location.

---

# 8. AUTOMATIC KNOWLEDGE UPDATES AND VERSIONING

New files should update BUDDY's knowledge without requiring manual data entry for every extracted fact.

However, automatic extraction does not mean that every extracted value should immediately become authoritative.

Implement a knowledge lifecycle.

## 8.1 File identity

Calculate a cryptographic hash of each file.

Detect exact duplicate uploads.

Where useful, also calculate normalized content hashes.

Avoid repeating extraction and embedding work for identical content.

## 8.2 Document versioning

Preserve document versions.

When a new file resembles an existing document, determine whether it is:

* A duplicate.
* A revised document.
* A new document.
* A potentially conflicting document.

Use deterministic matching first.

Use semantic comparison only when needed.

Do not merge unrelated files merely because their content is similar.

## 8.3 Knowledge states

Support states such as:

* uploaded
* processing
* pending_review
* approved
* rejected
* superseded
* failed
* archived

Maintain an audit trail for consequential changes.

## 8.4 Approval policy

Provide configurable automatic-approval policies.

Recommended defaults:

* Low-risk, well-validated, non-conflicting reference content may be eligible for automatic indexing.
* Event dates, venues, cancellations, fees, admission requirements, and other consequential institutional facts should require review when their authority is uncertain.
* Conflicting revisions must not silently replace approved information.
* Clearly identified trusted sources may use a more automated policy once that policy has been explicitly configured.

Preserve the original file and source evidence.

## 8.5 Index synchronization

When approved knowledge changes:

* Update structured records.
* Update keyword indexes.
* Update vector indexes.
* Invalidate affected caches.
* Record indexing failures.
* Allow failed indexing operations to be retried.

The authoritative database must remain intact if a derived index fails.

---

# 9. PERSISTENT HYBRID KNOWLEDGE BASE

Retain the existing SQLite database.

Do not destroy or replace existing institutional records.

## 9.1 Structured storage

Use structured tables for facts that benefit from deterministic querying.

Examples:

* Events.
* Faculty.
* Departments.
* Contacts.
* Registration deadlines.
* Notices.
* Schedules.
* Document metadata.
* Source references.
* Version history.
* Approval status.

## 9.2 Full-text retrieval

Preserve and improve existing SQLite FTS5 search where appropriate.

Use keyword search for:

* Exact event titles.
* Faculty names.
* Department names.
* Document identifiers.
* Registration information.
* Specific terms and phrases.

## 9.3 Semantic retrieval

Add a local vector index if the project does not already have one.

Evaluate a suitable lightweight vector store such as Chroma.

Choose one implementation rather than introducing multiple vector databases.

Use an embedding model compatible with the deployment environment.

Prefer local embeddings when practical.

Design the vector store behind an abstraction so it can be replaced later.

The vector index must be rebuildable from approved documents and structured records.

Do not treat vector similarity as proof that a retrieved fact is true.

## 9.4 Retrieval fusion

Use the following retrieval strategies according to the question:

* SQL for exact structured facts.
* FTS5 for keyword matches.
* Vector search for semantic similarity.
* Document-specific retrieval for tables, slides, transcripts, or other structured content.
* Web search for current external information.

Combine retrieval results where useful.

Deduplicate results.

Prioritize verified, current, authoritative records.

Preserve source references.

Do not run every retrieval mechanism for every query.

## 9.5 Multilingual retrieval

BUDDY may encounter English, Marathi, and Hindi.

Inspect the existing language requirements.

Choose an embedding model and query-processing strategy based on actual multilingual retrieval tests.

Do not assume an English-only embedding model will perform well for Marathi.

Preserve original text and metadata.

Where appropriate, support multilingual queries against the same knowledge base without duplicating every document for each language.

---

# 10. MAKE OLLAMA A GENUINELY CAPABLE OFFLINE ASSISTANT

This is a critical requirement.

Ollama must not be used only to extract documents.

BUDDY must remain useful when Gemini, Groq, and internet access are unavailable.

## 10.1 Offline capabilities

When offline, BUDDY should be able to:

* Answer greetings.
* Maintain ordinary conversation.
* Answer basic general-knowledge questions within the local model's capabilities.
* Explain common technical concepts.
* Answer questions about previously indexed college information.
* Retrieve event dates, venues, guests, and schedules.
* Search previously ingested documents.
* Answer follow-up questions using local conversation context.
* Summarize local documents.
* Explain retrieved information.
* Provide a graceful response when information is missing.
* Continue operating its essential local functions.

Offline operation must not depend on live web search, cloud embeddings, cloud LLMs, or cloud-based validation.

## 10.2 Audit the current local model

Inspect:

* The configured Ollama model.
* Model availability.
* Model size.
* Context length.
* RAM and VRAM constraints where detectable.
* CPU or GPU inference behavior where observable.
* Existing timeout configuration.
* Current latency and failure behavior.

Do not automatically replace the local model without evaluating compatibility and available resources.

Benchmark the existing model against suitable alternatives from the Qwen family or other appropriate local model families.

Choose a model that balances:

* Response quality.
* First-token latency.
* Tokens per second.
* Tool use and structured output, where required.
* Memory consumption.
* Offline reliability.
* Hardware compatibility.

Do not assume the largest model is best for the actual PC.

Do not download multiple large models automatically without user authorization.

If a model is missing, report the missing dependency and provide a clear setup instruction.

## 10.3 Offline routing

Implement explicit provider-availability handling.

When cloud providers cannot be reached:

1. Stop attempting unnecessary cloud requests.
2. Use local knowledge retrieval.
3. Use Ollama for general reasoning when available.
4. Use deterministic response templates for simple facts.
5. Preserve conversation context locally where configured.
6. Return a clear limitation when the answer requires unavailable current information.

Do not repeatedly wait for cloud timeouts before switching to offline mode.

Use provider health checks, short failure timeouts, and circuit-breaker behavior where appropriate.

## 10.4 Offline knowledge retrieval

The following must remain local:

* Structured institutional database.
* Full-text search index.
* Vector index.
* Document metadata.
* Approved document contents.
* Local embeddings, if used.
* Essential routing logic.
* Basic conversation functionality.

Once a document is successfully ingested and indexed locally, ordinary queries about it must not require the internet.

Do not design the system so that cloud-generated embeddings are necessary for every search.

## 10.5 Offline general knowledge limitations

Be honest about the local model's limitations.

The system can answer common questions from the model's learned knowledge and the local knowledge base.

It cannot reliably know every current event, recent policy change, or newly published fact without receiving that information.

When the internet is unavailable and the answer requires current external information, BUDDY should say that it cannot verify the latest information.

Do not present stale model knowledge as current fact.

---

# 11. INTELLIGENT MULTI-MODEL ROUTING

Create or extend a central adaptive router.

The system must not call all three models for every question.

## 11.1 Suggested initial routing

Simple greetings:
Use the fast path.

Direct college facts:
Use SQL or a deterministic template.

Basic explanations:
Use Ollama when its measured quality and latency are adequate.

College-specific explanations:
Retrieve verified facts and pass them directly to the selected capable model.

Complex reasoning:
Select the best-performing available model according to the evaluation results.

Current events:
Use web search and appropriate sources before generating current claims.

Complex research:
Use hybrid retrieval and a capable cloud model, with optional independent review.

Offline:
Use the local database, local retrieval, and Ollama.

Provider failure:
Use an eligible fallback without repeatedly waiting for an unavailable provider.

## 11.2 Unified model interface

Create a common interface for the existing provider adapters.

Support, where applicable:

* Standard generation.
* Streaming generation.
* Structured output.
* Tool calling.
* Timeouts.
* Usage metrics.
* Error normalization.
* Provider health information.

Keep provider-specific API details within their adapters.

Reuse existing integrations.

Do not introduce a large orchestration framework unless there is a demonstrated benefit.

## 11.3 Model selection

Keep model identifiers configurable.

Do not invent model IDs.

Verify the availability of selected models through the existing configuration or official provider interfaces.

Benchmark local and cloud models against representative BUDDY queries.

Do not hardcode that Gemini is always best or that Groq is always fastest for every request.

Groq is an inference platform; evaluate the actual model being served.

## 11.4 Selective model collaboration

Implement optional multi-model workflows for questions that benefit from them.

Example:

1. Retrieve verified facts.
2. Ask Ollama to prepare a structured outline if useful.
3. Supply the original question, verified context, and draft to Gemini or Groq.
4. Ask the selected model to improve clarity and completeness.
5. Validate important facts against the original evidence.

For complex research, an independent second model may review an answer.

However, ordinary questions should not incur extra model calls unnecessarily.

If direct RAG-to-model generation is equally accurate and faster, prefer it.

---

# 12. FACTUAL GROUNDING

The knowledge base is the authority for verified institutional facts.

Models are responsible for explaining those facts, not inventing replacements.

For each response, provide relevant evidence and clear instructions.

The model must:

* Use verified records for college-specific information.
* Avoid inventing event dates, venues, names, fees, or deadlines.
* Acknowledge missing information.
* Distinguish verified facts from general explanation.
* Avoid presenting unsupported claims as official statements.
* Produce natural spoken language when appropriate.

Implement deterministic checks for critical values when practical.

For example, if the approved event date is 18 December, detect a response that says 15 December.

A second LLM must not be the sole verifier of critical institutional facts.

Preserve source references and retrieval metadata for the frontend.

---

# 13. LIVE WEB RESEARCH

Inspect and reuse the existing web-search integration where possible.

For questions requiring current information:

1. Determine whether live research is necessary.
2. Search appropriate sources.
3. Prefer official college, university, government, and other authoritative sources.
4. Record source URLs and retrieval timestamps.
5. Supply relevant evidence to the selected model.
6. Cite sources in the web console where supported.
7. Distinguish external research from approved institutional records.

Do not automatically add arbitrary web-search results to the official institutional knowledge base.

Use the document approval and ingestion workflow for permanent knowledge updates.

Offline queries must not depend on web search.

---

# 14. FOLLOW-UP QUESTIONS AND SESSION CONTEXT

Preserve the existing conversation-management architecture.

Support follow-up questions such as:

Visitor: "When is the robotics event?"

BUDDY retrieves the date.

Visitor: "Where is it?"

The system resolves the reference to the same event.

Visitor: "Who is the chief guest?"

The system retrieves the corresponding guest information.

Maintain relevant session context locally where appropriate.

Avoid resending the entire conversation history unnecessarily.

If multiple events match the conversation, ask for clarification.

Do not allow document text or retrieved content to override system instructions through conversation history.

---

# 15. ADMINISTRATION AND API INTEGRATION

Inspect existing administrative APIs and frontend components.

Extend the existing interfaces instead of creating duplicate systems.

Provide protected functionality for:

* Uploading supported files.
* Inspecting ingestion status.
* Viewing extracted information.
* Reviewing pending knowledge updates.
* Approving or rejecting updates.
* Inspecting document versions.
* Retrying failed ingestion.
* Searching indexed knowledge.
* Rebuilding derived indexes.
* Viewing model health.
* Inspecting retrieval and routing diagnostics.

Validate every administrative action on the server.

Do not expose secrets, unrestricted filesystem paths, internal stack traces, or private document contents to unauthorized users.

If a frontend upload component already exists, extend it to support the new file types and processing statuses.

Do not redesign the entire interface.

---

# 16. DATABASE SAFETY AND INDEX RECOVERY

Preserve the existing SQLite database.

Inspect its schema and migration conventions before making changes.

Use migrations for new tables and columns.

Do not drop or recreate existing institutional data.

Keep the relational database authoritative for structured knowledge and lifecycle state.

Treat vector and full-text indexes as rebuildable derived data where practical.

Handle partial failures carefully.

If a document is approved but vector indexing fails:

* Preserve the approved structured record.
* Record the indexing failure.
* Expose a diagnostic status.
* Allow retry.
* Do not claim semantic indexing succeeded.

Provide a safe index-rebuild process.

Preserve original documents and version history.

---

# 17. PERFORMANCE AND RESOURCE MANAGEMENT

Measure the system before optimizing it.

Track:

* File extraction latency.
* OCR latency.
* Audio transcription latency.
* Local structured extraction latency.
* Database query latency.
* Keyword retrieval latency.
* Vector retrieval latency.
* Web-search latency.
* Ollama first-token latency.
* Ollama generation throughput.
* Gemini latency.
* Groq latency.
* Response validation latency.
* Total time to first spoken response.
* Total response completion time.

Optimize by:

* Skipping unnecessary LLM calls.
* Avoiding web search for simple local questions.
* Running independent retrieval operations concurrently where appropriate.
* Limiting context size.
* Using configurable result limits.
* Reusing provider clients.
* Applying suitable caching.
* Invalidating caches when knowledge changes.
* Avoiding unnecessary model handoffs.
* Streaming output when supported.
* Preventing large document ingestion jobs from blocking chat requests.

Do not promise performance improvements without measurements.

Keep CPU, RAM, GPU, and disk requirements reasonable for the actual deployment hardware.

---

# 18. VOICE AND ESP32-S3 COMPATIBILITY

Preserve the existing working voice and hardware integration.

The ESP32-S3 must continue to support its existing responsibilities:

* Microphone input.
* Audio playback.
* Display rendering.
* LED status.
* Wi-Fi communication.
* Existing hardware APIs.

Do not rewrite firmware unless a specific compatibility issue requires it.

The local backend must be able to serve offline responses to the existing voice interface.

Ensure the new ingestion pipeline does not interfere with voice processing.

Where feasible, stream model output to the existing TTS pipeline so that BUDDY can start speaking before the complete response is generated.

Preserve established API contracts.

Do not claim end-to-end streaming works unless it has been tested.

---

# 19. SECURITY AND CONFIGURATION

Inspect the current environment configuration.

Do not hardcode API keys, passwords, or tokens.

Do not copy real secrets into documentation, tests, frontend code, or new configuration files.

Use the existing settings system and environment variables.

Protect cloud API keys on the backend.

Do not expose provider credentials to the ESP32 or browser.

Do not disable authentication to simplify development.

Do not automatically rotate external account credentials without permission.

If exposed credentials are found, report the exposure and recommend rotation.

Use placeholder values in example configuration files.

---

# 20. TESTING REQUIREMENTS

Add automated tests using the existing testing framework.

Use mocks for cloud provider calls where appropriate.

The standard test suite must not require paid API calls.

## A. File ingestion

Test:

* PDF.
* DOCX.
* TXT.
* Markdown.
* CSV.
* XLSX.
* PPTX.
* JSON.
* HTML.
* Image OCR.
* Audio transcription where the dependency is available.
* Video processing where supported.
* ZIP archive extraction.
* Unsupported formats.
* Corrupted files.
* Duplicate uploads.
* Oversized files.
* Malicious archive paths.
* Extraction failures.
* Missing optional dependencies.

## B. Structured extraction

Test:

* Correct event extraction.
* Missing fields.
* Ambiguous dates.
* Invalid model output.
* Source references.
* Schema validation.
* Contradictory records.

## C. Knowledge updates

Test:

* New document ingestion.
* Duplicate detection.
* Revised event dates.
* Revised venues.
* Approval and rejection.
* Document versioning.
* Index update failures.
* Index rebuilding.
* Cache invalidation.

## D. Hybrid retrieval

Test:

* Exact structured queries.
* Keyword search.
* Semantic search.
* Result fusion.
* Metadata filtering.
* Source provenance.
* Exclusion of ineligible records.
* Conflicting evidence.
* Multilingual retrieval where configured.

## E. Multi-model orchestration

Test:

* Ollama-only responses.
* Gemini responses.
* Groq responses.
* Retrieval-grounded generation.
* Selective draft-and-polish.
* Provider timeouts.
* Provider failures.
* Fallback routing.
* Missing local models.
* Offline operation.
* Prevention of unnecessary model calls.

## F. Offline behavior

Explicitly test the application with cloud providers mocked as unavailable and web search disabled.

Verify that BUDDY can:

1. Answer a greeting.
2. Answer a basic general-knowledge question within the local model's capabilities.
3. Retrieve a previously indexed event.
4. Answer a follow-up about that event.
5. Search locally indexed documents.
6. Respond gracefully when required information is absent.

Verify that these tests do not attempt cloud requests.

## G. Security

Test:

* Unauthorized uploads.
* Unauthorized approval.
* Malformed files.
* Archive path traversal.
* Prompt injection in uploaded content.
* Secret redaction where implemented.
* Rejection of unauthorized tool execution.

## H. Regression

Run the existing tests.

Verify that established chat, voice, hardware, and administration functionality remains compatible.

---

# 21. REQUIRED END-TO-END ACCEPTANCE TEST

Create a synthetic test corpus.

Do not insert synthetic records into the real production knowledge base.

Include:

1. A robotics event notice.
2. A CSV or spreadsheet containing event details.
3. A presentation describing event activities.
4. A text or Markdown file containing supplementary information.
5. A revised event notice changing the event date.

The event data may include:

Title: APCOER Robotics Innovation Day 2026

Original date: 15 December 2026

Time: 10:00 AM onwards

Venue: Main Auditorium, APCOER

Chief guest: Dr. Example Guest

Activities:

* Robotics exhibition.
* Autonomous robot demonstrations.
* Technical presentations.
* Student innovation challenge.

Registration is required, but no deadline is stated.

Clearly label all test data as synthetic.

Run these tests:

TEST 1:
Ingest each supported test file through the appropriate processor.

TEST 2:
Verify that extracted information preserves the correct fields and source references.

TEST 3:
Verify that missing registration deadlines remain null.

TEST 4:
Approve the synthetic knowledge records.

TEST 5:
Ask when the robotics event is scheduled.

Verify that the correct date is returned.

TEST 6:
Ask where the event is happening.

Verify that the correct venue is returned.

TEST 7:
Ask who the chief guest is.

Verify that the correct guest is returned.

TEST 8:
Ask a follow-up question such as "What activities will take place?"

Verify that the system retrieves the relevant activity information.

TEST 9:
Disable cloud providers and web search.

Verify that Ollama and local retrieval can answer the same supported questions without attempting network access.

TEST 10:
Ask a basic general-knowledge question while offline.

Verify that the local model generates a response.

TEST 11:
Ask for a current fact that is unavailable locally.

Verify that BUDDY acknowledges its inability to verify current information instead of inventing an answer.

TEST 12:
Upload a revised notice changing the event date to 18 December 2026.

Verify that the change is detected, version history is preserved, and approval requirements are respected.

TEST 13:
Simulate vector-index failure and verify that authoritative records are preserved.

TEST 14:
Run the existing regression tests.

Report the actual results.

---

# 22. DOCUMENTATION

Update the existing project documentation to explain:

* The new architecture.
* Supported file types.
* Optional processing dependencies.
* How ingestion works.
* How to add new file processors.
* How structured extraction works.
* How to approve knowledge updates.
* How versioning works.
* How hybrid retrieval works.
* How to rebuild indexes.
* How Ollama operates offline.
* How model routing works.
* How provider fallback works.
* How to run the acceptance tests.
* How to diagnose ingestion failures.
* How to configure the local model.
* Which features require internet access.
* Which features work completely offline.
* Remaining limitations.

Clearly distinguish implemented features from future possibilities.

Do not document untested functionality as completed.

---

# 23. DEFINITION OF DONE

The upgrade is complete only when:

1. The feature branch was created before source code changes.
2. Existing architecture was inspected.
3. Existing data and working functionality were preserved.
4. A modular multi-format ingestion system exists.
5. Supported formats use appropriate extractors.
6. Structured knowledge extraction is validated.
7. Knowledge updates and versioning work.
8. The hybrid retrieval system works.
9. Ollama can handle supported offline conversations and retrieval-grounded questions.
10. Cloud providers can be disabled without breaking essential local operation.
11. Gemini and Groq receive relevant retrieved context when selected.
12. Model routing avoids unnecessary calls.
13. Important institutional facts are grounded in approved evidence.
14. Administrative actions remain protected.
15. Database migrations preserve existing records.
16. Index failures can be recovered from.
17. Tests have been executed and actual results reported.
18. Existing voice and hardware interfaces remain compatible.
19. No real secrets have been added to source control.
20. Documentation reflects the actual implementation.
21. All changes remain on the feature branch.
22. No commit, push, merge, or deployment occurred without authorization.

Do not describe the system as production-ready merely because it starts successfully.

Report incomplete features, untested paths, required model downloads, optional dependencies, and known risks.

---

# 24. EXECUTION ORDER

Execute the work incrementally.

PHASE 1:
Inspect Git and create the feature branch.

PHASE 2:
Inspect the repository and produce a concise implementation plan.

PHASE 3:
Implement the ingestion registry and common document representation.

PHASE 4:
Implement structured extraction, validation, and versioning.

PHASE 5:
Implement the knowledge lifecycle and approval policy.

PHASE 6:
Implement or extend hybrid retrieval.

PHASE 7:
Strengthen Ollama's offline capabilities and add explicit offline routing.

PHASE 8:
Implement or extend the unified provider interface and adaptive model router.

PHASE 9:
Implement grounding, selective model collaboration, and failure handling.

PHASE 10:
Integrate administration and frontend functionality.

PHASE 11:
Run the end-to-end acceptance tests and existing regression suite.

PHASE 12:
Update documentation and report the implementation status.

After each major phase, run the relevant tests and inspect the diff.

Prefer small, coherent changes over a massive rewrite.

If a critical implementation decision could risk existing functionality or data, explain the problem and ask before taking that risk.

Do not stop after producing a plan. Once the branch is safely created and the repository is inspected, proceed with implementation unless a genuine blocker requires user input.

Do not invent successful test results.

Do not claim that offline operation has been verified unless cloud access was actually disabled or mocked and the relevant tests passed.

Do not commit, push, merge, or deploy without explicit permission.

---

# 25. FINAL REPORT

At completion, provide:

1. Original branch and feature branch.
2. Confirmation that main was not modified.
3. Baseline commit hash.
4. Architecture changes.
5. Supported file formats implemented and tested.
6. Files created and modified.
7. Database migrations performed.
8. New dependencies and their purposes.
9. Local model configuration and offline capabilities.
10. Model-routing behavior.
11. Test commands executed.
12. Actual test results.
13. Measured latency, if available.
14. Security considerations.
15. Manual configuration required.
16. Features not implemented or not tested.
17. Remaining production risks.
18. Confirmation that no commit or push occurred.

The final objective is a unified BUDDY intelligence system in which knowledge is continuously updateable, local intelligence remains useful offline, and cloud models improve response quality when available.

Build it incrementally, preserve the existing application, and verify the result rather than merely producing code.
