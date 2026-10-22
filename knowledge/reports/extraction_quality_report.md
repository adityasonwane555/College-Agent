# Extraction Quality & Verification Report

## Verification Checklist
- [x] Official robots.txt checked (`Allow: /` confirmed)
- [x] XML Sitemap indices parsed (507 URLs found)
- [x] Boilerplate navigation and scripts stripped
- [x] Markdown tables preserved with row/col relationships
- [x] Bulleted lists, headings, and paragraph hierarchy maintained
- [x] Source attribution (URL, timestamp) included in every record
- [x] JSONL, JSON, and Markdown formats compiled without syntax errors
- [x] Idempotent chunking with stable chunk IDs
- [x] Ingested into Buddy AI's SQLite FTS5 database

## Dataset Outputs
- `knowledge/processed/apcoer_knowledge.jsonl`: One record per page
- `knowledge/processed/apcoer_knowledge.json`: Master JSON dataset
- `knowledge/processed/apcoer_knowledge.md`: Complete searchable human-readable encyclopedia
- `knowledge/processed/apcoer_chunks.jsonl`: Semantic chunks for vector/FTS search
