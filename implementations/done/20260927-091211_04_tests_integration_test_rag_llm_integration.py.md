## Goal

Fix `tests/integration/test_rag_llm_integration.py`'s 4 `ToolLoopGuard.check_all(...)` call sites (2 failing tests: `test_c07_tool_loop_guard_fires_on_dedup`, `test_c08_tool_loop_guard_allows_different_args`) to pass a `round_tool_names` argument in the correct (3rd) position (REQ-004).

## Scope

In scope: the 4 `check_all(...)` calls in this file (lines ~221, 225, 249, 250) only.

## Assumptions

- `round_tool_names=[]` is behavior-neutral for these 2 tests (dedup-focused assertions, no stagnation-detection assertions), per the Plan's confirmed evidence.

## Design decisions

- Insert `[]` as the 3rd positional argument at each call site, matching the existing positional-argument style.

## Alternatives considered

- Converting to keyword arguments: rejected as unnecessarily larger diff than positional insertion.

## Implementation

### Target file

`tests/integration/test_rag_llm_integration.py`

### Procedure

1. Re-confirm each `guard.check_all(...)` call's exact current line/form via `rg -n "check_all\(" tests/integration/test_rag_llm_integration.py`.
2. For each of the 4 calls, insert `[]` as the 3rd positional argument.

### Method

Direct positional-argument insertion at 4 call sites — no signature or logic change.

### Details

- Before pattern: `guard.check_all(<arg1>, <arg2>, <arg3>, <arg4>)` — 4 positional args.
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
| `tests/integration/test_rag_llm_integration.py` | Integration | `uv run pytest tests/integration/test_rag_llm_integration.py -q` | All tests pass |

## Completion criteria

- `uv run pytest tests/integration/test_rag_llm_integration.py -q` passes with no failures.

## Out of scope

- Other target files from this same Plan (each has its own implementation procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Inserted `[]` as 3rd positional arg at 4 call sites |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 10 tests pass |
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
- **Requirement ID**: REQ-004: fix `check_all(...)` call sites in `tests/integration/test_rag_llm_integration.py`
- **Source issue**: issues/20260927-075237_agent001_toolloopguard.check_all-requires-message-argument-callers-do-not-pass.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081106_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091211
- **Related target files**: tests/integration/test_rag_llm_integration.py
