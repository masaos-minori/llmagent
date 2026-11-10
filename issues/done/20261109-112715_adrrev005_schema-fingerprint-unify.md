# Unify SQLite schema validation on exact DDL fingerprint matching and remove leftover schema-version mechanisms

## Priority
High

## Summary
Extend the existing exact-shape fingerprint check (today implemented only for eventbus.sqlite) to every SQLite database, and remove the other drift-detection mechanisms (legacy marker tables, `user_version` stamping, partial structure checks) so that one mechanism enforces the "current schema only, never migrate" policy.

## Background
- Source: `memo-issue.md` items H-05, M-10, and the session.sqlite part of M-09, re-checked against current source on 2026-11-09. Several memo claims are stale; they are listed below so the plan starts from current facts.
- `Explicit in code`: `scripts/shared/eventbus_schema_fingerprint.py` builds a structural fingerprint (tables, views, columns, indexes with partial predicates, table-level constraints, foreign keys, triggers) from `scripts/eventbus/schema.sql` and compares it to a target connection; it is used by `scripts/eventbus/schema.py`, `scripts/db/create_schema.py`, and `scripts/db/recovery_drill.py`. It composes with a `PRAGMA user_version` gate.
- `Explicit in code`: `scripts/db/recovery_drill.py` still detects legacy marker tables (`schema_migrations`, `workflow_schema_version`) in a restored copy; `scripts/eventbus/schema.sql` stamps `PRAGMA user_version`; `scripts/db/schema_sql.py` and `scripts/db/create_schema.py` also read the stamp.
- `Needs confirmation`: validation applied today to workflow, mdq, session, rag, and mcp_dedup databases. The memo states that workflow checks only tables and columns, mdq migrates on every startup (ADR-008) while `db_03` says create-only, session detects only a missing schema, and rag rejects unknown schemas. Archived issues `rmwfmig`, `rmebmig`, `rmmdqmig` (all under `issues/done/`) removed the workflow, eventbus, and mdq migrations, so the mdq claim is probably stale. `scripts/shared/mcp_dedup.py` creates `tool_call_state` with `CREATE TABLE IF NOT EXISTS`.
- Memo claim refuted by current source: "`tool_call_state` and `classify_stale_pending` have no writer". `tool_call_state_ops.py` has writers (`record_tool_call`, `finalize_tool_call`) called from `scripts/agent/workflow/state_store.py`, and `classify_stale_pending` is called by `scripts/agent/workflow/workflow_engine.py`. The precondition issue the memo cites now lives at `issues/done/20261031-175803_toolstate001_tool-call-state-producer.md` with its plan `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md`, which indicates a producer was implemented. Related: `issues/done/20261107-203223_wfaudit010_snapshots-never-written.md`.
- `Explicit in documentation`: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` state that `execution_snapshots` and `tool_call_state.snapshot_id` are retired and "a legacy database may still contain the empty table"; `scripts/` no longer references `execution_snapshots`, only tests do.
- `Needs confirmation`: the ADR-001 rule that reclaims lease-less legacy rows after a timeout (`scripts/agent/workflow/` lease handling; `wflease001` is cited in `workflow_engine.py`).
- `Documentation only`: `db_07` states that no database uses version stamping, while `db_01` mentions `user_version`.

## Problem
- Drift detection differs per database, and the policy "only the current schema is accepted; nothing is migrated" is enforced by a full shape comparison for eventbus only. An old-shape workflow, session, mdq, or mcp_dedup database can pass startup if its tables and columns match even when CHECK constraints, indexes, or triggers differ (`Needs confirmation` per database).
- Four mechanisms coexist (marker tables, `user_version`, the shape fingerprint, existence-only checks), each detecting a different subset of drift.
- Documentation contradicts itself on version stamping and on mdq migration, so operators cannot tell which check protects which file.

## Reason for Change
- A mismatched schema can accept invalid state values silently, which conflicts with ADR-004 INV-05 (data-integrity failures are Fail-Fast).
- Timing: the mcp_dedup, ADR-008 recovery, and governance-ledger issues in this batch depend on a single validation mechanism.

## Implementation Intent
- One mechanism for every SQLite database: compare the live schema (tables, columns, types, constraints, indexes, triggers) with the canonical DDL, and on any difference refuse to start with an explicit error that tells the operator to archive and recreate. Never migrate and never modify automatically.
- Generalize the existing eventbus fingerprint validator (or its approach) rather than writing a second one; keep `shared` a leaf module with standard-library imports only.
- Only objects that production writes and reads exist in the canonical DDL.

## Target Files or Areas
- `scripts/shared/eventbus_schema_fingerprint.py` (generalization or successor), `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/recovery_drill.py`, `scripts/db/helper.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`
- `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/shared/mcp_dedup.py` (schema creation and validation only)
- Startup paths of the Agent, RAG, and MDQ components that open their databases (`Unknown`: exact modules)
- Tests: `tests/db/test_create_schema.py`, `tests/deploy/test_required_workflow_tables_parity.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/db/test_db_recovery.py`
- Docs: ADR-001, ADR-008, `docs/41_db/db_01_*.md`, `db_02_*.md`, `db_03_*.md`, `db_03_07_*.md`, `db_07_*.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`

## Required Changes
- Confirm per database (workflow, eventbus, mcp_dedup, mdq, session, rag) the validation that runs today, and record it before changing code.
- Implement a shared schema fingerprint check and apply it to every SQLite database listed above.
- Remove legacy-marker detection, `user_version` stamping and checks, any remaining migration code, and the reclaiming of lease-less legacy rows (ADR-001), where confirmed present.
- Remove leftover `execution_snapshots` / `snapshot_id` handling that exists only for legacy databases, where confirmed present.
- Make every recovery path recreate from the canonical DDL.
- Update ADR-001, ADR-008, `db_01`, `db_02`, `db_03`, `db_03_07`, `db_07`, and `agent_09_01` so that they describe one validation mechanism.

## Constraints
- Current-only policy: no migration, no automatic repair; the error message must tell the operator to archive and recreate.
- ADR-008 4DB separation and `tools/check_db_separation.py` must keep passing.
- `shared` must remain a leaf module (`.importlinter`).
- Keep sqlite-vec virtual tables (rag, session) out of false mismatches (`Needs confirmation`: how the fingerprint should treat vec virtual tables and shadow tables).
- Do not remove `tool_call_state` or `classify_stale_pending`: they have a writer; the memo's deletion task does not apply unless the plan finds an unused part.

## Acceptance Criteria
- For each database, test fixtures with a missing CHECK constraint, an extra legacy table, an extra column, and a missing index all fail startup with an explicit error.
- No migration, `user_version`, or legacy-marker code remains (`rg -n "user_version|schema_migrations|workflow_schema_version" scripts/` returns nothing outside a named, justified exception).
- No document claims a validation mechanism other than fingerprint matching.
- `uv run python tools/check_db_separation.py` and `check_docs_consistency.py --domain db` pass.

## Testing Expectations
- New fixture-based tests per database for the four drift cases above; update `tests/db/`, `tests/deploy/`, `tests/agent/workflow/`.
- Impact-radius check before changing shared helpers (`rules/toolchain.md`).
- Full validation sequence, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, and the documentation checkers.

## Documentation Impact
- ADR-001 and ADR-008 and the DB documents must describe a single validation mechanism, the failure behavior (refuse to start, archive and recreate), and the removal of legacy handling. Record anything unconfirmed in `governance_03` Needs Confirmation.

## Out of Scope
- Defining the mcp_dedup.sqlite system-of-record decision (mcp_dedup issue in this batch).
- Manual recovery procedure and backup verification (ADR-008 alignment issue in this batch).
- Changing any table's business schema.

## Dependencies
- Depends on: none. The memo's precondition (the `tool_call_state` producer question in `issues/20261031-175803_toolstate001_tool-call-state-producer.md`) is already answered by the archived issue and plan under `issues/done/` and `plans/done/`.
- Blocks: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md` (mcp_dedup ownership) and `issues/20261109-112922_adrrev009_adr008-recovery-align.md` (ADR-008 alignment).
- Related, recently archived (re-verify against current source): `rmwfmig_remove-the-workflow.sqlite-incremental-migrations`, `rmebmig_remove-the-eventbus.sqlite-schema-migrations`, `rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild`, `wfaudit010_snapshots-never-written`, and `compat001` / `compat006` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: the validation currently applied per database (see Background); the plan must start with this inventory.
- `Needs confirmation`: whether any part of `tool_call_state` / `classify_stale_pending` is unused today.
- `Needs confirmation`: how a shape fingerprint should treat sqlite-vec virtual tables in rag.sqlite and session.sqlite.
- Maintainer decision: whether a legacy workflow database that still carries the retired `execution_snapshots` table must now fail startup (the documents say it is harmless; exact matching would reject it).

## AI Implementation Instruction
- Start from the verified inventory; do not delete `tool_call_state` or related helpers on the memo's authority.
- Reuse the existing eventbus fingerprint design; do not add a parallel validator.
- Never add migration or auto-repair code; fail with an explicit error.
- Keep changes to schema validation and its documentation; do not alter business schemas or unrelated modules.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112715
- **Related target files**: `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/recovery_drill.py`, `scripts/db/helper.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/shared/mcp_dedup.py`, `docs/41_db/`, `docs/23_agent/agent_09_01_data-layer-session-db.md`
