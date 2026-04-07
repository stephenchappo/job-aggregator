# Polly Status

## Snapshot

Date: 2026-04-07

State: working v0.1, not yet fully polished

## Completed

- project scaffold created
- CLI implemented
- config and directory bootstrap implemented
- SQLite job tracking implemented
- ffmpeg preprocessing implemented
- pyannote diarisation integrated
- faster-whisper transcription integrated
- overlap-based speaker assignment implemented
- JSON/Markdown/TXT/SRT/VTT renderers implemented
- tests added and passing
- Deepthought runtime installed and verified
- Hugging Face token persisted
- Deepthought GPU recovered after reboot
- `/etc/fstab` fixed so optional media SSD does not break boot
- first real MP3 smoke test completed successfully
- successful output moved to Marvin AI Dropzone

## Working sample

- input: `Latitude AI Screener with David - 260309.mp3`
- detected language: `en`
- detected speakers: `2`
- output formats generated successfully

## Known issues

### 1. Whisper GPU path not fully healthy

Current behavior:

- configured GPU path fails
- Polly retries on CPU with `int8`
- pipeline succeeds, but slower than intended

Observed issue:

- `libcublas.so.12` not available to the CTranslate2 runtime used by faster-whisper

### 2. Pyannote startup warning

Current behavior:

- pyannote emits a `torchcodec` warning
- pipeline still succeeds because the diarization path uses in-memory waveform loading

## Immediate TODOs

- verify subtitle playback in a media player
- review transcript quality in more detail
- test `retry`
- test `render`
- test `watch`
- decide whether current timestamps are sufficient for v1

## Near-term upgrade path

- restore GPU inference for faster-whisper
- resolve or suppress torchcodec warning cleanly
- add more integration tests
- add a simple publish-to-dropzone helper

## Longer-term roadmap

- summary/action-item pass
- named speaker mapping
- known-speaker embeddings
- API layer or thin web UI
- container packaging
