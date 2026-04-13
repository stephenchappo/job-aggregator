# Rowboat Architecture

## Goal

Support a local-first Rowboat deployment for life continuity:

- people
- opportunities
- obligations
- care systems
- systems maintenance
- inspiration recall

## Split

### Zaphod

- official Rowboat desktop app
- primary user interaction
- workspace owner

### Deepthought

- local Ollama inference
- reusable LAN model endpoint
- optional automation and ingestion support

### Workspace

- repo-backed workspace outside this repo
- currently bound through `C:\Users\steph\.rowboat`

## Design Rule

Keep the desktop app official and lightweight.

Keep backend inference local and reproducible.

Keep the actual knowledge workspace versionable and portable.
