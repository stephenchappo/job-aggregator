# Polly

Polly is a local batch transcription and speaker diarisation pipeline for MP3 meeting recordings. It runs natively on Deepthought and produces speaker-labelled transcripts plus machine-readable outputs.

## Current status

Polly is working end to end on Deepthought as of 2026-04-07.

- Real MP3 smoke test completed successfully
- Output formats verified: JSON, Markdown, TXT, SRT, VTT
- Diarisation and transcription both run locally
- `faster-whisper` currently falls back to CPU when the GPU backend cannot load `libcublas.so.12`
- The pyannote stack still emits a non-fatal `torchcodec` warning

## What Polly includes

- Native Python CLI via `meetpipe`
- MP3 ingest and SQLite job tracking
- ffmpeg preprocessing to mono 16 kHz WAV
- faster-whisper transcription
- pyannote diarisation
- Deterministic overlap-based speaker assignment
- Canonical JSON transcript plus Markdown, TXT, SRT, and VTT rendering
- Retry, status, watch, render, and doctor commands

## Quick start

```bash
cd meeting-pipeline
./scripts/install_deepthought.sh
source .venv/bin/activate
meetpipe doctor
meetpipe process data/input/my_meeting.mp3
```

Outputs are written under `data/output/<job-id>/`.

## Documentation

- [docs/RUNBOOK.md](docs/RUNBOOK.md): operator guide, CLI usage, workflows, maintenance, troubleshooting
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): technical design, data flow, module map, dependencies, future API shape
- [docs/STATUS.md](docs/STATUS.md): current project state, known issues, work completed, upgrade path

## Deepthought notes

- Primary runtime target: Deepthought
- Required env var: `HUGGINGFACE_TOKEN`
- Preferred path: `~/projects/meeting-pipeline`
- Marvin dropzone for exports: `/marvin/Documents/AI Dropzone`

## Notes

- Summary generation is intentionally stubbed and disabled by default in v0.1.
- Speaker naming reuse is not implemented yet.
- `watch` mode is single-process and intentionally conservative for the first release.
