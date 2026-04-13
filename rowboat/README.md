# Rowboat

Local support project for the Rowboat life operating system.

## Purpose

This folder tracks the reproducible setup for:

- the official Rowboat desktop app on Zaphod
- the repo-backed Rowboat workspace
- the Deepthought local Ollama backend
- privacy and outbound-data constraints
- future ingestion and automation work

This is not the Rowboat source code. It is the local project wrapper around your deployment and operating model.

## Architecture

- `Zaphod`
  - official Rowboat app
  - primary interactive surface
  - owns the local workspace checkout

- `Deepthought`
  - local Ollama model host
  - transcript and backend support

- `rowboat-workspace`
  - actual Rowboat workspace on disk
  - currently at `C:\Users\steph\projects\rowboat-workspace`

## Current Paths

- Workspace: `C:\Users\steph\projects\rowboat-workspace`
- Rowboat app: `C:\Users\steph\AppData\Local\Rowboat-win32-x64`
- Workspace binding: `C:\Users\steph\.rowboat` -> `C:\Users\steph\projects\rowboat-workspace`
- Deepthought support docs: `/srv/docker/deepthought/rowboat`
- Deepthought Ollama endpoint: `http://192.168.1.151:11434`

## Privacy

Closed by default.

- No data leaves the local network unless explicitly approved.
- Any outbound flow must be labeled clearly.
- Local models are preferred.
- External connectors stay disabled until reviewed.

## Project Layout

```text
rowboat/
  README.md
  docs/
    architecture.md
    setup.md
    privacy.md
  scripts/
    install-zaphod.ps1
    verify-deepthought.ps1
```

## Next Work

- refine workspace note schemas
- build initial ingestion helpers
- add first pilot corpus import scripts
- define local event ingestion for NFC and ambient capture
