## Goal

Fix `tests/integration/test_robustness_chaos.py::TestToolLoopGuardChaos`'s 8 `ToolLoopGuard.check_all(...)` call sites (3 failing tests) to pass a `round_tool_names` argument in the correct (3rd) position (REQ-005).

## Scope

In scope: the 8 `check_all(...)` calls inside `TestToolLoopGuardChaos` (lines ~72, 73, 88, 94, 100, 152, 153, 161) only.

## Assumptions

- `round_tool_names=[]` is behavior-neutral for these 3 tests (cycle/dedup-focused chaos-scenario assertions, no stagnation-detection assertions), per the Plan's confirmed evidence.

## Design decisions

- Insert `[]` as the 3rd positional argument at each call site, matching the existing positional-argument style.

## Alternatives considered

- Converting to keyword arguments: rejected as unnecessarily larger diff than positional insertion.

## Implementation

### Target file

`tests/integration/test_robustness_chaos.py`

### Procedure

1. Re-confirm each `guard.check_all(...)` call's exact current line/form inside `TestToolLoopGuardChaos` via `rg -n "check_all\(" tests/integration/test_robustness_chaos.py`.
2. For each of the 8 calls, insert `[]` as the 3rd positional argument.

### Method

Direct positional-argument insertion at 8 call sites — no signature or logic change.

### Details

- Before pattern: `guard.check_all(<arg1>, <arg2>, <arg3>, <arg4>)` — 4 positional args (some calls span multiple lines per existing formatting; preserve each call's existing multi-line style when inserting the new argument).
- After pattern: `guard.check_all(<arg1>, <arg2>, [], <arg3>, <arg4>)` — 5 positional args matching the current `check_all` signature.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix.

## Rollback considerations

- `git revert` the commit, or manually remove the inserted `[]` arguments.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/integration/test_robustness_chaos.py` | Integration | `uv run pytest tests/integration/test_robustness_chaos.py::TestToolLoopGuardChaos -q` | All 3 tests pass |

## Completion criteria

- `uv run pytest tests/integration/test_robustness_chaos.py::TestToolLoopGuardChaos -q` passes.
- `uv run pytest tests/integration/test_robustness_chaos.py -q` (full file) passes with no regression.

## Out of scope

- Other target files from this same Plan (each has its own implementation procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Inserted `[]` as 3rd positional arg at 8 call sites in TestToolLoopGuardChaos |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 5 TestToolLoopGuardChaos tests pass; all 14 total pass |
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
- **Requirement ID**: REQ-005: fix `check_all(...)` call sites in `tests/integration/test_robustness_chaos.py::TestToolLoopGuardChaos`
- **Source issue**: issues/20260927-075237_agent001_toolloopguard.check_all-requires-message-argument-callers-do-not-pass.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081106_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091211
- **Related target files**: tests/integration/test_robustness_chaos.py
