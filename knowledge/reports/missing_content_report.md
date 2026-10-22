# Missing Content & Verification Report

## Summary
- **Total Inaccessible URLs:** 0
- **Total Scanned / Non-selectable PDFs Detected:** 3

## 1. Failed or Inaccessible URLs (0)
No failed URLs encountered during this crawl.

## 2. Scanned / Image-Only PDFs (3)
These documents are officially hosted on the college portal but contain scanned image pages without a native text layer.
- **Student-Placement1-1** (8 pages): [https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement1-1.pdf](https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement1-1.pdf)
- **Student-Placement1** (8 pages): [https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement1.pdf](https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement1.pdf)
- **Student-Placement** (7 pages): [https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement.pdf](https://abmspcoerpune.org/wp-content/uploads/2024/12/Student-Placement.pdf)

## 3. Recommendations & Next Steps
1. **OCR Pipeline for Scanned Administrative Circulars:** Integrate Tesseract OCR or Vision LLM ingestion for the image-only PDFs listed above (primarily signed affiliation certificates and historical receipts).
2. **Scheduled Sitemap Polling:** Set up a weekly cron or GitHub Action executing `scripts/crawl_apcoer.py` to ingest new semester timetables, examination circulars, and CAP admission round notices automatically.
