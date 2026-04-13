# Cookbook Ingest Runbook

## Purpose

Cookbook Ingest is the local ebook-to-Obsidian recipe pipeline for Deepthought. It watches `E:\Documents\cookbook ingestion`, extracts recipe candidates from cookbook files, stages them for review, and promotes approved recipes into the live Obsidian recipe tree.

## Scope

Use Cookbook Ingest for:

- EPUB cookbooks
- PDF cookbooks
- MOBI cookbooks when Calibre is installed
- local batch import into the existing recipe vault structure

Do not use Cookbook Ingest yet for:

- direct image-to-recipe card rendering
- nutrition analysis
- shopping list generation
- public HTTP serving
- auto-promotion into the live vault without review

## Outputs

For each successful job Cookbook Ingest produces:

- `document.json`
- `document.md`
- one staged folder per accepted recipe candidate
- `<Recipe Title>.md`
- `candidate.json`
- `review.json`
- `source-excerpt.md`

`candidate.json` is the structured source of truth for each staged recipe. The Markdown note is the Obsidian-facing render.

## Primary Paths

Repo working tree:

```text
~/projects/job-aggregator/cookbook-ingest
```

Primary intake root:

```text
E:\Documents\cookbook ingestion
```

Important runtime paths:

```text
E:\Documents\cookbook ingestion\jobs
E:\Documents\cookbook ingestion\archive
E:\Documents\cookbook ingestion\failed
E:\Documents\cookbook ingestion\logs
E:\Documents\cookbook ingestion\cookbook_ingest.sqlite3
```

Obsidian destinations:

```text
D:\Documents\Obsidian Vault\80-Recipes\00-Staging
D:\Documents\Obsidian Vault\80-Recipes
```

Template source:

```text
D:\Documents\Obsidian Vault\60-Templates\[Template] Recipe Card.md
```

## Requirements

- Python 3.11+
- local checkout of this repo
- writable access to `E:\Documents\cookbook ingestion`
- writable access to the Obsidian vault
- `PyMuPDF` for PDF extraction
- `beautifulsoup4` for EPUB extraction
- `ebook-convert` for MOBI support

Optional:

- a local OpenAI-compatible API for LLM structuring and PDF OCR fallback

## Installation

### Manual Install

```bash
cd ~/projects/job-aggregator/cookbook-ingest
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -e '.[dev]'
```

### Verify Install

```bash
cd ~/projects/job-aggregator/cookbook-ingest
source .venv/bin/activate
python -m cookbook_ingest.cli doctor --config config.yaml
python -m pytest -q
```

## Configuration

Default config lives in:

```text
cookbook-ingest/config.yaml
```

Important settings:

- intake root
- jobs/archive/failed/logs paths
- Obsidian vault root
- staging root
- live recipes root
- duplicate threshold
- minimum recipe score
- OCR fallback threshold
- local LLM endpoint and model names

Environment overrides use the prefix:

```text
COOKBOOK_INGEST__
```

Example:

```bash
export COOKBOOK_INGEST__LLM__ENABLED=true
export COOKBOOK_INGEST__LLM__BASE_URL=http://localhost:11434/v1
```

## Standard Usage

### Process One File

```bash
cd ~/projects/job-aggregator/cookbook-ingest
source .venv/bin/activate
python -m cookbook_ingest.cli process "E:\Documents\cookbook ingestion\Example Cookbook.epub" --config config.yaml
```

### Process Everything Under a Folder

```bash
python -m cookbook_ingest.cli process "E:\Documents\cookbook ingestion" --config config.yaml
```

### Watch Mode

```bash
python -m cookbook_ingest.cli watch --config config.yaml
```

### Environment Check

```bash
python -m cookbook_ingest.cli doctor --config config.yaml
```

### Show Jobs

```bash
python -m cookbook_ingest.cli status --config config.yaml
python -m cookbook_ingest.cli status <job-id> --config config.yaml
```

