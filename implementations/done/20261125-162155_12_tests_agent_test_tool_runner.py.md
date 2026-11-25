## Goal

Pin the runner wiring: `dedup_state` reaches the audit line and the diagnostics record carries the ids (REQ-003, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Execute after rows 5, 6, 7; the runner now calls `record_tool_exec` and `record_transport_failure` from `agent.tool_result_audit`.
- Tests that patch `ctx.diagnostics.save_transport_failure` (lines 2127, 3133) keep working because the bridge calls the same method; the call gains the new keyword arguments.

## Design decisions

- Assert through the existing mock seams (audit logger payload, patched diagnostics store), not by importing the new module directly.

## Alternatives considered

N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`
### Procedure

- Add a case: a `ToolCallResult` with a non-empty `dedup_state` produces an audit payload containing it; an empty one does not add the key (AC-1).
- Update the `save_transport_failure` assertions to expect the new `call_id`, `request_id`, `task_id`, `turn_id` keyword arguments (AC-5).

### Method
- Exercise `execute_one_tool_call` with a stubbed `ToolCallResult` carrying `dedup_state` and check the logged JSON payload.

### Details
- The existing transport-failure and no-failure cases (lines 2127, 2152, 3160) stay passing with the extended call shape.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- AC-1 and AC-5 are pinned on the runner side.

## Out of Scope

- The bridge module and its unit tests (row 6 and its companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 20261125 | Execute after rows 5, 6, 7 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | 117 passed; ruff clean; mypy at baseline |

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
- **Requirement ID**: REQ-003, REQ-005 (runner pins)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `tests/agent/test_tool_runner.py`