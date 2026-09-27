## Goal

Fix `tests/agent/test_orchestrator.py::TestToolLoopGuardHelpers`'s 4 `ToolLoopGuard.check_all(...)` call sites (3 failing tests) to pass a `round_tool_names` argument in the correct (3rd) position (REQ-002).

## Scope

In scope: the 4 `check_all(...)` calls inside `TestToolLoopGuardHelpers` (lines ~1121, 1133, 1138, 1155) only. Out of scope: this same file's other, separately-tracked failures (`agent008`'s `TestAllowedToolsOverride`/`TestHandleTurnInvokesWorkflowEngine` — a distinct root cause, workflow-engine invocation, not this signature issue).

## Assumptions

- `round_tool_names=[]` is behavior-neutral for these 3 tests (cycle/dedup-focused assertions, no stagnation-detection assertions), per the Plan's confirmed evidence.

## Design decisions

- Insert `[]` as the 3rd positional argument at each call site, matching each test's existing positional-argument style.

## Alternatives considered

- Converting to keyword arguments: rejected as unnecessarily larger diff than positional insertion.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Re-confirm each `ToolLoopGuard(ctx).check_all(...)` call's exact current line/form inside `TestToolLoopGuardHelpers` via `rg -n "check_all\(" tests/agent/test_orchestrator.py` (adversarial re-verification — do not rely solely on the Plan's recorded line numbers).
2. For each of the 4 calls, insert `[]` as the 3rd positional argument.

### Method

Direct positional-argument insertion at 4 call sites — no signature or logic change. Scoped strictly to `TestToolLoopGuardHelpers`; do not touch `TestAllowedToolsOverride`/`TestHandleTurnInvokesWorkflowEngine` in the same file (tracked separately under `agent008`).

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
| `tests/agent/test_orchestrator.py` | Unit | `uv run pytest tests/agent/test_orchestrator.py::TestToolLoopGuardHelpers -q` | All 3 tests pass |

## Completion criteria

- `uv run pytest tests/agent/test_orchestrator.py::TestToolLoopGuardHelpers -q` passes.
- `uv run pytest tests/agent/test_orchestrator.py -q -k "not TestAllowedToolsOverride and not TestHandleTurnInvokesWorkflowEngine"` passes with no new regression (excludes `agent008`'s separately-tracked failures).

## Out of scope

- `TestAllowedToolsOverride::test_original_config_restored_even_on_error` and `TestHandleTurnInvokesWorkflowEngine`'s tests in this same file — tracked under a separate Plan/issue (`agent008`).
- Other target files from this same Plan (each has its own implementation procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Inserted `[]` as 3rd positional arg at 4 call sites in TestToolLoopGuardHelpers |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 9 TestToolLoopGuardHelpers tests pass; 76 of 87 total pass (11 excluded per Plan scope) |
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
- **Requirement ID**: REQ-002: fix `check_all(...)` call sites in `tests/agent/test_orchestrator.py::TestToolLoopGuardHelpers`
- **Source issue**: issues/20260927-075237_agent001_toolloopguard.check_all-requires-message-argument-callers-do-not-pass.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081106_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091211
- **Related target files**: tests/agent/test_orchestrator.py
