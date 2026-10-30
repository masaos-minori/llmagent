## Goal

Set the per-attempt side-effect flag in `scripts/agent/tool_runner.py` before any non-READ tool call executes, on both the gateway and the no-gateway path (`REQ-006`, record a side effect before a retry decision can need it).

## Scope

- Modify only `scripts/agent/tool_runner.py` (`_execute_prepared_call`).

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 3, after row 06 (`side_effects_started` on `TurnState`); independent of the wfrecovery001 Plan. Execution order follows the Plan's phases, not `seq`.
- Verified in this cycle: `_execute_prepared_call` returns from the gateway branch (`:151-153`) before `classify_operation_type` runs (`:155`), and production always has a gateway (the function's own docstring cites `factory.py:652`), so setting the flag only in the no-gateway branch would never fire in production.
- `classify_operation_type` returns `OperationType.UNKNOWN` (non-READ) for unregistered tools and when no registry is given (`scripts/agent/tool_policy.py`), so unclassified calls count as side effects (conservative).
- Calls in a round can run concurrently; the flag is shared per turn, which is conservative.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `side_effects_started` (row 06 document).

## Design decisions

- Hoist the classification to the top of `_execute_prepared_call`, set `ctx.turn.side_effects_started = True` when the operation is not READ, and reuse the same `op` value in the existing no-gateway preflight check instead of classifying twice.

## Alternatives considered

- Set the flag inside the gateway: rejected, the gateway is another module and the rule belongs with the tool runner that already owns the READ branch.

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. At the start of `_execute_prepared_call` (`:134`), compute `op = classify_operation_type(name, ctx.services_required.runtime_tools)`.
2. If `op` is not `OperationType.READ`, set `ctx.turn.side_effects_started` to true before any execution.
3. Keep the gateway branch and the preflight branch behavior; make the preflight branch use the already computed `op`.

### Method

- Set the flag before awaiting the call, so a failure during the call still leaves it set.

### Details

- `classify_operation_type` and `OperationType` are already imported in this module.
- Line numbers are from the current file; locate by symbol.

## Compatibility considerations

- No change to call results or policy enforcement; a new write on `TurnState`.
- Behavior consequence (intended): the engine suppresses retry after a non-READ call.

## Security considerations

- Policy enforcement (`check_preflight`) is unchanged; the flag only influences retry.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -v` (flag set for a non-READ call on both paths, not for READ)
- `uv run ruff format scripts/agent/tool_runner.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- After a non-READ call through the gateway, `ctx.turn.side_effects_started` is true; after a READ call it stays false.

## Out of Scope

- Clearing the flag per attempt (adapter row), the retry rule (engine row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Hoist the classification and set the flag | Pending | — | — | Plan Phase 3; after row 06 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Row 11 document |
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
- **Requirement ID**: REQ-006 (set the side-effect flag before a non-READ call)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/tool_runner.py
