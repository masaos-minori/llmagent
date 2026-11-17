## Goal

Add the workflow lease-contract behavior to `db_02` §7 (workflow tables): both lease columns are stamped by the sole production writer, the lease equals the stage `timeout_sec` plus a fixed margin, no heartbeat/renewal exists, and an old `started_at` alone never makes an attempt stale (`REQ-002`); the schema-level `NOT NULL` / CHECK statement stays a gated follow-on until `compat002` implements (`REQ-008`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-002` matches current committed source with one wording correction (re-verified 20261117): `idempotency_ops::begin_stage_if_new()` is the sole writer of `attempts` rows and stamps `owner_id` / `lease_expires_at` in the attempt-insert transaction **when a `lease_duration_sec` is passed**; the helper still accepts `None` for legacy/test callers (`scripts/agent/workflow/idempotency_ops.py:20-45`). The sole production caller `workflow_engine.py` always passes stage `timeout_sec` + `_LEASE_MARGIN_SEC` (30 s) (`workflow_engine.py:31,336`), so every production attempt row is stamped. The doc attributes "stamped" to the sole production writer (the engine path), not to an unconditionally-stamping helper. Safe to document now.
- §7 currently lists the workflow tables (`tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state`) but omits `owner_id`/`lease_expires_at`, the lease margin, and heartbeat absence (`db_02:44-50`) — confirmed by reading §7. §7 already documents the `processed_events` deletion for attempts marked failed and the `attempts.status` CHECK (re-verified 20261117); the new paragraph must not duplicate them, only link to recovery.
- `REQ-008` stays gated (re-verified 20261117): the current DDL keeps the lease columns nullable (`scripts/db/schema_sql.py:192-193`, no lease CHECK), and the `compat002` procedure documents (`implementations/20261117-011632_*`) are all Pending — `compat002` is not yet implemented, so a schema-enforced `NOT NULL` statement would be wrong now. The exact wording is pinned in `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`.

## Design decisions
- **Append a lease-contract paragraph to §7**, beside the existing workflow-table description, stating the contract by responsibility and consequence (both lease columns stamped in the insert transaction by the sole production writer — the engine always supplying a lease duration; lease = stage `timeout_sec` + fixed margin, never shorter than that margin; no heartbeat/renewal; stale only when the explicit lease expired). Point to `idempotency_ops.py` / `state_store.py`. Do not state the 30 s value as deployed configuration (avoids `check_docs_content_policy.py`).
- **REQ-008 is recorded as a gated follow-on in this procedure only, not as an inline placeholder in `db_02`.** Re-verification decision: writing "GATED — once `compat002` implements, add NOT NULL..." into the reference doc would embed a forward-looking schema claim in a doc that must describe only current behavior — the same mismatch this row is meant to avoid. The gated wording stays pinned here and in the `compat002` plan until a post-`compat002` procedure lands it.

## Alternatives considered
- **Writing REQ-008 now.** Rejected: the columns are still nullable in the shipped DDL, so a `NOT NULL` statement would be a doc/source mismatch. Deferred to `compat002`.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`
### Procedure
**Executable now:**
1. **REQ-002** — In §7 (after the workflow-table description, around line 44-50), add a lease-contract paragraph: `attempts` rows carry `owner_id` and `lease_expires_at`, written in the same transaction that inserts the attempt row by `idempotency_ops::begin_stage_if_new()` — the sole writer of `attempts` rows — and the production caller `workflow_engine.py` always supplies the lease duration: the stage `timeout_sec` plus a fixed process margin (`workflow_engine._LEASE_MARGIN_SEC`), so a lease never expires while its own stage is still executing; there is no heartbeat or lease renewal; an attempt is stale only when its explicit `lease_expires_at` has passed and an old `started_at` alone never makes it stale; recovery (`state_store.py::recover_stale_attempts()`) recovers only lease-expired rows — link to db_07 §9.7 for the recovery narrative already documented there. Do not restate the `processed_events` deletion or the `attempts.status` CHECK (already in §7).
**Gated follow-on (not part of this cycle's target-file edits):**
2. **REQ-008** — Add that `owner_id` and `lease_expires_at` are enforced `NOT NULL` (with `CHECK(length(owner_id) > 0)`) at the schema level once `compat002` implements; land it via a post-`compat002` procedure, not as an inline placeholder in the doc. Blocked until `compat002` implements.
### Method
One lease-contract paragraph (executable now); REQ-008 stays a pinned gated follow-on.
### Details
- Insert the lease-contract paragraph into §7 after the existing workflow-table description (line 46), before the `task_nonce` paragraph (line 48). Keep it responsibility/consequence level; cite the two source files and link `db_07_api_and_operations-recovery-and-reference.md#97-persistence-domain-policy` for recovery.
- **REQ-008 (gated)** — no inline placeholder in `db_02` (see Design decisions). The gated wording stays here: once `compat002` implements, a follow-on procedure adds "`owner_id` and `lease_expires_at` are `NOT NULL`; `owner_id` also carries `CHECK(length(owner_id) > 0)`" to §7.

## Compatibility considerations
N/A: documentation only; no runtime blast radius. `deploy.sh` serves docs statically (rsynced).

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain db` — all pass; lease columns/margin documented; no migration implied.
- `uv run python tools/check_docs_structure.py`, `tools/check_docs_japanese.py` — pass.

## Completion criteria
- §7 documents the lease columns, margin policy, heartbeat absence, and lease-only staleness (`REQ-002`).
- REQ-008 is recorded as a gated follow-on, not written (`REQ-008`).

## Out of Scope
The schema-level `NOT NULL` / CHECK statement (`REQ-008`, gated on `compat002`); code/schema/test changes (the lease issue owns those).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-121018 | 20261117-121046 | Gated: REQ-008 (Phase 3) deferred until compat002 implements; Phase 1 (REQ-002) safe-now. REQ-008 gate confirmed still closed (compat002 procedures 20261117-011632_* all Pending; schema_sql.py:192-193 nullable). REQ-008 recorded as pinned gated follow-on, no inline doc placeholder. Lease-contract paragraph landed in db_02 section 7; producer wording matches current source (engine supplies lease, helper stamps in insert transaction). |
| 2 | Add or update tests per Validation plan | Completed | — | 20261117-121046 | N/A: documentation-only row. N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-121046 | Documentation checkers in Validation plan. check_docs_quality/content_policy/consistency --domain db/structure/japanese all exit 0; check_workitem_structure clean. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-008`
- **Source issue**: `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-020145
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`