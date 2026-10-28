# PROJECT: BUDDY AI — COMPLETE APCOER WEBSITE KNOWLEDGE EXTRACTION

Act as a senior web scraping engineer, data extraction specialist, and AI knowledge-base architect.

I am building BUDDY AI, an AI-powered reception robot for Anantrao Pawar College of Engineering & Research (APCOER), Pune, Maharashtra, India.

My official college website is:

https://abmspcoerpune.org/

## MAIN OBJECTIVE

Extract as much useful, publicly accessible text information as possible from the official college website and its linked public documents.

Create a complete, organized, searchable local knowledge base that my BUDDY AI agent can use to answer questions from students, parents, visitors, faculty, and other college guests.

Do not merely explain how to perform the task. Inspect my existing project, implement the crawler, run it where possible, save the extracted data into the project, and report the actual results.

Do not replace or break my existing BUDDY AI application.

# PHASE 1 — INSPECT MY PROJECT

Before making changes:

1. Inspect my existing project directory.
2. Identify the programming language and application architecture.
3. Identify the AI agent's main entry point.
4. Find any existing document-processing or knowledge-base modules.
5. Check whether I already use RAG, embeddings, a vector database, or semantic search.
6. Reuse existing infrastructure wherever possible.
7. Avoid unnecessary changes to existing application files.

If a knowledge-base pipeline does not exist, create a separate, modular ingestion system.

# PHASE 2 — DISCOVER THE WEBSITE

Start at:

https://abmspcoerpune.org/

Discover internal pages using:

* The homepage and navigation menus.
* Internal links.
* Sitemap files, if available.
* robots.txt.
* Department pages and their subpages.
* Faculty profiles.
* Academic pages.
* Admission pages.
* Placement pages.
* Campus facilities.
* Research and innovation pages.
* Student activities and clubs.
* News, events, and announcements.
* Public notices.
* Public reports and brochures.
* Downloadable documents.
* Publicly accessible PDF files.

Follow internal links recursively.

Restrict crawling to the official domain and explicitly approved college subdomains.

Handle redirects and duplicate URLs correctly.

Normalize URLs and remove URL fragments where appropriate.

Avoid infinite loops, calendar traps, repeated query parameters, and duplicate pages.

Use configurable crawl depth, request limits, and page limits. Make it possible to resume a crawl without starting from scratch.

Check and respect the website's crawling rules and access restrictions.

Do not bypass CAPTCHA, authentication, bot protection, paywalls, or other access controls. Record blocked URLs for manual or authorized collection.

# PHASE 3 — EXTRACT MAXIMUM USEFUL TEXT

For every accessible HTML page, extract all relevant content, including:

* Page title.
* Main heading.
* Subheadings.
* Paragraphs.
* Lists and bullet points.
* Tables and their row/column relationships.
* Department descriptions.
* Course names and details.
* Faculty names and official designations.
* Officially published contact details.
* Admission procedures.
* Eligibility criteria.
* Fee information, when publicly available.
* Academic calendars and timetables.
* Syllabus and curriculum information.
* Laboratory descriptions.
* Library and campus facilities.
* Placement information.
* Recruiter names and published placement statistics.
* Student clubs and activities.
* Events, workshops, seminars, and competitions.
* Research centres, projects, and publications.
* Institutional policies and committees.
* Official notices and announcements.
* Relevant image alternative text.
* Useful document links.
* Publication dates and academic years, where available.

Preserve the original meaning and context.

Remove irrelevant scripts, CSS, decorative markup, repeated navigation, and unnecessary boilerplate without removing meaningful content.

Do not discard useful information just because it appears in a table, list, accordion, or expandable section.

If relevant text is present in the HTML source, extract it even when it is not immediately visible in the page layout.

Use browser automation only when necessary and permitted to retrieve ordinary, publicly accessible page content that requires normal page rendering.

Do not interact with forms or submit data.

Do not invent facts or silently fill missing information using general knowledge.

# PHASE 4 — EXTRACT PDFS AND DOCUMENTS

This phase is essential.

Find public documents linked from every discovered page.

Prioritize:

* Admission brochures.
* Department brochures.
* Course and curriculum documents.
* Syllabus PDFs.
* Timetables.
* Academic calendars.
* Placement reports.
* Annual reports.
* Faculty profiles.
* Student handbooks.
* Examination notices.
* Research reports.
* Event reports.
* Public institutional reports.
* College policies.
* Publicly available committee documents.
* Laboratory and facilities information.

Download publicly accessible files only where permitted.

For PDF files:

1. Extract selectable text.
2. Preserve headings and paragraph order.
3. Extract tables when possible.
4. Retain page numbers.
5. Detect scanned documents.
6. Use OCR for scanned PDFs where feasible.
7. Record extraction failures.
8. Record documents requiring manual review.

