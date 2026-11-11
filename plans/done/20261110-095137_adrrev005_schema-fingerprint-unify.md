## Goal
- Enforce the "current schema only, never migrate" policy on every SQLite database (workflow, eventbus, mcp_dedup, mdq, session, rag) with one mechanism, an exact DDL fingerprint comparison in a generalized `scripts/shared/schema_fingerprint.py`, and remove the other drift mechanisms (`user_version` stamping, legacy marker-table detection, existence-only table checks, the lease-less legacy recovery rule).

## Priority
High

## Scope
- **In-Scope**: Generalize the eventbus fingerprint into `scripts/shared/schema_fingerprint.py` (canonical DDL as input, stdlib only) and delete the eventbus-named module; apply it on creation/open/startup/deploy for all six databases with an explicit archive-and-recreate error; remove `PRAGMA user_version` stamping and checks, marker-table detectors, and the lease-less legacy rule; new per-database drift tests; update the ADRs, DB documents, and deploy scripts.
- **Out-of-Scope**: The mcp_dedup.sqlite system-of-record decision (`issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`); manual recovery and backup verification (`issues/20261109-112922_adrrev009_adr008-recovery-align.md`); any table's business schema; `scripts/shared/execution_snapshot.py`'s read of the file-header `user_version` for the snapshot (observability only, named exception, see Design).
- **Dependencies**: Depends on none by the Issue; sequencing: written against the state after `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` (it removes the Agent-side eventbus branches of `scripts/db/` and adds `scripts/eventbus/db_tools.py`); after that plan lands, `scripts/eventbus/db_tools.py` and `tests/eventbus/test_eventbus_db_tools.py` must be added to this Plan through `tools/amend_plan.py` (fallout, they import the module this Plan renames). Blocks `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md` and `issues/20261109-112922_adrrev009_adr008-recovery-align.md`.
  - **Depends on**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md | phase 3 | this Plan's `scripts/db/` rows assume the eventbus branches are already removed

