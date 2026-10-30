## Goal

Record attempt ownership and a lease when an attempt starts, and let the finish operation require the expected owner and lease for a takeover, in `scripts/agent/workflow/attempt_ops.py` (`REQ-005`, owner and lease at attempt start; `REQ-007`, conditional takeover).

## Scope

- Modify only `scripts/agent/workflow/attempt_ops.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114516_wflease001_stale-attempt-lease.md` Scope): Plan Phase 3. Requires the schema row (`attempts.owner_id`, `attempts.lease_expires_at`; Plan row 6, `Blocked` for this document set, which needs `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3) and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 3, whose row 04 document creates `insert_attempt` and `mark_attempt_finished` in this file. This document MUST NOT run before them. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgment (Step 8b): `attempt_ops.py` is also a target of the wfrecovery001 Plan: sequencing dependency; this document extends that contract with two optional fields.
- No process or worker identity exists in `scripts/` today (the only `worker_id` (new) is the session id in `audit_event_emitter.py`); a per-process identifier is introduced here.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `insert_attempt` and `mark_attempt_finished` (wfrecovery001 Plan row 04 document).
- Column names `owner_id` and `lease_expires_at` are created by the schema row of this Plan (Phase 2, `Blocked` for this document set); `tools/stale_detector.py` flags them until that row lands, which the Plan's phase order guarantees before this document is executed.

## Design decisions

- `worker_id` (new) returns a per-process identifier built from the host name, the process id, and a random suffix, created once and cached at module level (a bare PID can be reused after a restart).
- `insert_attempt` gains optional `owner_id` and `lease_expires_at` parameters; when omitted the row is inserted with nulls (legacy-compatible).
- `mark_attempt_finished` gains optional `expect_owner` (new) and `expect_lease` (new) conditions that are added to the `WHERE` clause only when given, keeping the row-count requirement.

## Alternatives considered

- Use the session id as the owner: rejected, one session can span restarts and several processes cannot share one safely.

## Implementation

### Target file

`scripts/agent/workflow/attempt_ops.py`

### Procedure

1. Add `worker_id` (new)() returning the cached per-process identifier.
2. Extend `insert_attempt` with `owner_id` and `lease_expires_at` (strings in the persisted `YYYY-MM-DDTHH:MM:SSZ` format) and include them in the INSERT.
3. Extend `mark_attempt_finished` with `expect_owner` (new) and `expect_lease` (new), adding `AND owner_id IS ?` and `AND lease_expires_at IS ?` only when the arguments are provided.

### Method

- Format `lease_expires_at` with the same `strftime` pattern `now_iso()` uses (the engine computes the instant; this module only stores the string).
- Do not log or return the identifier beyond the stored column.

### Details

- `finish_attempt` (own transaction) passes the new optional conditions through unchanged for normal completion (they stay `None`).
- Keep this module free of imports from the engine or `state_store`.

## Compatibility considerations

- Both new parameters are optional; existing callers and tests are unaffected.
- Persisted rows get two nullable columns from the migration; legacy rows keep nulls.

## Security considerations

- The identifier contains the host name and process id; it is stored in the local `workflow.sqlite` only and not emitted to audit logs by this change.

## Rollback considerations

- Revert the commit together with the schema row; migrated columns remain nullable and unused.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` (owner and lease recorded; conditional finish with a stale expected lease affects zero rows)
- `uv run ruff format scripts/agent/workflow/attempt_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- An attempt started with a lease stores `owner_id` and `lease_expires_at`.
- A conditional finish with a non-matching owner or lease updates zero rows and raises the typed attempt error from the wfrecovery001 contract.

## Out of Scope

- Computing the lease duration (engine row), carrying it through the start entry (`idempotency_ops.py` row), detection (`state_store.py` row), schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `worker_id` (new); extend `insert_attempt` and `mark_attempt_finished` | Pending | — | — | Plan Phase 3; gated on the schema row and wfrecovery001 Phase 3 |
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
- **Requirement ID**: REQ-005 (owner and lease at attempt start), REQ-007 (conditional takeover)
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130005
- **Related target files**: scripts/agent/workflow/attempt_ops.py
