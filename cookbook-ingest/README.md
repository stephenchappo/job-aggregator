# Cookbook Ingest

Local cookbook ebook ingestion pipeline for Deepthought. It watches `E:\Documents\cookbook ingestion`, extracts recipe candidates from EPUB, PDF, and MOBI sources, stages them into the Obsidian recipe vault format, and supports manual promotion into the live recipe folders.

## Features

- watched-folder intake and manual CLI processing
- SQLite job tracking
- EPUB extraction without external services
- MOBI conversion through `ebook-convert` when available
- PDF text extraction through PyMuPDF with optional OCR fallback via a local OpenAI-compatible vision model
- heuristic recipe segmentation with optional local LLM structuring
- deterministic Obsidian Markdown rendering based on the existing recipe template
- staged review output before live recipe promotion

## Quick Start

```bash
cd cookbook-ingest
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp config.yaml config.local.yaml
cookbook-ingest doctor --config config.local.yaml
cookbook-ingest process "E:\Documents\cookbook ingestion\My Cookbook.epub" --config config.local.yaml
```

## Commands

- `cookbook-ingest doctor`
- `cookbook-ingest process <path>`
- `cookbook-ingest watch`
- `cookbook-ingest status [job-id]`
- `cookbook-ingest review <job-id>`
- `cookbook-ingest promote <staged-recipe-id>`
- `cookbook-ingest retry <job-id>`

## LLM Integration

LLM support is optional. When `llm.enabled` is `true`, the pipeline expects an OpenAI-compatible local API and uses:

- `structuring_model` for candidate-to-JSON normalization
- `vision_model` for OCR fallback on poor-text PDFs

When LLM support is disabled or unavailable, the pipeline falls back to deterministic heuristics for segmentation and recipe note rendering.

## Documentation

- `docs/RUNBOOK.md`
- `docs/ARCHITECTURE.md`
- `docs/STATUS.md`
