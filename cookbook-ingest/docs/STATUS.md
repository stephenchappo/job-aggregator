# Cookbook Ingest Status

## Snapshot

Date: 2026-04-07

State: working v0.1

## Completed

- standalone `cookbook-ingest/` project scaffold created
- CLI implemented
- config and directory bootstrap implemented
- SQLite job tracking implemented
- EPUB extraction implemented
- MOBI conversion hook implemented through `ebook-convert`
- PDF extraction implemented through PyMuPDF
- optional local OpenAI-compatible LLM client implemented
- heuristic recipe segmentation implemented
- heuristic recipe structuring implemented
- duplicate detection implemented
- category mapping implemented
- deterministic Obsidian Markdown renderer implemented
- staged review artifacts implemented
- manual promotion flow implemented
- tests added and passing
- doctor command implemented
- end-to-end smoke test completed with a generated EPUB

## Verified Behaviors

- `python -m pytest -q` passes
- `python -m compileall cookbook_ingest tests` passes
- `doctor` reports environment and dependency state
- a sample EPUB stages a recipe note, `candidate.json`, `review.json`, and `source-excerpt.md`

## Current Known Issues

### 1. MOBI conversion depends on Calibre

Current behavior:

- `ebook-convert` is required for `.mobi`
- current local verification showed `ebook-convert: no`

Impact:

- MOBI support is not ready until Calibre is installed on the runtime machine

### 2. LLM path is off by default

Current behavior:

- extraction and staging work without LLMs
- OCR fallback and JSON structuring are present but disabled until configured

Impact:

- v1 works immediately for cleaner sources
- difficult scans and layout-heavy PDFs will benefit from enabling the local model endpoint later

### 3. Category mapping is conservative

Current behavior:

- uncertain candidates stage into review-oriented paths
- subcategory mapping is based on simple keyword rules

Impact:

- safer than aggressive auto-filing
- more manual classification work in early use

## Immediate TODOs

- install Calibre on Deepthought for MOBI support
- point `llm.base_url` at the Deepthought local model endpoint if you want OCR fallback and JSON structuring
- test with at least one real EPUB cookbook
- test with at least one real text-layer PDF cookbook
- test with at least one image-heavy PDF cookbook
- review how often duplicates and misclassifications occur on real books

## Near-Term Upgrade Path

- add better taxonomy and folder mapping
- improve heuristic segmentation for mixed-content books
- add richer promotion safety checks
- add bulk review helpers
- add a small installer script for Deepthought runtime setup

## Longer-Term Roadmap

- card image rendering
- richer source page extraction and citations
- n8n orchestration mode
- batch promotion UI or TUI
- nutrition parsing and metadata enrichment
