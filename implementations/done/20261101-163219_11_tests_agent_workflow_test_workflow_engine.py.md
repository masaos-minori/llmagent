## Goal

Assert in `tests/agent/workflow/test_workflow_engine.py` that every engine-started attempt carries the owner stamp and the timeout-plus-margin lease (REQ-005, REQ-009 / AC-5).

## Scope

- Extend the existing retry/timeout tests (`test_retry_succeeds_on_second_attempt` `:113`, `test_timeout_raises_workflow_timeout_error` `:165-230`): after a stage runs, read the attempt row and assert `owner_id` is non-null and `parse_iso_utc(lease_expires_at) - parse_iso_utc(started_at) == stage timeout_sec + 30` (`StageDefinition(timeout_sec=5)` fixtures at `:41-43` make the expected 35 s).
- Add one case asserting the fallback horizon (no stage def / default 60 s path yields 90 s) if the fixture allows a stage-less run; otherwise assert with the 5 s stages only.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Engine fixtures already build stores and engines per test (this file's existing style); no new fixture layer.

## Design decisions

- Assertions read the persisted row through the store (not the engine's in-memory objects) so the test locks the DB contract, per REQ-005.

## Alternatives considered

- Asserting on `begin_stage_if_new` call arguments with spies — rejected: the Plan AC-5 is about the stored row, and spies would survive a write-side bug.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. Add a shared helper `fetch_attempt(conn, attempt_id)` mirroring the file's existing row reads.
2. Extend the two named tests and add `test_attempt_start_stamps_lease`.

### Method
Test-only edits inside existing classes.

### Details
- No heartbeat/renewal assertion — Plan UNK-02 (deadline lease).

## Compatibility considerations

- Existing assertions in these tests stay; this is additive unless a retry test's row expectations change.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Delete the added helper and cases.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v`

## Completion criteria

- AC-5 covered end-to-end through the engine path.

## Out of Scope

- Timeout/retry behavior changes themselves (`wfretry001` issue, Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Implemented: lease assertions in retry/timeout tests and TestWorkflowEngineLeaseStamping. |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: this procedure is the test update itself. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff + full suite 10908 passed, diff-cover exit 0. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: documentation updates owned by procedures 15 and 16. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Ownership and lease-based recovery)
- **Requirement ID**: `REQ-005`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/shared/json_utils.py`