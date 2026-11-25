# Remove the legacy memory model from the session schema

## Priority
Medium

## Summary
The session DDL and the Agent memory code still implement the old Semantic/Episodic model with pinning, links, and JSONL recovery, which ADR-008 (approved 2026-11-24) no longer permits. Implementation is partly blocked by undecided Episodic Memory details.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issue 017):
- Confirmed: `scripts/db/schema_sql.py` defines `memory_type ... CHECK(memory_type IN ('semantic','episodic'))` (`:102`), `pinned` (`:115`), `memory_links` (`:125`), and `memories_vec` (`:142`); `scripts/agent/memory/pin_ops.py` and `extract.py` exist; JSONL references remain in `scripts/db/store_protocols.py`, `scripts/agent/factory.py`, and `scripts/agent/config_section_builders.py`.
- This is Known Issue `SHARED-003` (implementation still follows the old model). `SHARED-004` and `SHARED-005` track what is not decided: Episodic event categories, retention, and per-event-type periods.
- Not verified: the `/memory` command routing and the full set of Agent memory tests (the note asked for them; they were not read in full here).

## Problem
The schema and code conflict with the approved memory model (Repository Context plus Episodic Memory only, no JSONL, no pinning, no user-facing memory operations).

## Reason for Change
ADR-008 INV-20 to INV-22 are Not verified until the old model is removed.

## Implementation Intent
Identify the canonical Episodic Memory schema from the approved ADR text, remove obsolete columns, tables, comments, JSONL archive and rebuild assumptions, and `/memory` paths, and ensure Repository Context is never copied into persistent memory or indexes.

## Target Files or Areas
- `scripts/db/schema_sql.py`, `scripts/db/store_protocols.py`
- `scripts/agent/memory/`, `scripts/agent/factory.py`, `scripts/agent/config_section_builders.py`, the memory command routing
- `docs/23_agent/agent_11_01_memory-overview-and-modes.md`, ADR-008 evidence
- `tests/db/`, `tests/agent/`

## Required Changes
- Fix the canonical Episodic schema from the approved decisions; remove `pinned`, the semantic type, `memory_links`, and obsolete indexes only as the approved model dictates.
- Remove JSONL archive and `/memory rebuild` assumptions and the `/memory` command path; retire the obsolete configuration keys.
- Add schema-shape, no-JSONL, no-user-command, and Repository Context non-persistence tests; update the Known Issues and ADR evidence.

## Constraints
- Do not decide Episodic event categories or retention (`SHARED-004`, `SHARED-005`); do not invent configuration keys.
- A session schema change recreates the store on mismatch (ADR-008 Decision Detail 22); follow `rules/persisted-schema-change.md`.

## Acceptance Criteria
- The session schema matches the approved model; no JSONL recovery or `/memory` dependency remains.
- Repository Context is not persisted into Episodic Memory; schema fingerprint and startup tests pass.

## Testing Expectations
Schema-shape, no-JSONL, no-command, and non-persistence tests; schema fingerprint and startup tests; ADR checks; whole suite.

## Documentation Impact
Agent memory documents, ADR-008 evidence, and the governance Known Issues.

## Out of Scope
- Episodic retention and event categories; EventBus `events.jsonl` (issues/20261125-103311_adrr005_eventbus-jsonl-removal.md).

## Dependencies
- N/A: none open as issues; blocked in part by the maintainer decisions tracked under `SHARED-004` and `SHARED-005`.

## Unresolved Questions
- `不明`: the exact canonical Episodic schema where the approved text leaves it open (`SHARED-004`).
- `不明`: the full list of memory command routes and tests (to be read at the start of the plan).

## AI Implementation Instruction
Stop and report where the approved ADR text does not define the Episodic schema; do not invent decisions.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103316
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/agent/memory/pin_ops.py`, `scripts/agent/factory.py`, `docs/23_agent/agent_11_01_memory-overview-and-modes.md`
