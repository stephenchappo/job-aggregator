# Polly Runbook

## Purpose

Polly is the local meeting transcription tool for Deepthought. It ingests MP3 recordings, normalises audio, diarises speakers, transcribes speech, assigns speakers to transcript segments, and renders JSON plus human-friendly outputs.

## Scope

Use Polly for:

- meeting recordings
- interviews and screener calls
- exported MP3 conversations
- batch, non-realtime transcription

Do not use Polly yet for:

- realtime streaming transcription
- speaker-name auto-identification
- public HTTP serving
- summary generation in production

## Outputs

For each successful job Polly produces:

- `transcript.json`
- `transcript.md`
- `transcript.txt`
- `transcript.srt`
- `transcript.vtt`

JSON is the source of truth. All other formats are derived from it.

## Primary paths

Deepthought working tree:

```text
~/projects/meeting-pipeline
```

Important directories:

```text
data/input
data/processing
data/archive
data/output
data/logs
data/meetpipe.sqlite3
```

Shared NAS dropzone:

```text
/marvin/Documents/AI Dropzone
```

## Requirements

- Python 3.11
- `ffmpeg` and `ffprobe`
- NVIDIA GPU preferred
- `HUGGINGFACE_TOKEN` for pyannote model access

## Installation

### Deepthought install

```bash
cd ~/projects/meeting-pipeline
./scripts/install_deepthought.sh
source .venv/bin/activate
meetpipe doctor
```

### Manual install

```bash
cd ~/projects/meeting-pipeline
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -e '.[ml,dev]'
```

## Environment

Persist:

```bash
export HUGGINGFACE_TOKEN=hf_xxx
```

Recommended locations:

- `~/.profile`
- `~/.bashrc`

## Standard usage

### Process one MP3

```bash
cd ~/projects/meeting-pipeline
source .venv/bin/activate
meetpipe process data/input/example.mp3
```

### Process all MP3s in the input directory

```bash
meetpipe process data/input/
```

### Watch mode

```bash
meetpipe watch
```

### Check environment health

```bash
meetpipe doctor
```

### Show jobs

```bash
meetpipe status
meetpipe status <job-id>
```

### Retry a failed job

```bash
meetpipe retry <job-id>
```

### Re-render outputs from JSON

```bash
meetpipe render <job-id>
```

## Normal operator workflow

### Option A: direct processing

1. Copy an MP3 into `data/input/`.
2. Run `meetpipe process <path>`.
3. Check the latest output under `data/output/<job-id>/`.
4. Review `transcript.md`.
5. Move or copy final outputs to `/marvin/Documents/AI Dropzone`.

### Option B: watch mode

1. Start `meetpipe watch`.
2. Drop MP3 files into `data/input/`.
3. Wait for the job to finish.
4. Review outputs and move deliverables if needed.

## Smoke test result

Known successful sample as of 2026-04-07:

- input: `Latitude AI Screener with David - 260309.mp3`
- language: `en`
- speakers detected: `2`
- outputs created successfully

## Logging and debugging

Per-job logs are written under:

```text
data/logs/<job-id>.log
```

Intermediate artifacts remain under:

```text
data/processing/<job-id>/
```

## Known issues

### Whisper GPU fallback

`faster-whisper` currently falls back to CPU because CTranslate2 cannot load `libcublas.so.12` in the current environment.

Impact:

- pipeline still works
- transcription is slower than it should be

### Torchcodec warning

The pyannote stack emits a `torchcodec` warning on startup.

Impact:

- warning is noisy
- current pipeline still works because diarization input is preloaded in memory

## Maintenance

### Re-run environment checks

```bash
source .venv/bin/activate
meetpipe doctor
pytest -q
```

### Review recent jobs

```bash
meetpipe status
ls -1dt data/output/*
```

### Clean up old job artifacts

Safe manual cleanup targets:

- old folders under `data/processing/`
- old folders under `data/output/`
- old archived source copies under `data/archive/`

Do not delete the SQLite DB unless you intentionally want to lose job history.

## Upgrade path

### Near-term improvements

- restore GPU transcription path for faster-whisper
- remove or silence the torchcodec issue cleanly
- test `retry`, `render`, and `watch` in more detail
- add a stable output publishing flow to Marvin

### Medium-term improvements

- optional summaries and action items
- known-speaker mapping
- word-level alignment improvements
- Docker packaging
- minimal API or web wrapper

## Troubleshooting

### `meetpipe doctor` says `token_present: no`

Ensure `HUGGINGFACE_TOKEN` is exported in a shell file that your execution path actually loads.

### `nvidia-smi` works but transcription still uses CPU

Current issue is not basic CUDA visibility. It is the CTranslate2 runtime dependency for whisper GPU mode.

### Machine boots into emergency mode

Deepthought previously hit this because `/mnt/media_drive` was treated as required in `/etc/fstab`.

Current safe mount entry:

```fstab
UUID=A867-5792 /mnt/media_drive exfat defaults,nofail,x-systemd.device-timeout=10,uid=1000,gid=1000,umask=022,noatime 0 0
```

### pyannote fails on direct file decoding

Current code avoids that by loading WAV audio into memory before diarization.

## Support files

- `config.yaml`
- `scripts/install_deepthought.sh`
- `tests/`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/STATUS.md`