Support other useful document formats when practical, including TXT, DOCX, and publicly accessible CSV files.

Set reasonable download size and timeout limits.

Avoid downloading the same file repeatedly.

Do not claim a PDF was extracted if the extraction returned no meaningful text.

Do not attempt to bypass protected downloads or access restrictions.

# PHASE 5 — SAVE RAW AND PROCESSED DATA

Create a dedicated knowledge directory in my existing project.

Use this structure unless my project already has an appropriate equivalent:

knowledge/
raw/
html/
pdf/
other_documents/

```
extracted/
    html_pages/
    pdf_documents/
    other_documents/

processed/
    apcoer_knowledge.jsonl
    apcoer_knowledge.json
    apcoer_knowledge.md
    apcoer_chunks.jsonl

manifests/
    crawl_manifest.json
    document_manifest.json
    failed_urls.json

reports/
    crawl_summary.md
    extraction_quality_report.md
    missing_content_report.md
```

Do not overwrite unrelated project files.

## A. RAW DATA

Preserve the original downloaded HTML or document files where practical.

The raw files must remain separate from cleaned and processed data.

## B. INDIVIDUAL PAGE TEXT

Save each extracted page separately.

Each file should include:

* Page title.
* Source URL.
* Retrieval timestamp.
* Relevant publication date, if available.
* Extracted main text.
* Extraction status.

## C. JSONL DATASET

Create a UTF-8 JSONL file containing one record per page or meaningful document section.

Use a schema similar to:

{
"id": "stable-unique-id",
"title": "Page or document title",
"source_url": "https://abmspcoerpune.org/example/",
"source_type": "html",
"category": "department",
"department": null,
"heading": "Section heading",
"content": "Extracted source text",
"retrieved_at": "ISO-8601 timestamp",
"published_at": null,
"academic_year": null,
"page_number": null,
"extraction_status": "success"
}

This is a schema example, not factual college content.

Use null when information is unavailable.

Do not guess academic years, faculty designations, publication dates, or department names.

Retain the source URL for every record.

## D. COMBINED MARKDOWN

Create a human-readable Markdown knowledge file.

Separate pages and documents with headings.

Include the source URL for each section.

Preserve useful tables, lists, and dates.

## E. DOCUMENT MANIFEST

Track each discovered document, including:

* URL.
* Title.
* File type.
* Download status.
* Extraction status.
* Page count, where applicable.
* Text length.
* OCR status.
* Error details.

# PHASE 6 — CLEANING AND DEDUPLICATION

Implement conservative data cleaning.

Requirements:

* Normalize whitespace and text encoding.
* Remove obvious repeated navigation boilerplate.
* Deduplicate identical URLs.
* Detect duplicate documents using file hashes where practical.
* Avoid storing duplicate content repeatedly.
* Preserve meaningful repeated facts and table rows.
* Preserve source dates and academic years.
* Retain different versions of documents when they are genuinely different.
* Do not merge unrelated pages because they contain similar text.

Keep raw source content separate from cleaned content.

If AI-generated summaries are created, save them separately and retain the original extracted text.

Do not replace the original text with an AI summary.

# PHASE 7 — CATEGORIZE THE KNOWLEDGE

Organize extracted records into categories where the source supports the classification.

Use categories such as:

1. College Overview.
2. Institutional History.
3. Trust and Management.
4. Admissions.
5. Undergraduate Courses.
6. Postgraduate Courses.
7. Departments.
8. Faculty.
9. Curriculum and Syllabus.
10. Academic Calendar.
11. Timetables.
12. Examination Information.
13. Fees and Scholarships.
14. Campus Facilities.
15. Laboratories.
16. Library.
17. Placements.
18. Recruiters and Placement Reports.
19. Student Clubs.
20. NSS and Student Development.
21. Events and Workshops.
22. Research and Innovation.
23. Projects and Publications.
24. Policies and Committees.
25. Official Contacts.
26. News and Announcements.
27. Other.

Do not fabricate missing categories or invent information to populate them.

If a page contains multiple topics, preserve the full page or split it into meaningful sections with the same source URL.

# PHASE 8 — PREPARE THE KNOWLEDGE FOR AI SEARCH

Inspect the existing BUDDY AI architecture.

If RAG already exists, integrate the processed documents into it.

If no RAG system exists, prepare a clean dataset suitable for future semantic search and embedding generation.

Create `apcoer_chunks.jsonl`.

Each chunk should contain:

* Stable chunk ID.
* Source URL.
* Source title.
* Category.
* Section heading.
* Chunk text.
* Academic year or publication date when available.
* PDF page number when applicable.

Chunking requirements:

* Split at headings and meaningful paragraph boundaries.
* Preserve context.
* Avoid cutting table rows away from their headers.
* Keep related names, designations, and descriptions together.
* Use configurable chunk sizes and overlap.
* Avoid unnecessarily large chunks.
* Avoid duplicate chunks.
* Preserve source attribution.

