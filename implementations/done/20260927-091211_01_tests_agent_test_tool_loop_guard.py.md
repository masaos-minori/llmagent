## Goal

Fix `tests/agent/test_tool_loop_guard.py::TestCheckAll`'s 4 `ToolLoopGuard.check_all(...)` call sites (2 failing tests) to pass a `round_tool_names` argument in the correct (3rd) position, restoring the omitted final `message` argument (REQ-001).

## Scope

In scope: the `check_all(...)` call sites inside `TestCheckAll` in `tests/agent/test_tool_loop_guard.py` only. Out of scope: `scripts/agent/tool_loop_guard.py`'s current 5-parameter `check_all` signature and `scripts/agent/llm_turn_runner.py`'s call site — both confirmed already correct (Plan Reference Files evidence).

## Assumptions

- `round_tool_names=[]` is behavior-neutral for these 2 tests, since neither asserts on progress-stagnation detection (only cycle/dedup/retry-focused assertions, per the Plan's own confirmed evidence).

## Design decisions

- Insert `[]` as the 3rd positional argument at each call site, preserving each test's existing positional-argument style rather than switching to keyword arguments — minimal, localized diff.

## Alternatives considered

- Converting all `check_all(...)` calls to keyword arguments (`seen_calls=..., round_fingerprints=..., round_tool_names=[], failed_calls=..., message=...)`): rejected as a larger diff than necessary; positional insertion is sufficient and matches the existing call style.

## Implementation

### Target file

`tests/agent/test_tool_loop_guard.py`

### Procedure

1. Locate each `guard.check_all(...)` call inside `TestCheckAll` (confirmed via `rg -n "check_all\("` at lines ~233, ~243, ~246, ~249 — re-confirm exact current line numbers via `rg` before editing, since line numbers may have shifted since the Plan was written).
2. For each call, insert `[]` as the 3rd positional argument (after `round_fingerprints`, before `failed_calls`), so the call passes `(seen_calls_or_dict, round_fingerprints, [], failed_calls_or_set, message)`.

### Method

Direct positional-argument insertion at each of the 4 call sites — no signature or logic change.

### Details

- Before pattern (4 call sites, exact args vary per test): `guard.check_all(<arg1>, <arg2>, <arg3>, <arg4>)` — 4 positional args, missing the `round_tool_names` slot.
- After pattern: `guard.check_all(<arg1>, <arg2>, [], <arg3>, <arg4>)` — 5 positional args matching `check_all(self, seen_calls, round_fingerprints, round_tool_names, failed_calls, message)`'s current signature (`scripts/agent/tool_loop_guard.py:323-330`).
- Re-verify each call site's exact current form via Read immediately before editing (per adversarial verification — do not rely solely on the Plan's line numbers, which can drift).

## Compatibility considerations

- No production code changes; test-only fix restoring compatibility with the already-shipped `check_all` signature (added by commit `24e9e9b3`).

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- To rollback: `git revert` the commit containing this change, or manually remove the inserted `[]` arguments. No data migration or state involved.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_tool_loop_guard.py` | Unit | `uv run pytest tests/agent/test_tool_loop_guard.py -q` | All tests pass |

## Completion criteria

- `uv run pytest tests/agent/test_tool_loop_guard.py::TestCheckAll -q` passes (both previously-failing tests).
- `uv run pytest tests/agent/test_tool_loop_guard.py -q` (full file) passes with no regression.

## Out of scope

- `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`, `tests/integration/test_rag_llm_integration.py`, `tests/integration/test_robustness_chaos.py` (each covered by its own implementation procedure document from this same Plan).
- `scripts/agent/tool_loop_guard.py` and `scripts/agent/llm_turn_runner.py` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Inserted `[]` as 3rd positional arg at 4 call sites in TestCheckAll |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: fixing the existing call sites is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Both TestCheckAll tests pass; all 30 tests in file pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: fix `check_all(...)` call sites in `tests/agent/test_tool_loop_guard.py::TestCheckAll`
- **Source issue**: issues/20260927-075237_agent001_toolloopguard.check_all-requires-message-argument-callers-do-not-pass.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081106_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091211
- **Related target files**: tests/agent/test_tool_loop_guard.py
