# Polly Architecture

## Overview

Polly is a native Python batch pipeline for local meeting transcription on Deepthought.

The pipeline is intentionally simple:

1. ingest MP3
2. register job in SQLite
3. preprocess to mono 16 kHz WAV
4. diarise speakers
5. transcribe speech
6. align transcript to diarisation
7. postprocess into readable turns
8. render JSON, Markdown, TXT, SRT, VTT

## Design goals

- fully local processing
- deterministic job tracking
- JSON as canonical output
- swappable transcription and diarisation modules
- operator-friendly CLI

## Core stack

- Python 3.11
- `faster-whisper`
- `pyannote.audio`
- `ffmpeg`
- SQLite
- Pydantic
- Typer
- Watchdog

## Runtime model

Polly is currently a single-process CLI application. No daemon, scheduler, or web service is required for normal use.

## Data flow

```text
MP3
  -> ingest
  -> SQLite job row
  -> ffmpeg preprocess
  -> WAV
  -> pyannote diarisation
  -> faster-whisper transcription
  -> overlap alignment
  -> speaker turns
  -> canonical transcript JSON
  -> Markdown/TXT/SRT/VTT
```

## Module map

### `app/cli.py`

Typer CLI entrypoint.

Commands:

- `process`
- `retry`
- `status`
- `render`
- `doctor`
- `watch`

### `app/config.py`

- YAML config loading
- environment override support
- directory bootstrap

### `app/db.py`

- SQLite schema
- job create/update/read/list

### `app/ingest.py`

- MP3 discovery
- SHA256 hashing
- deterministic-ish job ID generation
- copy to processing and archive

### `app/audio.py`

- `ffmpeg` preprocessing
- `ffprobe` metadata extraction

### `app/diarize.py`

- pyannote pipeline loading
- Hugging Face token handling
- compatibility handling for `token` vs `use_auth_token`
- in-memory WAV loading to avoid fragile direct decoder paths

### `app/transcribe.py`

- faster-whisper invocation
- segment and word extraction
- current CPU fallback if the configured GPU path fails

### `app/align.py`

- overlap computation
- transcript segment speaker assignment
- turn merging

### `app/postprocess.py`

- cleaned turn generation
- optional filler cleanup

### `app/render.py`

- JSON writing
- Markdown rendering
- SRT rendering
- VTT rendering
- TXT rendering

### `app/pipeline.py`

- stage orchestration
- job status updates
- error handling

## Job lifecycle

Tracked statuses:

- `queued`
- `preprocessing`
- `diarizing`
- `transcribing`
- `aligning`
- `postprocessing`
- `rendering`
- `summarising`
- `done`
- `failed`

## Canonical document model

The JSON output contains:

- job metadata
- audio metadata
- diarization segments
- transcript segments
- raw speaker turns
- cleaned speaker turns
- render metadata
- optional summary payload

## Current runtime characteristics

### Diarization

Pyannote is running successfully on Deepthought.

### Transcription

Whisper works, but currently falls back to CPU because the GPU runtime for CTranslate2 is not fully healthy for its expected CUDA library set.

### Rendering

All output renderers work on a real sample file.

## Current known technical quirks

### Pyannote API drift

Different pyannote versions use either `token` or `use_auth_token` when loading pipelines. Polly now supports both.

### Torchcodec instability

Current environment emits `torchcodec` warnings. Polly avoids direct decoder dependence for diarization by loading the WAV into memory.

### Whisper GPU dependency mismatch

`faster-whisper` currently trips on `libcublas.so.12`, so Polly retries transcription on CPU with `int8`.

## Future API surfaces

These are not implemented yet, but are good future extension points.

### Local Python API

Potential import usage:

```python
from app.pipeline import PipelineRunner
```

### HTTP API

Plausible future endpoints:

- `POST /jobs`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/retry`
- `GET /jobs/{job_id}/files`

### Folder-driven automation API

Current watch mode is already close to an ingestion API:

- drop MP3 into input folder
- poll job DB or output directory

## Storage strategy

### Local working state

Keep on Deepthought:

- code
- venv
- SQLite
- transient processing artifacts

### Shared outputs

Publish final artifacts to Marvin when needed:

- `/marvin/Documents/AI Dropzone`

## Documentation split

### Repo

Store:

- technical architecture
- setup
- runbooks
- code-adjacent troubleshooting
- upgrade and maintenance notes

### Obsidian

Store:

- project plan
- worklog
- experiments
- acceptance notes
- decisions and TODOs

### Outline

Store:

- stable service summary
- operational access info
- short homelab runbook
- owner-facing service documentation for future reference
