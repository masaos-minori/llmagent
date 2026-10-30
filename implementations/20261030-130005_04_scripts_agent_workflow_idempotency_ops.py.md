## Goal

Carry the lease duration into the attempt-start transaction in `scripts/agent/workflow/idempotency_ops.py`, so each new attempt is written with its owner and a lease (`REQ-005`, owner and lease at attempt start).

## Scope

- Modify only `scripts/agent/workflow/idempotency_ops.py` (`begin_stage_if_new`).

## Assumptions

- Plan Dependencies (`plans/20261030-114516_wflease001_stale-attempt-lease.md` Scope): Plan Phase 3. Requires the schema row (Plan row 6, `Blocked` for this document set), `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 3 (its row 05 document rewrites `begin_stage_if_new` with the signature `(db, task_id, stage_id, workflow_id=None)`), and this Plan's row 03 (`worker_id`, owner and lease parameters). Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgment (Step 8b): `idempotency_ops.py` is also a target of the wfrecovery001 Plan: sequencing dependency; this document adds one optional parameter to the function that Plan rewrites.
- Names created by earlier rows or Plans, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `worker_id` (row 03 document), `insert_attempt` (wfrecovery001 Plan row 04 document).
- Column names `owner_id` and `lease_expires_at` are created by the schema row of this Plan (Phase 2, `Blocked` for this document set); `tools/stale_detector.py` flags them until that row lands, which the Plan's phase order guarantees before this document is executed.

## Design decisions

- Add an optional `lease_sec: int | None = None` parameter to `begin_stage_if_new`; when given, compute `lease_expires_at` as the current UTC time plus `lease_sec` (new), formatted like `now_iso()`, and pass it with `worker_id()` to `insert_attempt`; when omitted, insert with no owner and no lease (legacy-compatible).

## Alternatives considered

- Compute the lease in the engine and pass the final timestamp: rejected, the start time must come from the same instant as `started_at` inside the transaction.

## Implementation

### Target file

`scripts/agent/workflow/idempotency_ops.py`

### Procedure

1. Extend the `begin_stage_if_new` signature with `lease_sec: int | None = None`.
2. When `lease_sec` (new) is set, derive the single start instant used for both `started_at` and `lease_expires_at`, and pass `owner_id=worker_id()` and the lease string to `insert_attempt`.
3. Update the docstring to describe the owner and lease.

### Method

- Use one `datetime.now(UTC)` value inside the `begin_immediate()` block for both fields so the lease is exactly start plus `lease_sec` (new).
- Format with the same `%Y-%m-%dT%H:%M:%SZ` pattern as `now_iso()`.

### Details

- The ledger and the stage-already-running check are unchanged by this document.

## Compatibility considerations

- Optional parameter; the engine and tests that omit it get legacy behavior.

## Security considerations

- N/A: no external input.

## Rollback considerations

- N/A: revert the commit together with the schema row.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py tests/agent/workflow/test_stale_recovery_lease.py -v`
- `uv run ruff format scripts/agent/workflow/idempotency_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- A started attempt has `lease_expires_at` equal to its `started_at` plus `lease_sec` (new).

## Out of Scope

- Engine passing the value (row 05), owner helper and insert parameters (row 03), detection, schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `lease_sec` (new) and pass owner and lease to the attempt insert | Pending | — | — | Plan Phase 3; gated on the schema row and wfrecovery001 Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test rows' documents |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (owner and lease at attempt start)
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130005
- **Related target files**: scripts/agent/workflow/idempotency_ops.py