## Background
- Source: `memo-issue.md` items H-05, M-10, session part of M-09, re-verified on 2026-11-10.
- **Verified per-database inventory (the Issue's required first step)**:
  - workflow.sqlite: `check_workflow_schema` (`scripts/agent/services/workflow_schema.py:48-120`) checks the five required tables with named columns and refuses databases carrying `schema_migrations`/`workflow_schema_version`; constraints, indexes, and triggers are not compared; `deploy/setup_services.sh:55-57` re-checks table names only; `deploy/init_db.sh:72` repeats the marker query.
  - eventbus.sqlite: exact fingerprint plus a `PRAGMA user_version` gate (`scripts/shared/eventbus_schema_fingerprint.py`, `scripts/eventbus/schema.py:29-70`, `deploy/init_db.sh:89-117`); `schema.sql:65` stamps version 6.
  - mcp_dedup.sqlite: `CREATE TABLE IF NOT EXISTS` and `PRAGMA user_version = 1` stamping on every open (`scripts/shared/mcp_dedup.py:48-62,243-245`); an old-shape table passes silently.
  - mdq.sqlite: `CREATE TABLE IF NOT EXISTS` only (`scripts/mcp_servers/mdq/db_schema.py:23-99`); health checks table existence (`health_check.py:65-67`); no migration code remains (consistent with the archived `rmmdqmig`), so the Issue's mdq-migration claim is stale.
  - session.sqlite and rag.sqlite: existence-only `required_tables` checks (`scripts/db/session_consistency.py:58-117`, `scripts/db/rag_consistency_queries.py:216-224`) and a one-table domain identity check (`scripts/db/recovery.py:151-170`).
- `Confirmed by repository evidence` (production state, read-only inspection of `/opt/llm/db` on 2026-11-10): `workflow.sqlite` carries `schema_migrations` and `workflow_schema_version` and lacks `tool_call_state`; `eventbus.sqlite` has `user_version 0`; `rag.sqlite` has no `rag_corpus_meta`; `mdq.sqlite` has an extra `chunk_summaries` table. The deployed databases are therefore older than the current schema and the current gates would already refuse the workflow and eventbus files.
- `Refuted`: the memo's "`tool_call_state` has no writer". Two different tables share the name: workflow.sqlite's `tool_call_state` (columns `idempotency_key`, `task_id`, ...; `scripts/db/schema_sql.py:229`, writers in `scripts/agent/workflow/`) and mcp_dedup.sqlite's (columns `key`, `args_hash`, `snapshot_json`, ...; `scripts/shared/mcp_dedup.py:48`). The Issue does not distinguish them; neither is deleted here.
- `Confirmed by repository evidence`: `execution_snapshots` and `snapshot_id` no longer appear under `scripts/` (only tests and docs), so there is no code to remove; only the document statement "a legacy database may still contain the empty table" (`db_03_07...md:29,78-80`) conflicts with exact matching.
- `Confirmed by repository evidence`: the lease-less legacy age rule exists (`scripts/agent/workflow/state_store.py:37,231-290,383,432`), but the sole writer of `attempts` (`scripts/agent/workflow/idempotency_ops.py:64-67`) always stamps `owner_id` and `lease_expires_at`, so lease-less rows exist only in legacy databases; removing the rule needs no DDL change (the nullable columns stay).
- `Refuted`/narrowed (Issue target list): `scripts/db/helper.py` has no schema-validation code and is not a target; the targets the Issue missed are `scripts/agent/services/workflow_schema.py`, `scripts/db/session_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/mcp_servers/mdq/db_schema.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `tools/generate_reference_table.py` (requires a `PRAGMA user_version` stamp in `schema.sql`, line 562), `tools/check_compat_shims.py`, `registry/manifests/db_schema_versions.yaml`, and `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:74` (allows the eventbus fingerprint module by name). `docs/23_agent/agent_09_01_data-layer-session-db.md` has no validation text to update (no match), so it is not a target.
- `Documentation only`: `db_07` says no database uses version stamping while the code stamps eventbus and mcp_dedup; the rows below align the documents with the one mechanism.

## Problem
- Drift detection differs per database: only eventbus compares the full shape, so an old-shape workflow, session, rag, mdq, or mcp_dedup database can start when its table and column names match; four mechanisms coexist; documents contradict each other on version stamping.
- The deployed `/opt/llm/db` files already differ from the current schema (see Background), so any generalized gate will refuse them until the operator archives and recreates them.

## Reason for Change
- A mismatched schema can accept invalid state silently, contrary to ADR-004 INV-05 (data-integrity failures are Fail-Fast); the mcp_dedup, ADR-008 recovery, and governance-ledger Issues depend on one mechanism. No external deadline.

## Implementation Intent
- One mechanism for every database: compare the live schema with the canonical DDL; on any difference refuse to start with an explicit error telling the operator to archive and recreate; never migrate or repair automatically.
- Generalize the existing eventbus fingerprint design rather than writing a second validator; `shared` stays a leaf (stdlib only); canonical DDL text is passed in by callers (`scripts/db/schema_sql.py` for workflow, session, rag; `schema.sql` for eventbus; the module constants for mcp_dedup and mdq).
- sqlite-vec virtual tables and their shadow tables are excluded from the shape comparison and only required to exist by name (UNK-01).

## Requirements
- `REQ-001`: Keep the verified per-database inventory (Background) as the baseline and re-verify it at the start of implementation (Phase 1) before code changes.
- `REQ-002`: Provide `scripts/shared/schema_fingerprint.py` (canonical DDL as input; tables, views, columns, indexes with partial predicates, table-level constraints, foreign keys, triggers; stdlib only; vec virtual and shadow tables handled by name) and remove `scripts/shared/eventbus_schema_fingerprint.py` with every caller moved.
- `REQ-003`: Apply it to workflow, eventbus, mcp_dedup, mdq, session, and rag at creation/open, at Agent and service startup, and in `deploy/init_db.sh`/`deploy/setup_services.sh`; refusal is an explicit error naming archive-and-recreate and leaves the file unchanged.
- `REQ-004`: Remove `PRAGMA user_version` stamping and checks (including the `schema.sql` stamp and the generator's requirement for it), legacy marker-table detection, the lease-less legacy recovery rule, and existence-only checks; no migration or auto-repair code is added.
- `REQ-005`: Tests per database (workflow, eventbus, mcp_dedup, mdq, session, rag) show that a missing CHECK constraint, an extra legacy table, an extra column, and a missing index each fail startup with the explicit error.
- `REQ-006`: Update ADR-001, ADR-008, the DB, deployment, agent, EventBus, and MCP documents to describe one validation mechanism and its failure behavior.
- `REQ-007`: Verification: `rg -n "user_version|schema_migrations|workflow_schema_version" scripts/` returns only the named exception, `tools/check_db_separation.py` and `check_docs_consistency.py --domain db` pass.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-10 (fallout): added scripts/eventbus/db_tools.py — imports shared.eventbus_schema_fingerprint which this Plan deletes; import breaks on deletion
Amended 2026-11-10 (fallout): added tests/eventbus/test_eventbus_db_tools.py — asserts the user_version refusal (lines 82-103) that this Plan removes; breaks without update

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/schema_fingerprint.py` | Create: New file: generalized fingerprint (tables, views, columns, indexes with predicates, table constraints, foreign keys, triggers) that takes the canonical DDL text | New file: generalized fingerprint (tables, views, columns, indexes with predicates, table constraints, foreign keys, triggers) that takes the canonical DDL text; stdlib only | REQ-002 / AC-02 | Design source: `scripts/shared/eventbus_schema_fingerprint.py:36-210` (`apply_schema_in_memory`, `build_fingerprint`, `assert_matches`) (checked in Step 3) | `tests/shared/test_schema_fingerprint.py` | Verified |
| `scripts/shared/eventbus_schema_fingerprint.py` | Delete: Delete after its callers move to the generalized module | Delete after its callers move to the generalized module; no compatibility shim | REQ-002, REQ-004 / AC-02, AC-04 | `eventbus_schema_fingerprint.py:7,21,42,213-222` (version gate); importers `scripts/eventbus/schema.py`, `deploy/init_db.sh`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:74` (checked in Step 3) | `tests/shared/test_schema_fingerprint.py` | Verified |
| `scripts/eventbus/schema.py` | Modify: Validate an existing database with the generalized fingerprint only | Validate an existing database with the generalized fingerprint only; drop the `user_version` read and stamp comparison | REQ-003, REQ-004 / AC-03, AC-04 | `scripts/eventbus/schema.py:29-70` (checked in Step 3) | `tests/eventbus/test_eventbus_startup.py`, `tests/eventbus/test_eventbus_schema_version.py` | Verified |
| `scripts/eventbus/schema.sql` | Modify: Remove the `PRAGMA user_version = 6` stamp and its comment (persisted-schema checklist applies | Remove the `PRAGMA user_version = 6` stamp and its comment (persisted-schema checklist applies; the DDL objects are unchanged) | REQ-004 / AC-04 | `scripts/eventbus/schema.sql:63-65` (checked in Step 3) | `tests/eventbus/test_eventbus_startup.py` | Verified |
| `scripts/db/schema_sql.py` | Modify: Expose the canonical DDL of every database through one accessor family | Expose the canonical DDL of every database through one accessor family; remove the eventbus `user_version` reader (`eventbus_schema_version`, if plan 002 has not already removed it) | REQ-002, REQ-004 / AC-02, AC-04 | `scripts/db/schema_sql.py:250-264` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/db/create_schema.py` | Modify: Validate-first for every database: a fresh file receives the canonical DDL, an existing one is checked by fingerprint and refused unchanged on any difference | Validate-first for every database: a fresh file receives the canonical DDL, an existing one is checked by fingerprint and refused unchanged on any difference | REQ-003, REQ-004 / AC-03, AC-04 | `scripts/db/create_schema.py:89-131` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/db/recovery_drill.py` | Modify: Replace the legacy marker-table detector with the fingerprint check for each domain | Replace the legacy marker-table detector with the fingerprint check for each domain | REQ-003, REQ-004 / AC-03, AC-04 | `scripts/db/recovery_drill.py:56-76,238` (checked in Step 3) | `tests/db/test_recovery_drill.py` | Verified |
| `scripts/db/session_consistency.py` | Modify: Replace the existence-only `required_tables` checks with the fingerprint check for session.sqlite | Replace the existence-only `required_tables` checks with the fingerprint check for session.sqlite | REQ-003 / AC-03 | `scripts/db/session_consistency.py:58-117` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/db/rag_consistency_queries.py` | Modify: Replace the existence-only `required_tables` check with the fingerprint check for rag.sqlite | Replace the existence-only `required_tables` check with the fingerprint check for rag.sqlite | REQ-003 / AC-03 | `scripts/db/rag_consistency_queries.py:216-224` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/agent/services/workflow_schema.py` | Modify: Replace `REQUIRED_WORKFLOW_TABLES` and the marker-table refusal with the fingerprint check | Replace `REQUIRED_WORKFLOW_TABLES` and the marker-table refusal with the fingerprint check; keep the refusal text that tells the operator to archive and recreate | REQ-003, REQ-004 / AC-03, AC-04 | `scripts/agent/services/workflow_schema.py:48-120` (checked in Step 3) | `tests/agent/test_repl_health.py`, `tests/agent/test_startup_workflow_preflight.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Modify: Remove the lease-less legacy age rule (`_LEGACY_STALE_AGE_SEC`, `legacy_recovered`) | Remove the lease-less legacy age rule (`_LEGACY_STALE_AGE_SEC`, `legacy_recovered`); the only attempt writer always stamps a lease | REQ-004 / AC-04 | `scripts/agent/workflow/state_store.py:37,231-290,383,432`; sole insert `scripts/agent/workflow/idempotency_ops.py:64-67` stamps `owner_id`, `lease_expires_at` (checked in Step 3) | `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/shared/mcp_dedup.py` | Modify: Replace `CREATE TABLE IF NOT EXISTS` plus `PRAGMA user_version` stamping with create-when-absent and fingerprint validation | Replace `CREATE TABLE IF NOT EXISTS` plus `PRAGMA user_version` stamping with create-when-absent and fingerprint validation | REQ-003, REQ-004 / AC-03, AC-04 | `scripts/shared/mcp_dedup.py:48-62,243-245` (checked in Step 3) | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/mcp_servers/mdq/db_schema.py` | Modify: Validate an existing mdq.sqlite by fingerprint and refuse a mismatch with the archive-and-recreate message | Validate an existing mdq.sqlite by fingerprint and refuse a mismatch with the archive-and-recreate message | REQ-003 / AC-03 | `scripts/mcp_servers/mdq/db_schema.py:23-99`; table-existence health check `health_check.py:65-67` (checked in Step 3) | `tests/mcp_servers/mdq` | Verified |
| `tools/generate_reference_table.py` | Modify: Stop requiring a `PRAGMA user_version` stamp when generating the schema-version reference | Stop requiring a `PRAGMA user_version` stamp when generating the schema-version reference | REQ-004 / AC-04 | `tools/generate_reference_table.py:73,562` (checked in Step 3) | `tests/tools/test_generate_reference_table.py` | Verified |
| `tools/check_compat_shims.py` | Modify: Update the marker-table exception comments once the detectors are gone | Update the marker-table exception comments once the detectors are gone | REQ-004 / AC-04 | `tools/check_compat_shims.py:128-132,443-449` (checked in Step 3) | `uv run python tools/check_compat_shims.py` | Verified |
| `deploy/init_db.sh` | Modify: Replace the marker-table query and the eventbus-specific gate with the generalized per-database fingerprint gate | Replace the marker-table query and the eventbus-specific gate with the generalized per-database fingerprint gate | REQ-003, REQ-004 / AC-03, AC-04 | `deploy/init_db.sh:72` (marker query), `:89-117` (eventbus gate importing `shared.eventbus_schema_fingerprint`) (checked in Step 3) | `tests/deploy/test_init_db_schema_gate.py`, `tests/deploy/test_init_db_eventbus_schema.py` | Verified |
| `deploy/setup_services.sh` | Modify: Replace the table-name-only `REQUIRED_WORKFLOW_TABLES` check with the fingerprint gate | Replace the table-name-only `REQUIRED_WORKFLOW_TABLES` check with the fingerprint gate | REQ-003 / AC-03 | `deploy/setup_services.sh:55-57` (checked in Step 3) | `tests/deploy/test_required_workflow_tables_parity.py` | Verified |
| `registry/manifests/db_schema_versions.yaml` | Modify: Regenerate (not hand-edited) once the generator no longer reads a stamp | Regenerate (not hand-edited) once the generator no longer reads a stamp | REQ-004 / AC-04 | `registry/manifests/db_schema_versions.yaml` (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `tests/shared/test_schema_fingerprint.py` | Create: New file: fingerprint unit tests (missing CHECK, extra table, extra column, missing index, trigger, vec virtual table treatment) | New file: fingerprint unit tests (missing CHECK, extra table, extra column, missing index, trigger, vec virtual table treatment) | REQ-002, REQ-005 / AC-02, AC-05 | tests directory `tests/shared/` exists (checked in Step 3) | `uv run pytest tests/shared/test_schema_fingerprint.py -v` | Verified |
| `tests/db/test_schema_validation_per_database.py` | Create: New file: for each of workflow, eventbus, mcp_dedup, mdq, session, rag the four drift cases fail with an explicit archive-and-recreate error | New file: for each of workflow, eventbus, mcp_dedup, mdq, session, rag the four drift cases fail with an explicit archive-and-recreate error | REQ-003, REQ-005 / AC-03, AC-05 | tests directory `tests/db/` exists (checked in Step 3) | `uv run pytest tests/db/test_schema_validation_per_database.py -v` | Verified |
| `tests/db/test_create_schema.py` | Modify: Replace the eventbus `user_version` cases with fingerprint cases | Replace the eventbus `user_version` cases with fingerprint cases | REQ-003, REQ-004 / AC-03, AC-04 | 50 hits (rg count) (checked in Step 3) | `uv run pytest tests/db/test_create_schema.py -v` | Verified |
| `tests/agent/test_repl_health.py` | Modify: Replace table-list and marker-table cases with fingerprint cases | Replace table-list and marker-table cases with fingerprint cases | REQ-003, REQ-004 / AC-03, AC-04 | 30 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_repl_health.py -v` | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Modify: Delete the `user_version` cases | Delete the `user_version` cases; keep or move the shape-refusal cases | REQ-004 / AC-04 | 18 hits (rg count) (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_schema_version.py -v` | Verified |
| `tests/eventbus/test_eventbus_startup.py` | Modify: Replace the stamp assertions with fingerprint assertions | Replace the stamp assertions with fingerprint assertions | REQ-003, REQ-004 / AC-03, AC-04 | 6 hits (rg count) (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Verified |
| `tests/deploy/test_required_workflow_tables_parity.py` | Modify: Re-express the table parity check through the canonical DDL | Re-express the table parity check through the canonical DDL | REQ-003 / AC-03 | 8 hits (rg count) (checked in Step 3) | `uv run pytest tests/deploy/test_required_workflow_tables_parity.py -v` | Verified |
| `tests/deploy/test_init_db_schema_gate.py` | Modify: Cover the generalized gate and drop the marker-table cases | Cover the generalized gate and drop the marker-table cases | REQ-003, REQ-004 / AC-03, AC-04 | 8 hits (rg count) (checked in Step 3) | `uv run pytest tests/deploy/test_init_db_schema_gate.py -v` | Verified |
| `tests/deploy/test_init_db_eventbus_schema.py` | Modify: Follow the generalized gate | Follow the generalized gate | REQ-003 / AC-03 | 1 hit (rg count) (checked in Step 3) | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` | Verified |
| `tests/db/test_recovery_drill.py` | Modify: Replace the marker-table finding with the fingerprint finding | Replace the marker-table finding with the fingerprint finding | REQ-003, REQ-004 / AC-03, AC-04 | 7 hits (rg count) (checked in Step 3) | `uv run pytest tests/db/test_recovery_drill.py -v` | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify: Remove legacy lease-less recovery expectations | Remove legacy lease-less recovery expectations | REQ-004 / AC-04 | 6 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` | Verified |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Modify: Delete the legacy age-rule cases | Delete the legacy age-rule cases | REQ-004 / AC-04 | `test_stale_recovery_lease.py:30,255-276` (checked in Step 3) | `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -v` | Verified |
| `tests/agent/test_startup_workflow_preflight.py` | Modify: Follow the `check_workflow_schema` change | Follow the `check_workflow_schema` change | REQ-003 / AC-03 | 5 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_workflow_preflight.py -v` | Verified |
| `tests/shared/test_mcp_dedup.py` | Modify: Replace stamp expectations with fingerprint refusal cases | Replace stamp expectations with fingerprint refusal cases | REQ-003, REQ-004 / AC-03, AC-04 | 1 hit (rg count); `user_version` fixture at line 30 (checked in Step 3) | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Verified |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Modify: Replace the allowed-import entry `eventbus_schema_fingerprint.py` with the new module name | Replace the allowed-import entry `eventbus_schema_fingerprint.py` with the new module name | REQ-002 / AC-02 | `test_mdq_rag_boundary.py:74` (checked in Step 3) | `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -v` | Verified |
| `tests/tools/test_generate_reference_table.py` | Modify: Drop the `PRAGMA user_version` fixture lines | Drop the `PRAGMA user_version` fixture lines | REQ-004 / AC-04 | `test_generate_reference_table.py:138,377` (checked in Step 3) | `uv run pytest tests/tools/test_generate_reference_table.py -v` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify: Remove the lease-less legacy-row statement | Remove the lease-less legacy-row statement; describe the single validation mechanism | REQ-006 / AC-06 | `adr_02_02_001...md:74` (INV-07 lease text) (checked in Step 3) | `check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify: Describe fingerprint matching as the one drift check and the recreate policy for every database | Describe fingerprint matching as the one drift check and the recreate policy for every database | REQ-006 / AC-06 | `adr_02_05_008...md:60,75` (checked in Step 3) | `check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify: Remove the `user_version` mention | Remove the `user_version` mention | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify: Remove the `user_version` mention | Remove the `user_version` mention | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify: Describe one validation mechanism | Describe one validation mechanism | REQ-006 / AC-06 | 8 hits (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify: State that a legacy table makes startup fail, not that it is harmless | State that a legacy table makes startup fail, not that it is harmless | REQ-006 / AC-06 | `db_03_07...md:29,78-80,159` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify: Describe the fingerprint gate and the archive-and-recreate failure | Describe the fingerprint gate and the archive-and-recreate failure | REQ-006 / AC-06 | `db_07...md:115,145,149` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify: State the retired-table behavior accurately | State the retired-table behavior accurately | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | Modify: Describe the validation mechanism in the troubleshooting steps | Describe the validation mechanism in the troubleshooting steps | REQ-006 / AC-06 | 3 hits (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify: Describe the generalized gate in init_db and setup_services | Describe the generalized gate in init_db and setup_services | REQ-006 / AC-06 | 4 hits (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain deployment` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify: Describe fingerprint-only validation without the version stamp | Describe fingerprint-only validation without the version stamp | REQ-006 / AC-06 | 3 hits (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify: Remove the stamp reference | Remove the stamp reference | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify: Remove the stamp reference | Remove the stamp reference | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify: Align the mdq startup validation statement | Align the mdq startup validation statement | REQ-006 / AC-06 | 1 hit (rg count) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `scripts/eventbus/db_tools.py` | Modify: import assert_matches from the generalized schema_fingerprint module after deleting eventbus_schema_fingerprint | imports shared.eventbus_schema_fingerprint which this Plan deletes; import breaks on deletion | REQ-003 / N/A: none cites REQ-003 | rg: scripts/eventbus/db_tools.py:25 from shared.eventbus_schema_fingerprint import assert_matches | tests/eventbus/test_eventbus_db_tools.py | Verified |
| `tests/eventbus/test_eventbus_db_tools.py` | Modify: delete the PRAGMA user_version refusal cases (test_refuses_stale_version, test_refuses_unstamped_existing_database) that this Plan removes; keep the shape-drift case | asserts the user_version refusal (lines 82-103) that this Plan removes; breaks without update | REQ-004 / N/A: none cites REQ-004 | rg: tests/eventbus/test_eventbus_db_tools.py:82,91 PRAGMA user_version refusal cases expecting 'does not match'/'user_version 0' | uv run pytest tests/eventbus/test_eventbus_db_tools.py -v | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | Confirmed to hold no schema-validation code; connection and vec loading semantics only | REQ-003 |
| `scripts/db/recovery.py` | One-table domain identity check and the recreate policy that stay as they are | REQ-003 |
| `scripts/agent/startup_component_init.py` | Caller of `check_workflow_schema`; signature stays | REQ-003 |
| `scripts/shared/execution_snapshot.py` | Reads the file-header `user_version` for observability; the named exception to the AC grep | REQ-007 |
| `scripts/agent/workflow/idempotency_ops.py` | The sole `attempts` writer that stamps the lease | REQ-004 |
| `rules/persisted-schema-change.md` | Checklist for the `schema.sql` stamp removal | REQ-004 |
| `.importlinter` | `shared` leaf contract | REQ-002 |
| `tools/check_db_separation.py` | ADR-008 check that must keep passing | REQ-007 |

## Acceptance Criteria
- `AC-01` (REQ-001): the Phase 1 re-verification of the inventory is recorded in the implementation procedure before code changes.
- `AC-02` (REQ-002): `scripts/shared/schema_fingerprint.py` exists and `scripts/shared/eventbus_schema_fingerprint.py` does not; `PYTHONPATH=scripts uv run lint-imports` keeps `shared-is-leaf`.
- `AC-03` (REQ-003): each database's open or startup path calls the fingerprint check; the per-database tests show the explicit archive-and-recreate error.
- `AC-04` (REQ-004): `rg -n "user_version|schema_migrations|workflow_schema_version|_LEGACY_STALE_AGE_SEC" scripts/ deploy/` returns only the named `execution_snapshot.py` header read.
- `AC-05` (REQ-005): the four drift cases fail for each of the six databases.
- `AC-06` (REQ-006): no document claims a validation mechanism other than fingerprint matching; `check_docs_consistency.py --domain db|agent|eventbus|mcp|deployment` pass.
- `AC-07` (REQ-007): `uv run python tools/check_db_separation.py` and the full validation sequence pass.

## Tests
- `REQ-002`: new `tests/shared/test_schema_fingerprint.py`.
- `REQ-003`, `REQ-005`: new `tests/db/test_schema_validation_per_database.py` (six databases, four drift cases) plus the updated startup, deploy, and recovery-drill tests.
- `REQ-004`: updated `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/shared/test_mcp_dedup.py`, `tests/tools/test_generate_reference_table.py`.
- `REQ-006`, `REQ-007`: documentation checkers and the `rg` acceptance check.

## Documentation Impact
- Required (REQ-006): ADR-001, ADR-008, `db_01`, `db_02`, `db_03`, `db_03_07`, `db_07`, `agent_04_03`, `agent_10_04`, `deployment_01`, `eventbus_06`, `eventbus_07`, ADR-006, `mcp_02_02`. State one validation mechanism, the failure behavior (refuse to start, archive and recreate), and the removal of legacy handling; do not add implementation mappings (`skills/DESIGN.md` Docs content policy). Record anything unconfirmed through `governance_03`.

## Assumptions
- Plan 002 lands first (Depends on above). Falsifiable by `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` Execution Status.
- Removing the `PRAGMA user_version` line from `schema.sql` does not affect existing eventbus databases: the fingerprint ignores `user_version`, and existing files keep their stamp harmlessly. Falsifiable by `tests/eventbus/test_eventbus_startup.py`.
- The generalized module keeps the canonical normalization rules of the eventbus module; per-database DDL accessors pass `CREATE TABLE IF NOT EXISTS` text through the same normalizer. Falsifiable by the six-database drift tests.
- Overlap with other Frozen Plans (`tools/check_plan_target_overlaps.py`, Step 8b): all 18 findings are with `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` and are judged a sequencing dependency (recorded in Scope and `Depends on`: plan 002 first). The two designs do not contradict: plan 002 removes the Agent-side eventbus accessors and config key and moves creation to an EventBus tool, this Plan swaps the validation mechanism; in `scripts/shared/mcp_dedup.py` and `tests/shared/test_mcp_dedup.py` plan 002 edits only a comment and a field-name filter, this Plan edits the schema creation.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How the fingerprint treats sqlite-vec virtual tables and their shadow tables in rag.sqlite and session.sqlite | Confirmed (20261111, Phase 1, real extension loaded) | Resolved: virtual bases are required by name only, `{base}_*` shadow tables are omitted, and live virtual tables are recorded name-only from their sqlite_master DDL text, so `assert_matches` works on connections without the extension; confirmed against deployed `rag.sqlite` and `session.sqlite` (both OK) | False |
| UNK-02 | Whether a legacy workflow database carrying the retired `execution_snapshots` table must fail startup (the documents call it harmless; exact matching rejects it) | A maintainer decision; re-checked 20261111: deployed `/opt/llm/db/workflow.sqlite` does carry `execution_snapshots` and the new fingerprint rejects it | Default: fail (matches the Issue's "extra legacy table" criterion); the maintainer may object before Phase 3 | False |
| UNK-03 | The operator's plan for the deployed `/opt/llm/db` files, which already differ from the current schema (workflow markers, no `tool_call_state`; eventbus `user_version 0`; rag without `rag_corpus_meta`; mdq with `chunk_summaries`) | Whether the data in them must be kept; re-checked 20261111 (read-only `assert_matches`): `rag.sqlite` and `session.sqlite` match the canonical fingerprint; `workflow.sqlite` carries extra `execution_snapshots`; `eventbus.sqlite` carries extra `schema_migrations` | Maintainer decides archive-and-recreate per database before deploy; the Plan changes no data | False |
| UNK-04 | Whether any part of the mcp_dedup `tool_call_state` or `classify_stale_pending` is unused | Not re-examined here (ownership is the mcp_dedup Issue's scope) | Left to `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`; nothing is deleted here | False |
| UNK-05 | Whether file-level ordering with plan 002 needs a hard gate beyond the recorded Depends on | The state of plan 002 at implementation time | `tools/plan_dependency_order.py --plan` before Phase 1 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/schema_fingerprint.py` | create | High | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/eventbus_schema_fingerprint.py` | delete | High | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/schema.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/schema.sql` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/db/create_schema.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/db/recovery_drill.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/db/session_consistency.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/db/rag_consistency_queries.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/services/workflow_schema.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/mcp_dedup.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/db_schema.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tools/generate_reference_table.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tools/check_compat_shims.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `deploy/init_db.sh` | modify | High | N/A | N/A | not applicable (rsynced) |
| `deploy/setup_services.sh` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `registry/manifests/db_schema_versions.yaml` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_schema_fingerprint.py` | create | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_schema_validation_per_database.py` | create | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_repl_health.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_schema_version.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_startup.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_required_workflow_tables_parity.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_schema_gate.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_eventbus_schema.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_recovery_drill.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_stale_recovery_lease.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_workflow_preflight.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_mcp_dedup.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_generate_reference_table.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/90_deployment/deployment_01_deployment.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/db_tools.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/eventbus/test_eventbus_db_tools.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |

## Design
- **Mechanism**: `schema_fingerprint.assert_matches(conn, canonical_ddl, label=...)` builds the expected fingerprint by applying `canonical_ddl` to an in-memory database (as the eventbus module does today) and compares tables, views, columns, indexes with predicates, table-level constraints, foreign keys, and triggers; any difference raises `RuntimeError` whose message tells the operator to stop the service, archive the file, and recreate it. Callers: `scripts/db/create_schema.py` (fresh file gets the DDL, existing file is validated first, no write on refusal), `scripts/agent/services/workflow_schema.py`, `scripts/eventbus/schema.py`, `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/db/session_consistency.py`, `scripts/db/rag_consistency_queries.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`. Alternatives rejected: a second per-database validator (the Issue forbids it) and keeping `user_version` as a first gate (a second mechanism).
- **Named exception**: `scripts/shared/execution_snapshot.py` reads the SQLite file-header `user_version` field for the execution snapshot's `schema_versions` text. It stamps and gates nothing; it is kept and named in AC-04.
- **Compatibility impact**: every database file must match the canonical DDL exactly; the deployed files do not (UNK-03). Removing the stamp changes `scripts/eventbus/schema.sql` text only; the generated schema-version reference changes through the generator.
- **Consumer scan** (`tools/scan_change_consumers.py --seed eventbus_schema_fingerprint --seed user_version --seed REQUIRED_WORKFLOW_TABLES --seed LEGACY_MARKER_TABLES`): reconciled with `rg`; every consumer is a target row; `not affected`: `scripts/db/helper.py`, `scripts/db/recovery.py`, `scripts/shared/execution_snapshot.py` (named exception), `tests/shared/test_execution_snapshot.py`, `tests/agent/test_tool_runner.py` (`snapshot_id` is a parameter name), `tests/agent/test_startup_component_init.py` (patches `_check_workflow_schema` by name only). The scan lists candidates only.
- **Path B analysis** (Step 5): architecture: `PYTHONPATH=scripts uv run lint-imports` keeps 6 contracts; the new module imports only the standard library; `db` passes DDL text, so `shared` never imports `db`. Dependency graph: importers of `eventbus_schema_fingerprint` are `scripts/eventbus/schema.py`, `deploy/init_db.sh`, `scripts/db/recovery_drill.py`, `scripts/db/create_schema.py` and tests. Historical: churn not measured (`N/A`). Operational: no port or process change; the databases are inspected read-only (`sqlite3 -readonly`); services restart on deploy; `ss`, `fuser`, `pip-audit` not run. Persisted schema check (`rules/persisted-schema-change.md`): the DDL objects are unchanged, only the `user_version` stamp line is removed; no migration, per the current-only policy; the deployed files require archive-and-recreate (UNK-03).
- **Validation quality baseline**: `vulture` findings only in `scripts/rag/` and `scripts/shared/runtime_paths.py`, none in these targets; `bandit` baseline: 3 High pre-existing in `scripts/eventbus`; `radon`/diff-cover `N/A: no code diff yet`; implementation raises diff coverage to the `rules/toolchain.md` threshold.
- **Path classification**: Path B (more than 3 files; new shared module; persisted-schema handling).

## Implementation steps
1. **Phase 1: Generalized fingerprint (additive)**
   - [ ] Re-verify the inventory (REQ-001); create `scripts/shared/schema_fingerprint.py` and its tests, including the vec virtual-table treatment (UNK-01); keep the eventbus module until its callers move (REQ-002; `scripts/shared/schema_fingerprint.py`, `tests/shared/test_schema_fingerprint.py`).
2. **Phase 2: Eventbus and deploy gate on the new module**
   - [ ] Move `scripts/eventbus/schema.py`, `deploy/init_db.sh`, and the eventbus tests to the new module; remove the `user_version` gate and the `schema.sql` stamp; regenerate the schema-version reference; delete `scripts/shared/eventbus_schema_fingerprint.py` (REQ-002, REQ-003, REQ-004; the eventbus, deploy, tool, and registry rows of the target table).
   - [ ] Modify: import assert_matches from the generalized schema_fingerprint module after deleting eventbus_schema_fingerprint (REQ-003; `scripts/eventbus/db_tools.py`) — amendment 2026-11-10
   - [ ] Modify: delete the PRAGMA user_version refusal cases (test_refuses_stale_version, test_refuses_unstamped_existing_database) that this Plan removes; keep the shape-drift case (REQ-004; `tests/eventbus/test_eventbus_db_tools.py`) — amendment 2026-11-10
3. **Phase 3: Remaining databases**
   - [ ] Apply the fingerprint to workflow, mcp_dedup, mdq, session, and rag through `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/agent/services/workflow_schema.py`, `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/db/session_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/recovery_drill.py`, `deploy/setup_services.sh`; add `tests/db/test_schema_validation_per_database.py` (REQ-003, REQ-004, REQ-005).
4. **Phase 4: Remove the lease-less legacy rule**
   - [ ] Remove `_LEGACY_STALE_AGE_SEC` handling from `scripts/agent/workflow/state_store.py` and its tests (REQ-004).
5. **Phase 5: Tooling and generated references**
   - [ ] Update `tools/generate_reference_table.py`, `tools/check_compat_shims.py`, and regenerate `registry/manifests/db_schema_versions.yaml` (REQ-004).
6. **Phase 6: Documents**
   - [ ] Update ADR-001, ADR-008, and the DB, deployment, agent, EventBus, and MCP documents; register unconfirmed items through `governance_03` (REQ-006).
7. **Phase 7: Deployment and verification**
   - [ ] Run the full validation sequence; after the change is committed and pushed (the user's decision), hand off to `skills/deploy/SKILL.md` noting UNK-03: the deployed databases must be archived and recreated first (REQ-007; `deploy/init_db.sh`, `deploy/setup_services.sh`).

### Release units
**Unit**: fingerprint-cutover | **Phases**: 2 | **Reason**: removing the eventbus module, the `schema.sql` stamp, and the generator's stamp requirement break the eventbus startup, the deploy gate, and the reference generator until the matching callers and tests change in the same change; the sub-tasks of Phase 2 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/schema_fingerprint.py` | Unit | `uv run pytest tests/shared/test_schema_fingerprint.py -v` | Passes for all drift kinds |
| Six databases | Integration with temporary databases | `uv run pytest tests/db/test_schema_validation_per_database.py -v` | Four drift cases fail with the explicit error per database |
| Startup, deploy, recovery | Unit and integration | `uv run pytest tests/db tests/deploy tests/eventbus tests/agent tests/shared tests/mcp_servers -v` | All pass |
| Whole repository | Full validation sequence | `rules/toolchain.md`: ruff format/check, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, bandit, full `uv run pytest`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | No new findings; all pass |
| ADR-008 | Repository check | `uv run python tools/check_db_separation.py` | Passes |
| Residue | Search | AC-04 grep; `rg -l 'eventbus_schema_fingerprint|user_version' tests/ scripts/ tools/ deploy/` before deletion | Every hit reviewed; none remain except the named exception |
| Generated references | Drift check | `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_compat_shims.py` | Exit 0 |
| Documents | Documentation checks | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain db|agent|eventbus|mcp|deployment`, `check_adr_preservation.py`, `check_adr_authority.py` | Pass |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: The deployed `/opt/llm/db` files fail the new gate and the services refuse to start after deploy → **Mitigation**: UNK-03: the maintainer archives and recreates each database before deploy; the hand-off step names it; the workflow and eventbus files are already refused by the current gates.
- **Risk**: The fingerprint reports false mismatches for sqlite-vec or FTS5 shadow tables → **Mitigation**: UNK-01 default (exclude vec and shadow tables by name, require the virtual table); FTS5 shadow tables are likewise excluded and tested in Phase 1.
- **Risk**: Normalization differences between `CREATE TABLE IF NOT EXISTS` text and the stored SQL cause false mismatches → **Mitigation**: the module compares structural pragma output, not SQL text, as the eventbus module does; the six-database tests include a fresh-database control.
- **Risk**: Removing the `schema.sql` stamp breaks the reference generator and `db_schema_versions.yaml` → **Mitigation**: Phase 2 is one release unit with the generator change and the regeneration.
- **Risk**: Removing the lease-less rule leaves a running attempt that can never be recovered → **Mitigation**: only the legacy path produced lease-less rows (sole writer stamps the lease); `unparseable` classification remains for malformed leases; the lease tests stay.
- **Risk**: A parallel change to the same `scripts/db/` files (plan 002) conflicts → **Mitigation**: the recorded Depends on and `tools/plan_dependency_order.py` check before Phase 1.
- **Risk**: 48 target files make the change large → **Mitigation**: each phase is independently revertable and leaves the suite green; the release unit is Phase 2 only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Generalized fingerprint (additive) | Completed | 20261111-073000 | 20261111-082253 | Procedures 01 and 19 archived to implementations/done/ (20261111). Inventory re-verified in the adversarial verification pass. UNK-01 confirmed with the real extension (virtual bases name-only, shadows omitted, live virtual tables recorded name-only from sqlite_master text). Full validation gates --full all Pass once for both rows (shared coverage/diff-cover run at this boundary). |
| 2 | Eventbus and deploy gate on the new module | Completed | — | 20261111-102849 |  |
| 3 | Remaining databases | In Progress | — | — |  |
| 4 | Remove the lease-less legacy rule | In Progress | — | — |  |
| 5 | Tooling and generated references | In Progress | — | — |  |
| 6 | Documents | In Progress | — | — |  |
| 7 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261110-164906_01_scripts_shared_schema_fingerprint_py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-164906_02_scripts_shared_eventbus_schema_fingerprint_py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261110-164906_03_scripts_eventbus_schema_py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_04_scripts_eventbus_schema_sql.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_05_scripts_db_schema_sql_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_06_scripts_db_create_schema_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_07_scripts_db_recovery_drill_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_08_scripts_db_session_consistency_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_09_scripts_db_rag_consistency_queries_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_10_scripts_agent_services_workflow_schema_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_11_scripts_agent_workflow_state_store_py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-164906_12_scripts_shared_mcp_dedup_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_13_scripts_mcp_servers_mdq_db_schema_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_14_tools_generate_reference_table_py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261110-164906_15_tools_check_compat_shims_py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261110-164906_16_deploy_init_db_sh.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_17_deploy_setup_services_sh.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_18_registry_manifests_db_schema_versions_yaml.md` | 2,5 | Procedure | Completed | — | — |
| `implementations/20261110-164906_19_tests_shared_test_schema_fingerprint_py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-164906_20_tests_db_test_schema_validation_per_database_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_21_tests_db_test_create_schema_py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261110-164906_22_tests_agent_test_repl_health_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_23_tests_eventbus_test_eventbus_schema_version_py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_24_tests_eventbus_test_eventbus_startup_py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_25_tests_deploy_test_required_workflow_tables_parity_py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261110-164906_26_tests_deploy_test_init_db_schema_gate_py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261110-164906_27_tests_deploy_test_init_db_eventbus_schema_py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261110-164906_28_tests_db_test_recovery_drill_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_29_tests_agent_workflow_test_workflow_state_store_py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-164906_30_tests_agent_workflow_test_stale_recovery_lease_py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-164906_31_tests_agent_test_startup_workflow_preflight_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_32_tests_shared_test_mcp_dedup_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_33_tests_mcp_servers_mdq_test_mdq_rag_boundary_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-164906_34_tests_tools_test_generate_reference_table_py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261110-164906_35_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_36_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_37_docs_41_db_db_01_architecture_and_schema-overview-and-config.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_38_docs_41_db_db_02_architecture_and_schema-schema-reference.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_39_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_40_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_41_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_42_docs_23_agent_agent_04_03_state-and-persistence-platform-databases.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_43_docs_23_agent_agent_10_04_operations-and-observability-validation-and-troubleshooting.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_44_docs_90_deployment_deployment_01_deployment.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_45_docs_24_eventbus_eventbus_06_persistence_schema_and_replay.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_46_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_47_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_48_docs_22_mcp_mcp_02_02_startup-modes-and-health.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-164906_49_scripts_eventbus_db_tools_py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261110-164906_50_tests_eventbus_test_eventbus_db_tools_py.md` | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-095137
- **Related target files**: `scripts/shared/schema_fingerprint.py`, `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/db/recovery_drill.py`, `scripts/db/session_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/agent/services/workflow_schema.py`, `scripts/agent/workflow/state_store.py`, `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/mdq/db_schema.py`, `tools/generate_reference_table.py`, `tools/check_compat_shims.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `registry/manifests/db_schema_versions.yaml`, `tests/shared/test_schema_fingerprint.py`, `tests/db/test_schema_validation_per_database.py`, `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/eventbus/test_eventbus_startup.py`, `tests/deploy/test_required_workflow_tables_parity.py`, `tests/deploy/test_init_db_schema_gate.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `tests/db/test_recovery_drill.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/test_startup_workflow_preflight.py`, `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, `tests/tools/test_generate_reference_table.py`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, `docs/90_deployment/deployment_01_deployment.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-002 | Required Changes / repository evidence | `scripts/shared/schema_fingerprint.py` | 1 | AC-02 | `tests/shared/test_schema_fingerprint.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/shared/eventbus_schema_fingerprint.py` | 1 | AC-02 | `tests/shared/test_schema_fingerprint.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/shared/eventbus_schema_fingerprint.py` | 1 | AC-04 | `tests/shared/test_schema_fingerprint.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/eventbus/schema.py` | 2 | AC-03 | `tests/eventbus/test_eventbus_startup.py`, `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/eventbus/schema.py` | 2 | AC-04 | `tests/eventbus/test_eventbus_startup.py`, `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/eventbus/schema.sql` | 2 | AC-04 | `tests/eventbus/test_eventbus_startup.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/db/schema_sql.py` | 2 | AC-02 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/db/schema_sql.py` | 2 | AC-04 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/db/create_schema.py` | 2 | AC-03 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/db/create_schema.py` | 2 | AC-04 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/db/recovery_drill.py` | 3 | AC-03 | `tests/db/test_recovery_drill.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/db/recovery_drill.py` | 3 | AC-04 | `tests/db/test_recovery_drill.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/db/session_consistency.py` | 3 | AC-03 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/db/rag_consistency_queries.py` | 3 | AC-03 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/agent/services/workflow_schema.py` | 3 | AC-03 | `tests/agent/test_repl_health.py`, `tests/agent/test_startup_workflow_preflight.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/agent/services/workflow_schema.py` | 3 | AC-04 | `tests/agent/test_repl_health.py`, `tests/agent/test_startup_workflow_preflight.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/agent/workflow/state_store.py` | 4 | AC-04 | `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/shared/mcp_dedup.py` | 3 | AC-03 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/shared/mcp_dedup.py` | 3 | AC-04 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/mcp_servers/mdq/db_schema.py` | 3 | AC-03 | `tests/mcp_servers/mdq` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tools/generate_reference_table.py` | 5 | AC-04 | `tests/tools/test_generate_reference_table.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tools/check_compat_shims.py` | 5 | AC-04 | `uv run python tools/check_compat_shims.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `deploy/init_db.sh` | 2 | AC-03 | `tests/deploy/test_init_db_schema_gate.py`, `tests/deploy/test_init_db_eventbus_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `deploy/init_db.sh` | 2 | AC-04 | `tests/deploy/test_init_db_schema_gate.py`, `tests/deploy/test_init_db_eventbus_schema.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `deploy/setup_services.sh` | 2 | AC-03 | `tests/deploy/test_required_workflow_tables_parity.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `registry/manifests/db_schema_versions.yaml` | 5 | AC-04 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/shared/test_schema_fingerprint.py` | 2-4 | AC-02 | `uv run pytest tests/shared/test_schema_fingerprint.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `tests/shared/test_schema_fingerprint.py` | 2-4 | AC-05 | `uv run pytest tests/shared/test_schema_fingerprint.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/db/test_schema_validation_per_database.py` | 2-4 | AC-03 | `uv run pytest tests/db/test_schema_validation_per_database.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `tests/db/test_schema_validation_per_database.py` | 2-4 | AC-05 | `uv run pytest tests/db/test_schema_validation_per_database.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/db/test_create_schema.py` | 2-4 | AC-03 | `uv run pytest tests/db/test_create_schema.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/db/test_create_schema.py` | 2-4 | AC-04 | `uv run pytest tests/db/test_create_schema.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_repl_health.py` | 2-4 | AC-03 | `uv run pytest tests/agent/test_repl_health.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/agent/test_repl_health.py` | 2-4 | AC-04 | `uv run pytest tests/agent/test_repl_health.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/eventbus/test_eventbus_schema_version.py` | 2-4 | AC-04 | `uv run pytest tests/eventbus/test_eventbus_schema_version.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/eventbus/test_eventbus_startup.py` | 2-4 | AC-03 | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/eventbus/test_eventbus_startup.py` | 2-4 | AC-04 | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/deploy/test_required_workflow_tables_parity.py` | 2-4 | AC-03 | `uv run pytest tests/deploy/test_required_workflow_tables_parity.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/deploy/test_init_db_schema_gate.py` | 2-4 | AC-03 | `uv run pytest tests/deploy/test_init_db_schema_gate.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/deploy/test_init_db_schema_gate.py` | 2-4 | AC-04 | `uv run pytest tests/deploy/test_init_db_schema_gate.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/deploy/test_init_db_eventbus_schema.py` | 2-4 | AC-03 | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/db/test_recovery_drill.py` | 2-4 | AC-03 | `uv run pytest tests/db/test_recovery_drill.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/db/test_recovery_drill.py` | 2-4 | AC-04 | `uv run pytest tests/db/test_recovery_drill.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/agent/workflow/test_workflow_state_store.py` | 2-4 | AC-04 | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/agent/workflow/test_stale_recovery_lease.py` | 2-4 | AC-04 | `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_startup_workflow_preflight.py` | 2-4 | AC-03 | `uv run pytest tests/agent/test_startup_workflow_preflight.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/shared/test_mcp_dedup.py` | 2-4 | AC-03 | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/shared/test_mcp_dedup.py` | 2-4 | AC-04 | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | 2-4 | AC-02 | `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/tools/test_generate_reference_table.py` | 2-4 | AC-04 | `uv run pytest tests/tools/test_generate_reference_table.py -v` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | 6 | AC-06 | `check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 6 | AC-06 | `check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/90_deployment/deployment_01_deployment.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain deployment` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 6 | AC-06 | `check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | 6 | AC-06 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-10: imports shared.eventbus_schema_fingerprint which this Plan deletes; import breaks on deletion | scripts/eventbus/db_tools.py | Phase 2 | N/A: none cites REQ-003 | tests/eventbus/test_eventbus_db_tools.py | Confirmed by repository evidence |
| REQ-004 | Amendment 2026-11-10: asserts the user_version refusal (lines 82-103) that this Plan removes; breaks without update | tests/eventbus/test_eventbus_db_tools.py | Phase 2 | N/A: none cites REQ-004 | uv run pytest tests/eventbus/test_eventbus_db_tools.py -v | Confirmed by repository evidence |
