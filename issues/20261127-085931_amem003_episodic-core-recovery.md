# Implement the canonical Episodic Memory core and recovery model

## Priority
High

## Summary
Implement the approved Episodic Memory model: canonical Session DB schema, event extraction, validation, save, deduplication, relations, FTS-required and Vector-optional retrieval, safe prompt injection, consistency checks, backup, and recovery.

## Background
Source: bundle item H-03. Verified against master on 2026-11-27:
- `Explicit in code`: `episodic_events` has no match in `scripts/`, `tests/`, or `docs/`; the schema is new.
- `Explicit in code`: the current schema (`scripts/db/schema_sql.py`) still holds the legacy model: a `memories` table with a semantic/episodic type check, `pinned`, `memory_links`, and `memories_vec` (cited by the open issue `issues/20261125-103316_adrr010_agent-memory-schema.md`).
- `Explicit in code`: `scripts/agent/memory/` contains `extract.py`, `injection.py`, `retriever.py`, `rebuild_ops.py`, `jsonl_store.py`, `import_ops.py`, and `embedding_client.py`; the DB layer files named in Target Files all exist.
- `Documentation only`: Known Issues `SHARED-003` to `SHARED-005` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` record the schema mismatch and the undecided event categories and retention.

## Problem
Legacy Memory mixes Semantic and Episodic types, JSONL, pinning, manual writes, common scoring, and user-facing CRUD. The approved architecture allows only internally generated Episodic events in `session.sqlite`, treats FTS and Vector as derived, and does not use JSONL for recovery.

## Reason for Change
Schema, extraction, storage, retrieval, and recovery are tightly coupled; splitting them creates incompatible intermediate states (a new schema with old extraction, or a retriever reading legacy rows). They are one issue (Phase 2: same files, same acceptance, tested together). The legacy removal (issues/20261127-085936_amem008_legacy-memory-removal.md) depends on it.

## Implementation Intent
Create a minimal, explicit event model for reusable work experience. Keep canonical events and relations in SQLite, require FTS, allow optional Vector retrieval, and use archive-and-recreate for an old Session DB schema instead of in-place migration. Legacy rows and JSONL are not imported.

## Target Files or Areas
- `scripts/agent/memory/`
- `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/db/store_impl.py`
- `scripts/db/recovery.py`, `scripts/db/rotation.py`, `scripts/db/recovery_verification.py`, `scripts/db/session_consistency.py`
- `tests/agent/memory/`, `tests/db/`

## Required Changes
- Schema: inventory current Memory tables, triggers, FTS and Vector tables, and indexes; update the canonical DDL for events, relations, required FTS, and optional Vector structures; constrain event type, resolution state, and importance range; index repository, branch, event type, observation time, and source session, turn, and tool call; use UTC; archive the old DB and sidecars as one unit; do not import legacy rows or JSONL.
- Extraction: remove Semantic and generic Q&A extraction; implement the approved event types (`failure`, `resolution`, `review_finding`, `investigation_result`, `work_result`, `decision_history`); support Japanese and English evidence; evaluate role, neighboring messages, turn structure, and structured tool outcomes; do not store raw tool results, full logs, or full code; do not infer unknown root causes; allow several independently supported events per message; attach session, turn, and tool-call provenance; reject or redact secrets and unnecessary personal data; enforce a configurable per-session event limit.
- Save and relations: validate DTOs and enum values; normalize summary and content; validate embedding type, dimension, and finite values; save events and FTS state consistently; keep Vector optional and preserve FTS-only events when embedding fails; deduplicate exactly by normalized hash and by the approved near-duplicate rule; increment recurrence for the same failure; link resolutions and verification evidence to failures; report relation-write failure accurately; expose no manual-write or CRUD API.
- Retrieval and injection: implement Episodic-only FTS, optional Vector, and hybrid retrieval; exclude the current session; apply repository and branch as hard filters; rank by relevance, recency, resolution state, and recurrence; prefer unresolved failures only when relevant; limit injected events by the approved count and size; label them as past observation, not current policy; keep them out of conversation history; record FTS-only degraded mode safely.
- Backup and recovery: validate event-to-FTS, event-to-Vector, and relation integrity plus enum, importance, embedding dimension, and finite values; include Episodic data in SQLite Online Backup coverage; validate backups after creation, before activation, and after restore; keep internal FTS and Vector rebuild operations; recreate embeddings during Vector rebuild and keep the old index until the replacement completes; treat `/session export` as conversation export only.

## Constraints
- Do not implement in-place Session DB migration or restore Episodic Memory from JSONL.
- Do not make Vector availability a requirement for canonical persistence.
- Do not expose Episodic CRUD to users.
- Persisted-schema changes follow `rules/persisted-schema-change.md`.

## Acceptance Criteria
- Only Episodic events and relations are authoritative Memory data.
- FTS works without Vector support.
- General Q&A and unsupported inference are not persisted.
- Backup and restore preserve canonical Episodic data.
- Repository Context and Episodic Memory stay distinct in storage and prompts.

## Testing Expectations
Schema and fingerprint tests; archive-and-recreate; extraction in Japanese and English; generic Q&A exclusion; secret and personal-data exclusion; exact and near-duplicate; recurrence and relations; FTS-only and optional Vector; repository, branch, and current-session scoping; backup, restore, consistency, and rebuild. Run the validation sequence in `rules/toolchain.md`.

## Documentation Impact
Episodic data model, extraction boundaries, retrieval and degraded modes, and recovery behavior, handled in issues/20261127-085937_amem009_docs-manifests-sync.md. Follow `skills/DESIGN.md` (no field tables, no concrete values).

## Out of Scope
- Retention (issues/20261127-085933_amem005_episodic-retention-policy.md), budgeting and diagnostics (issues/20261127-085935_amem007_context-budget-diagnostics.md), and removal of legacy code (issues/20261127-085936_amem008_legacy-memory-removal.md).

## Dependencies
- Depends on issues/20261127-085929_amem001_memory-impact-cutover-map.md.
- Blocks issues/20261127-085933_amem005_episodic-retention-policy.md, issues/20261127-085935_amem007_context-budget-diagnostics.md, and issues/20261127-085936_amem008_legacy-memory-removal.md.
- Overlaps issues/20261125-103316_adrr010_agent-memory-schema.md (canonical Episodic schema and removal of `pinned`, the semantic type, and `memory_links`). Decide at plan time which issue owns the schema change so it is made once.

## Unresolved Questions
- `不明`: the approved near-duplicate rule, injection count and size limits, and per-session event limit.
- `不明`: the exact canonical Episodic schema where ADR-008 leaves it open (`SHARED-004`); the same question is open in `issues/20261125-103316_adrr010_agent-memory-schema.md`.
- `不明`: the session-end extraction call site and the embedding and Vector helper boundary (not re-read in full here).

## AI Implementation Instruction
Do not implement migration, JSONL import, or user-facing Memory operations. Stop and report where the approved text does not define a schema detail, limit, or rule; never invent it.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085931
- **Related target files**: `scripts/agent/memory/`, `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/db/store_impl.py`, `scripts/db/recovery.py`, `scripts/db/rotation.py`, `scripts/db/recovery_verification.py`, `scripts/db/session_consistency.py`
