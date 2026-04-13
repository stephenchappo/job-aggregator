# Cookbook Ingest Architecture

## Overview

Cookbook Ingest is a native Python batch pipeline for local cookbook ingestion on Deepthought.

The pipeline is intentionally simple:

1. discover source file
2. register job in SQLite
3. copy source into a per-job working directory
4. extract a normalized document from EPUB, PDF, or MOBI
5. segment recipe-like sections
6. structure each accepted segment into canonical recipe data
7. classify and duplicate-check each candidate
8. render staged Obsidian notes plus review artifacts
9. promote approved recipes into the live vault on demand

## Design Goals

- fully local processing
- deterministic job tracking
- staged review before live vault writes
- deterministic Markdown rendering
- optional local LLM integration without making the core pipeline depend on it
- operator-friendly CLI

## Core Stack

- Python 3.11+
- SQLite
- Pydantic
- Typer
- Watchdog
- BeautifulSoup
- PyMuPDF
- optional OpenAI-compatible local API

## Runtime Model

Cookbook Ingest is currently a single-process CLI application. Normal use is either manual CLI execution or a watched drop-folder loop. No scheduler or web service is required for v1.

## Data Flow

```text
EPUB / PDF / MOBI
  -> intake folder or manual CLI target
  -> SQLite job row
  -> per-job source copy
  -> document extraction
  -> normalized document.json + document.md
  -> recipe segmentation
  -> candidate structuring
  -> duplicate + category checks
  -> staged Markdown + JSON review artifacts
  -> manual promotion
  -> live Obsidian recipe folder
```

## Module Map

### `cookbook_ingest/cli.py`

Typer CLI entrypoint.

Commands:

- `process`
- `retry`
- `status`
- `review`
- `promote`
- `doctor`
- `watch`

### `cookbook_ingest/config.py`

- YAML config loading
- environment override support
- directory bootstrap

### `cookbook_ingest/db.py`

- SQLite schema
- job create/update/read/list

### `cookbook_ingest/ingest.py`

- supported file discovery
- SHA256 hashing
- job id generation
- source copy into the per-job directory

### `cookbook_ingest/extractors.py`

- EPUB parsing from archive contents
- MOBI conversion through `ebook-convert`
- PDF extraction through PyMuPDF
- optional OCR/doc-VLM fallback through the local vision model

### `cookbook_ingest/segment.py`

- recipe-like section detection
- ingredient and method signal scoring
- page-aware segment metadata

### `cookbook_ingest/llm_client.py`

- OpenAI-compatible local chat-completions calls
- recipe JSON structuring prompt
- OCR-to-Markdown vision prompt

### `cookbook_ingest/structure.py`

- heuristic candidate building when LLM mode is disabled or unavailable
- section parsing for ingredients, method, timing, and notes
- tag, course, category, and difficulty inference

### `cookbook_ingest/classify.py`

- deterministic folder classification
- duplicate matching against existing recipe notes
- suggested live-path generation

### `cookbook_ingest/render.py`

- frontmatter rendering
- recipe Markdown rendering
- staged `candidate.json`
- staged `review.json`
- source excerpt output

### `cookbook_ingest/pipeline.py`

- orchestration across all stages
- job status updates
- archive and failed-file handling
- promotion into the live recipe tree

## Job Lifecycle

Tracked statuses:

- `pending`
- `processing`
- `staged`
- `failed`
- `archived`

`staged` means document extraction and candidate rendering completed and review artifacts were written. Promotion is tracked separately through review records and the job's `promoted_count`.

## Canonical Artifact Model

### Job Record

Stored in SQLite and contains:

- source path
- source hash
- timestamps
- job status
- working directory
- archive/failed paths
- document output paths
- staged and promoted counts

### Extracted Document

Per job:

- source metadata
- normalized text
- normalized Markdown
- page map when available
- OCR usage flag

### Recipe Candidate

Per staged recipe:

- canonical recipe fields
- timing block
- source notes
- duplicate warnings
- confidence score
- rendered note metadata

### Review Record

Per staged recipe:

- staged recipe id
- job id
- stage path
- suggested live path
- warnings
- duplicate matches
- ready-for-promotion flag

## LLM Integration Model

LLM support is optional.

When disabled:

- EPUB, PDF, and MOBI extraction still work
- segmentation and structuring fall back to heuristic parsing

When enabled:

- recipe segments can be normalized through a local text model
- poor-text PDFs can use a local vision model for OCR fallback

The current implementation expects an OpenAI-compatible local endpoint and is configured by:

- base URL
- API key env var
- structuring model name
- vision model name

## Storage Strategy

### Intake Root

`E:\Documents\cookbook ingestion`

Stores:

- raw incoming files
- jobs
- archive
- failed
- logs
- SQLite DB

### Obsidian Vault

`D:\Documents\Obsidian Vault\80-Recipes`

Stores:

- staged candidate recipe folders
- live promoted recipe folders

## Current Technical Limits

### Extraction Quality

Text-heavy EPUBs and PDFs work best. Image-heavy PDFs depend on the optional local vision model.

### Classification Quality

Folder mapping is keyword-based in v1 and intentionally conservative.

### Promotion Model

Promotion is one recipe at a time. There is no bulk-approve or merge flow yet.

## Future Extension Points

Good next additions:

- bulk promotion tooling
- explicit duplicate-resolution workflow
- better recipe taxonomy mapping
- card-image rendering
- direct n8n integration
- richer PDF page-reference handling
- nutrition and metadata enrichment
