## Goal

Make `scripts/agent/workflow/workflow_engine.py` pass each stage's lease duration (stage `timeout_sec` plus a margin) when it starts an attempt (`REQ-005`, lease derived from the stage timeout with a named margin).

## Scope

- Modify only `scripts/agent/workflow/workflow_engine.py` (`_run_stage` and one module constant).

## Assumptions

- Plan Dependencies (`plans/20261030-114516_wflease001_stale-attempt-lease.md` Scope): Plan Phase 3, after this Plan's row 04 (`lease_sec` parameter), the schema row (Plan row 6, `Blocked` for this document set), and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 4, whose row 07 document rewrites `_run_stage` to call `begin_stage_if_new` with persisted numbering. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `workflow_engine.py` is also a target of the wfrecovery001 Plan, `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md`, and `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`: sequencing dependency; this change is one added argument in the same call and the later change rebases.
- The engine enforces the stage deadline with `asyncio.wait_for(fn(), timeout=timeout)` (`:224`), so a normally running stage cannot outlive `timeout_sec`; owner decision (2026-10-30): no heartbeat.
- Plan UNK-03: the margin is a named constant (30 s), not configuration.
- Names created by earlier rows or Plans, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: the `lease_sec` parameter (row 04 document).

## Design decisions

- Define `_LEASE_MARGIN_SEC = 30` (new) at module level and pass `lease_sec = timeout + _LEASE_MARGIN_SEC` where `timeout` is the stage's `timeout_sec` already resolved in `_run_stage` (`:204`).

## Alternatives considered

- Put the margin in `config/workflows/default.json`: rejected for now (Plan UNK-03); it would also change the deploy pre-flight surface.

## Implementation

### Target file

`scripts/agent/workflow/workflow_engine.py`

### Procedure

1. Add the `_LEASE_MARGIN_SEC` (new) constant near the other module constants.
2. In `_run_stage`, pass `lease_sec` to `begin_stage_if_new`, computed from the resolved stage timeout.

### Method

- The stage timeout default for an unknown stage is 60 s (`:205` region); use the same resolved value so plan, execute, and verify each get their own lease.

### Details

- Do not change timeout classification or retry logic (retry Plan).
- Module size is 9644 B; the change is two lines.

## Compatibility considerations

- No behavior change for stage execution; only the attempt row gains owner and lease.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (the started attempt's lease equals start plus stage timeout plus the margin)
- `uv run ruff format scripts/agent/workflow/workflow_engine.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- Each attempt is started with `lease_sec` equal to the stage `timeout_sec` plus the named margin.

## Out of Scope

- Lease storage, detection, schema, tests, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the margin constant and pass `lease_sec` at attempt start | Pending | — | — | Plan Phase 3; gated on the schema row and wfrecovery001 Phase 4 |
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
- **Requirement ID**: REQ-005 (lease from the stage timeout plus a margin)
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130005
- **Related target files**: scripts/agent/workflow/workflow_engine.py
