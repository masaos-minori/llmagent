# Define the database data lifecycle in ADR-008

## Priority
High

## Summary
ADR-008 does not define, for each database, what happens to data on a schema change, how long data is kept, which store is canonical, or which databases are in scope. Record these rules before any schema-changing work.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H08`; merged from ADRCHK-H09, H19, M11, M12, L01, L10 (review findings H4, M15, M16, N7, N29, N48)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- Schema changes lose data: ADR-008 and the schema-fingerprint plan archive and recreate any database whose fingerprint does not match, while ADR-006 says EventBus events must not be lost and `scripts/db/schema_sql.py` says session data must not be recreated silently. Production workflow and EventBus databases have extra tables, so the next deployment will refuse to start. Unprocessed events, tasks, and conversation memory would be lost.
- No retention is defined: ADR-008 INV-09 requires a retention period for each database, but EventBus never deletes events and keeps done `dlq_outbox` rows permanently.
- The canonical memory store is unclear: `MemoryEntry` is stored in JSONL and indexed in SQLite, while ADR-008 treats the session `memories` table as canonical and omits `memories_fts`, `memories_vec`, `memory_links`, and the JSONL backup.
- Scope and inventory are wrong: ADR-008 and ARCH-003 say four databases while the plans cover more (workflow, eventbus, mcp_dedup, mdq, session, rag); Decision #4 includes `dlq_outbox` but INV-04 does not; Implementation References omit some tables.
- References and terms are wrong: the operator-restore glossary cites the wrong Decision Details, the Summary range omits the last decision, and ADR-001 says DB schema version where ADR-008 uses fingerprints.

## Implementation Intent
- ADR-008 lists, for each in-scope database, the schema-mismatch rule (recreate, drain then recreate, or export then recreate), the retention rule, and the canonical and derived stores.
- ADR-006 and the code comments refer to these rules, and the table inventory matches the DDL sources.

## Target Files or Areas
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md (terminology only)
- `docs/23_agent/agent_09_01_data-layer-session-db.md`
- config/adr_authority.toml (ARCH-003)
- scripts/db/schema_sql.py and scripts/eventbus/schema.sql (comments only)
- The DB schema-migration-and-scaling guide (`db_03_architecture_and_schema-migration-and-scaling.md`, directory unknown)

## Required Changes
- (no decision needed) Build the table inventory from `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`, and `scripts/mcp_servers/mdq/db_schema.py`.
- (no decision needed) Fix the decision references in ADR-008 and the terminology in ADR-001.
- (decision) Decide whether mcp_dedup and mdq are in ADR-008 scope, and set the title.
- (decision) Decide the schema-mismatch rule for each database.
- (decision) Decide retention for events, `consumer_delivery`, and `dlq_outbox`, or record unbounded growth as an accepted risk.
- (decision) Decide the canonical memory store and its derived tables.
- Update ADR-006, `agent_09_01`, ARCH-003, and the comments after the decisions.

## Constraints
- Do not choose the rules; prepare evidence and options only.
- A change to any DDL changes the schema fingerprint; no DDL change is part of this issue.
- Run `uv run python tools/check_db_separation.py` after any change near schema comments.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- ADR-008 has one rule for each in-scope database for mismatch, retention, and the canonical store.
- ADR-006 no longer claims no event loss without that rule as a condition.
- ARCH-003 and ADR-008 agree on the set of databases.

## Testing Expectations
Documentation-only plus comments. Run `tools/check_db_separation.py`, the ADR checkers, and the docs checkers listed in `routing.md`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-008, ADR-006, the session data-layer guide, and the migration guide: mismatch rule, retention, canonical store, scope.

## Out of Scope
- Any DDL change.
- Running or planning the deployment.

## Dependencies
- `issues/20261117-123009_adrchk009_plan-code-reconcile.md` (Phase 7 of the schema-fingerprint plan) is blocked until this decision is recorded.
- `issues/20261117-123017_adrchk017_eventbus-task-supervision.md` schema task is blocked until this decision is recorded.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the approval record for ADR-008 decision changes.

## Unresolved Questions
- The current memory write path is `不明`: needs `scripts/agent/memory/jsonl_store.py` and `scripts/agent/memory/import_ops.py`.
- The location of the migration-and-scaling guide is `不明` (probably under `docs/41_db/`).

## AI Implementation Instruction
- Do not choose the rules. Prepare evidence and options only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123008
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md (terminology only)`; `docs/23_agent/agent_09_01_data-layer-session-db.md`; `config/adr_authority.toml (ARCH-003)`; scripts/db/schema_sql.py and scripts/eventbus/schema.sql (comments only); The DB schema-migration-and-scaling guide (`db_03_architecture_and_schema-migration-and-scaling.md`, directory unknown)
