# Rowboat TODO

## Phase 1 Pilot

Goal: get Rowboat reliably usable for a small set of real-life threads.

- [ ] Verify the Rowboat desktop app launches cleanly on Zaphod and uses `C:\Users\steph\.rowboat`.
- [ ] Confirm Rowboat is configured to use Deepthought Ollama at `http://192.168.1.151:11434`.
- [ ] Test `qwen3:8b` for both assistant and knowledge graph tasks in real usage.
- [ ] Record any onboarding choices or manual UI steps that should become reproducible setup notes.
- [ ] Create 5-10 high-value `People` notes for active relationships.
- [ ] Create 2-3 active `Opportunity` notes for live job threads.
- [ ] Create 2-3 `Obligation` notes for debts or recurring admin pressure.
- [ ] Create `Care Systems` notes for plant care and self-care.
- [ ] Create `Systems` notes for vehicle maintenance and Home Assistant maintenance.

## Phase 2 Privacy And Governance

Goal: make the local-first and closed-by-default rules explicit and enforceable.

- [ ] Define the complete list of approved local-only data classes.
- [ ] Define the approval process for any connector or feature that leaves the local network.
- [ ] Add a machine-readable outbound integration register alongside the human-readable docs.
- [ ] Add a clear review checklist for any future external service integration.
- [ ] Decide where secrets and local overrides should live without entering git.

## Phase 3 Workspace Foundation

Goal: stabilize the note model before scaling inputs.

- [ ] Review the current `knowledge/` taxonomy after initial live use.
- [ ] Normalize starter notes and templates across `People`, `Opportunities`, and `Obligations`.
- [ ] Add starter templates for `Care Systems`, `Systems`, `Commitments`, and `Inspiration`.
- [ ] Decide which domains should have one-note-per-entity versus timeline/event-driven notes.
- [ ] Add richer linking between `People`, `Meetings`, `Commitments`, and `Inspiration`.

## Phase 4 Ingestion

Goal: bring in high-value context without overwhelming the workspace.

- [ ] Define the first transcript import path from existing pipelines into `imports/transcripts/`.
- [ ] Define the first job-search material import path for job descriptions and interview notes.
- [ ] Decide which existing Obsidian notes should be mirrored or copied into Rowboat imports.
- [ ] Build a lightweight import format for events and transcripts that is easy to append to.
- [ ] Explore local image-description support for inspiration references.

## Phase 5 Reviews And Continuity

Goal: make Rowboat useful for staying on top of active threads over time.

- [ ] Design a daily review note format for active threads.
- [ ] Design a weekly review note format for drift detection and follow-up planning.
- [ ] Add a recurring review flow for social continuity.
- [ ] Add a recurring review flow for job-search continuity.
- [ ] Add a recurring review flow for obligations and maintenance.
- [ ] Add a small dashboard or status summary for active threads.

## Phase 6 Ambient Capture

Goal: lower the friction of updating state from the real world.

- [ ] Define the event schema for quick captures from phone shortcuts or NFC tags.
- [ ] Identify the first 3 NFC-driven workflows to prototype.
- [ ] Decide whether the first event receiver should be `n8n`, a small webhook, or a file-drop flow.
- [ ] Map event types to target note types and update rules.

## Phase 7 Reproducibility

Goal: make it easy to rebuild the setup after a machine loss or reimage.

- [ ] Add a one-command rebuild path for Zaphod setup.
- [ ] Add a one-command verification path for Deepthought backend health.
- [ ] Document all required local paths, versions, and assumptions.
- [ ] Revisit whether any part of the main Obsidian vault should be refactored around Rowboat patterns.