### Review Staged Candidates for a Job

```bash
python -m cookbook_ingest.cli review <job-id> --config config.yaml
```

### Retry a Job

```bash
python -m cookbook_ingest.cli retry <job-id> --config config.yaml
```

### Promote a Reviewed Recipe

```bash
python -m cookbook_ingest.cli promote <staged-recipe-id> --config config.yaml
```

## Normal Operator Workflow

### Option A: Manual Processing

1. Copy a cookbook file into `E:\Documents\cookbook ingestion`.
2. Run `process` against the specific file.
3. Inspect staged notes under `D:\Documents\Obsidian Vault\80-Recipes\00-Staging`.
4. Review `candidate.json`, `review.json`, and the rendered Markdown note.
5. Promote any accepted recipe into the live recipe folders.

### Option B: Watch Mode

1. Start `watch`.
2. Drop EPUB, PDF, or MOBI files into `E:\Documents\cookbook ingestion`.
3. Wait for the job to finish.
4. Review staged recipes in Obsidian.
5. Promote accepted recipes one by one.

## Job Layout

Each job keeps working artifacts under:

```text
E:\Documents\cookbook ingestion\jobs\<job-id>\
```

Typical contents:

- copied source file
- `document.json`
- `document.md`
- generated page images if OCR fallback ran

Per-job logs are written under:

```text
E:\Documents\cookbook ingestion\logs\<job-id>.log
```

## Review and Promotion Rules

Review before promotion when:

- the category landed in `Needs Classification`
- a duplicate warning appears
- source pages are missing but matter for the note
- ingredients or method look incomplete

Promotion should only happen when:

- title is correct
- source book is correct
- ingredient list is usable
- method steps are usable
- the target live folder will not overwrite an existing recipe

## Known Issues

### MOBI depends on Calibre

Current behavior:

- MOBI files require `ebook-convert`
- if it is missing, MOBI jobs fail cleanly

Impact:

- EPUB and PDF still work
- MOBI support is unavailable until Calibre is installed

### LLM features are disabled by default

Current behavior:

- heuristic extraction works without a model
- OCR fallback and JSON structuring only activate when `llm.enabled` is true

Impact:

- pipeline is usable without a local model endpoint
- difficult PDFs may need manual cleanup until LLM support is enabled

### Classification is intentionally conservative

Current behavior:

- recipes with low category confidence stage under review-oriented paths

Impact:

- fewer bad auto-filing mistakes
- more manual sorting in v1

## Maintenance

### Re-run Health Checks

```bash
source .venv/bin/activate
python -m cookbook_ingest.cli doctor --config config.yaml
python -m pytest -q
```

### Review Recent Jobs

```bash
python -m cookbook_ingest.cli status --config config.yaml
Get-ChildItem "E:\Documents\cookbook ingestion\jobs" | Sort-Object LastWriteTime -Descending
```

### Safe Cleanup Targets

- old folders under `E:\Documents\cookbook ingestion\jobs\`
- old source files under `E:\Documents\cookbook ingestion\archive\`
- old failed files under `E:\Documents\cookbook ingestion\failed\`
- stale logs under `E:\Documents\cookbook ingestion\logs\`

Do not delete the SQLite DB unless you intentionally want to lose job history.

## Troubleshooting

### `doctor` says `ebook-convert: no`

Install Calibre on the runtime machine if you want MOBI support.

### `doctor` says `recipe_template_exists: no`

Confirm the Obsidian vault path and template path are correct in `config.yaml`.

### A PDF stages no recipes

Check:

- whether the PDF had an actual text layer
- whether OCR fallback is enabled through the local LLM endpoint
- `document.md` for extraction quality
- the job log for extraction errors

### Promotion fails because the target exists

The pipeline will not overwrite an existing live recipe folder. Review the staged candidate, compare it with the existing recipe, and either rename or merge manually.
