## Goal

Fix `tests/integration/test_orchestrator_integration.py::TestToolCallFlow`'s 3 `ToolLoopGuard.check_all(...)` call sites (2 failing tests) to pass a `round_tool_names` argument in the correct (3rd) position (REQ-003).

## Scope

In scope: the 3 `check_all(...)` calls inside `TestToolCallFlow` (lines ~552, 556, 575) only. Out of scope: this same file's separately-tracked `TestApprovalWorkflowWithRealDB::test_handle_turn_invokes_workflow_engine_run` failure (`NameError: name 'orch' is not defined`, tracked under `int001`) — a distinct root cause.

## Assumptions

- `round_tool_names=[]` is behavior-neutral for these 2 tests, per the Plan's confirmed evidence.

## Design decisions

- Insert `[]` as the 3rd positional argument at each call site, matching each test's existing positional-argument style.

## Alternatives considered

- Converting to keyword arguments: rejected as unnecessarily larger diff than positional insertion.

## Implementation

### Target file

`tests/integration/test_orchestrator_integration.py`

### Procedure

1. Re-confirm each `ToolLoopGuard(ctx).check_all(...)` call's exact current line/form inside `TestToolCallFlow` via `rg -n "check_all\(" tests/integration/test_orchestrator_integration.py`.
2. For each of the 3 calls, insert `[]` as the 3rd positional argument.

### Method

Direct positional-argument insertion at 3 call sites — no signature or logic change. Scoped strictly to `TestToolCallFlow`; do not touch `TestApprovalWorkflowWithRealDB` in the same file (tracked separately under `int001`).

### Details

- Before pattern: `ToolLoopGuard(ctx).check_all(<arg1>, <arg2>, <arg3>, <arg4>)` — 4 positional args.
- After pattern: `ToolLoopGuard(ctx).check_all(<arg1>, <arg2>, [], <arg3>, <arg4>)` — 5 positional args matching the current `check_all` signature.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix.

## Rollback considerations

- `git revert` the commit, or manually remove the inserted `[]` arguments.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/integration/test_orchestrator_integration.py` | Integration | `uv run pytest tests/integration/test_orchestrator_integration.py::TestToolCallFlow -q` | Both tests pass |

## Completion criteria

- `uv run pytest tests/integration/test_orchestrator_integration.py::TestToolCallFlow -q` passes.
- `uv run pytest tests/integration/test_orchestrator_integration.py -q -k "not test_handle_turn_invokes_workflow_engine_run"` passes with no new regression (excludes `int001`'s separately-tracked `NameError`).

## Out of scope

- `TestApprovalWorkflowWithRealDB::test_handle_turn_invokes_workflow_engine_run` in this same file — tracked under a separate Plan/issue (`int001`).
- Other target files from this same Plan (each has its own implementation procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Inserted `[]` as 3rd positional arg at 3 call sites in TestToolCallFlow |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 11 TestToolCallFlow tests pass; 38 of 39 total pass (1 excluded per Plan scope) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping |

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
- **Requirement ID**: REQ-003: fix `check_all(...)` call sites in `tests/integration/test_orchestrator_integration.py::TestToolCallFlow`
- **Source issue**: issues/20260927-075237_agent001_toolloopguard.check_all-requires-message-argument-callers-do-not-pass.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081106_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091211
- **Related target files**: tests/integration/test_orchestrator_integration.py
