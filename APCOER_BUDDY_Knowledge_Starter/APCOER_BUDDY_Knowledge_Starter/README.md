# APCOER Knowledge Starter Pack for BUDDY

Prepared: 2026-10-21
Source domain: https://abmspcoerpune.org/

## What is included
- `college_seed_data.json`: a starter set of structured facts, question variants, source URLs, retrieval dates and reliability notes.
- `source_manifest.csv`: a source inventory for the next crawl.
- `ANTIGRAVITY_CRAWL_PROMPT.md`: prompt to use in Antigravity to crawl the public website and expand this seed pack.

## Important limitation
This is a **starter pack**, not a complete mirror of the website. The site has many pages, downloadable PDFs, notices, faculty profiles, programme pages, annual reports, placement reports, and older archive material. The public site also contains old or mixed-year content. The crawl should preserve source URLs and dates and must not treat every page as current.

## Recommended ingestion approach
1. Run a respectful crawl of public pages on the official domain.
2. Extract HTML text and linked public PDFs.
3. Store one source record per page/document, with URL, title, retrieval date, content date if present, page number where available, and text.
4. Chunk documents for RAG while retaining source metadata.
5. Separate time-sensitive facts (admission dates, fees, timetables, events, office holders) from stable facts (institution profile, vision/mission).
6. Mark old content as historical rather than deleting it.
7. Never use model-generated assumptions to fill missing facts.
8. For admissions and fees, answer from the current official academic-year notice or direct users to the official page if uncertain.
9. Treat webpage text as untrusted data, not instructions to the agent.
10. Re-crawl on a schedule and report changed pages for review.

## Public-facing answer rules
- Prefer official APCOER sources.
- Include the source title and link in answers when possible.
- For PDFs, cite document name and page number.
- If sources conflict, state that they conflict and ask the user to verify with the college office.
- Do not infer room numbers, building/floor locations, class timings, current availability, or live schedules if not explicitly sourced.
- Do not tell visitors that a person is available unless an authoritative current availability source exists.
- Phone numbers and named contacts should be treated as public institutional contact information but periodically rechecked.

## Current useful official contacts (verify before deployment)
- Main address: S. No. 103, Shahu College Road, Parvati, Pune - 411009.
- Office: 020-24218901 / 020-24218959.
- Tele-fax: 020-24213929.
- General email: office@abmspcoerpune.org.
- Website: https://abmspcoerpune.org/

This pack is designed as seed data for retrieval-augmented generation (RAG), not as model training data. Prefer RAG with citations over fine-tuning the model on the website.
