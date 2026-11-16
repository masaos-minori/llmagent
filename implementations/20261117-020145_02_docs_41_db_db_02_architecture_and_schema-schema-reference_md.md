## Goal

Add the workflow lease-contract behavior to `db_02` §7 (workflow tables): both lease columns are always stamped by the sole producer, the lease equals the stage `timeout_sec` plus a fixed margin, no heartbeat/renewal exists, and an old `started_at` alone never makes an attempt stale (`REQ-002`); later add the schema-level `NOT NULL` / CHECK statement once `compat002` implements (`REQ-008`, gated).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-002` matches current committed source: `idempotency_ops::begin_stage_if_new()` is the sole producer and always stamps `owner_id` and `lease_expires_at` (`lease_expires_from(now, lease_duration_sec)` = stage `timeout_sec` + `_LEASE_MARGIN_SEC` = 30 s); `_classify_running_attempts()` recovers only lease-expired rows (`scripts/agent/workflow/state_store.py:365-419`). Safe to document now.
- §7 currently lists the workflow tables (`tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state`) but omits `owner_id`/`lease_expires_at`, the lease margin, and heartbeat absence (`db_02:44-50`) — confirmed by reading §7.
- `REQ-008` (Phase 3) is gated on `compat002` implementing: the current DDL keeps the lease columns nullable (`scripts/db/schema_sql.py:192-193`), so a schema-enforced `NOT NULL` statement would be wrong now. The exact wording is pinned in `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`.

## Design decisions
- **Append a lease-contract paragraph to §7**, beside the existing workflow-table description, stating the contract by responsibility and consequence (both columns always stamped by the sole producer; lease = stage `timeout_sec` + fixed margin, never shorter than that margin; no heartbeat/renewal; stale only when the explicit lease expired). Point to `idempotency_ops.py` / `state_store.py`. Do not state the 30 s value as deployed configuration (avoids `check_docs_content_policy.py`).
- **Split Phase 1 vs Phase 3 within §7.** REQ-002 lands now; REQ-008 (schema-level `NOT NULL`/CHECK) is a gated follow-on.

## Alternatives considered
- **Writing REQ-008 now.** Rejected: the columns are still nullable in the shipped DDL, so a `NOT NULL` statement would be a doc/source mismatch. Deferred to `compat002`.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`
### Procedure
**Phase 1 (safe-now, executable now):**
1. **REQ-002** — In §7 (after the workflow-table description, around line 44-50), add a lease-contract paragraph: both `owner_id` and `lease_expires_at` are stamped on every attempt row by the sole writer `idempotency_ops::begin_stage_if_new()`; the lease is the stage `timeout_sec` plus a fixed process margin and is therefore never shorter than that margin; there is no heartbeat or lease renewal; an attempt is stale only when its explicit `lease_expires_at` has passed and an old `started_at` alone never makes it stale; recovery deletes `processed_events` only for attempts it marks failed. Point to `scripts/agent/workflow/idempotency_ops.py` and `scripts/agent/workflow/state_store.py`.
**Phase 3 (gated on `compat002`):**
2. **REQ-008** — Add that `owner_id` and `lease_expires_at` are enforced `NOT NULL` (with `CHECK(length(owner_id) > 0)`) at the schema level once `compat002` implements. Blocked until `compat002` implements.
### Method
One lease-contract paragraph (Phase 1); one schema-enforcement sentence (Phase 3, gated).
### Details
- Insert the lease-contract paragraph into §7 after the existing workflow-table description (lines 44-50), before the `task_nonce` paragraph. Keep it responsibility/consequence level; cite the two source files.
- **REQ-008 (Phase 3, gated)** — leave a clearly marked placeholder: "GATED — once `compat002` implements, add: `owner_id` and `lease_expires_at` are `NOT NULL`; `owner_id` also carries `CHECK(length(owner_id) > 0)`." Do not write the `NOT NULL` statement now.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: REQ-008 (Phase 3) deferred until compat002 implements; Phase 1 (REQ-002) safe-now. |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation checkers in Validation plan. |

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