Make ingestion idempotent so rerunning the pipeline does not duplicate the knowledge base.

Do not fine-tune the language model on this data.

Use retrieval-augmented generation so BUDDY can find relevant official information when answering questions.

# PHASE 9 — SOURCE-GROUNDED ANSWERING

Prepare the knowledge base so BUDDY can answer questions such as:

* What courses does the college offer?
* What departments are available?
* Who is the HOD of a particular department?
* Where can I find department contact details?
* What facilities are available?
* How do admissions work?
* Where can I find the academic calendar?
* Where can I find a syllabus?
* What placement activities take place?
* Which clubs and student activities are available?
* Where can I find information about workshops?
* What is the official college contact information?

BUDDY must answer using retrieved source evidence.

Whenever practical, include the official source URL in the internal answer metadata so the application can provide a source reference.

If the answer cannot be found, BUDDY must clearly say that the information was not found in its current knowledge base.

It must not fabricate answers or invent faculty names, fee amounts, dates, eligibility criteria, or contact details.

If multiple sources conflict, preserve both sources and flag the conflict for review instead of silently deciding which one is correct.

# PHASE 10 — CURRENTNESS AND UPDATES

Academic information changes over time.

For every record, preserve retrieval timestamps and original publication dates when available.

Distinguish between current notices and historical reports.

Do not assume that an old timetable, syllabus, admission notice, or fee structure is current merely because it remains online.

When multiple versions exist:

* Preserve each version.
* Identify its academic year or publication date when possible.
* Mark currentness as unverified when it cannot be established.
* Do not silently replace a newer document with an older one.

Implement incremental crawling or content-hash comparison where practical.

Do not schedule recurring crawls unless explicitly requested.

# PHASE 11 — EXTRACTION QUALITY REPORT

After crawling, generate a report containing:

* Total URLs discovered.
* Unique HTML pages fetched.
* Successfully extracted HTML pages.
* Failed HTML pages.
* Blocked pages.
* Total PDF links discovered.
* PDFs successfully downloaded.
* PDFs successfully extracted.
* Scanned PDFs requiring OCR.
* Documents requiring manual review.
* Duplicate pages removed.
* Duplicate documents removed.
* Total extracted words and characters.
* Total knowledge chunks created.
* Categories represented in the data.
* Categories with little or no available information.
* Crawl depth reached.
* Remaining unprocessed URLs.
* Errors and their causes.

Clearly distinguish discovered URLs from successfully extracted pages.

Do not claim that the entire website was extracted unless the crawl results support that claim.

# PHASE 12 — TEST THE RESULTS

Validate that:

1. The homepage text was extracted.
2. Internal department pages were discovered.
3. Relevant faculty pages were processed.
4. Public document links were discovered.
5. Public PDFs were processed where possible.
6. Tables and lists were preserved.
7. Every record has source metadata.
8. JSON and JSONL files parse correctly.
9. Text encoding is valid.
10. Duplicate records are handled.
11. Failed URLs are recorded.
12. Re-running ingestion does not duplicate records.
13. The existing BUDDY AI application still works.
14. The output can be consumed by the existing knowledge retrieval system.

Create a small set of test questions based only on successfully extracted sources.

Verify that each test answer can be traced to its supporting source.

Do not invent test results or claim physical or application tests succeeded if they were not performed.

# PHASE 13 — WINDOWS EXECUTION

Provide straightforward Windows instructions.

Include:

* Dependency installation.
* Environment setup.
* How to run the crawler.
* How to resume a crawl.
* How to regenerate the processed dataset.
* How to inspect the reports.
* How to import the knowledge into BUDDY AI.

Use the project's existing Python environment if it is Python-based.

Avoid unnecessary dependencies.

Keep the crawler configurable, resumable, and easy to run again.

# FINAL DELIVERABLES

Create the working implementation in my existing project and provide:

1. Crawler source code.
2. Dependency and setup instructions.
3. Raw downloaded sources where appropriate.
4. Extracted page text.
5. Extracted PDF text.
6. `apcoer_knowledge.jsonl`.
7. `apcoer_knowledge.json`.
8. `apcoer_knowledge.md`.
9. `apcoer_chunks.jsonl`.
10. Crawl and document manifests.
11. Failed URL report.
12. Extraction quality report.
13. Windows run instructions.
14. Integration instructions for BUDDY AI.
15. A list of files created or modified.
16. A summary of actual test results and remaining limitations.

Start by inspecting the existing repository and the official website's crawling rules and sitemap.

Then implement and run the crawler.

Prioritize complete, accurate, source-attributed text extraction over superficial summaries.

Do not stop after writing the crawler. Run it, inspect its results, fix extraction errors where possible, and report honestly what was and was not collected.
