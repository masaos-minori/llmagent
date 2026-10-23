## Goal

Guard the behavior-preserving extraction of `check_empty_result_repeat()`
(`REQ-006`, `REQ-007`): assert `_scan_empty_result_repeat()` returns the same
tripping pair and `None` for the same boundary cases the existing 34 tests use and
writes nothing, while `check_empty_result_repeat()` still logs, still writes one
`guard_hint` with the same fields, and still returns the same text. Also assert
the disabled-option boundary.

## Scope

`tests/agent/test_tool_loop_guard.py` only. Adds one new test class to the
existing file; the 34 existing tests must keep passing unchanged. Reference reads:
`scripts/agent/tool_loop_guard.py` (the split, row 4), `scripts/agent/context.py`
(the diagnostics the scan must not write to). Dependent production file:
`scripts/agent/tool_loop_guard.py`.

## Assumptions

- The existing 34 tests exercise the threshold boundary cases; the new scan test
  reuses the same inputs and asserts identical `(tool_name, count)` / `None`
  outputs.
- `ctx.diagnostics` is reachable so the "writes nothing" assertion can be made on
  the scan path.

## Design decisions

- `TestNonRecordingScanIsEquivalentToTheCheck`: parametrize over the existing 30
  boundary cases; assert `_scan_empty_result_repeat()` equals what
  `check_empty_result_repeat()` would return on the scan portion, and that no
  diagnostic was written.
- `TestDisabledOptionIsInert`: with `tool_empty_result_max_repeats <= 0` the scan
  returns `None` (`REQ-006` boundary).

## Alternatives considered

- Rewriting the existing tests against the scan directly — would weaken coverage of
  the recording wrapper; keep both the wrapper test and the scan-equivalence test.

## Implementation

### Target file

`tests/agent/test_tool_loop_guard.py`

### Procedure

Add one class after the existing tests:

1. `TestNonRecordingScanIsEquivalentToTheCheck`:
   - For each of the existing boundary cases, assert
     `_scan_empty_result_repeat()` returns the same tripping `(tool_name, count)`
     or `None` as the current `check_empty_result_repeat()` scan half, and that it
     wrote nothing to `ctx.diagnostics`.
   - Assert `check_empty_result_repeat()` still logs (capture `caplog`), still
     writes exactly one `guard_hint` with the same fields, and still returns the
     same text (`REQ-007`, `AC-5`).
2. `TestDisabledOptionIsInert`: with `tool_empty_result_max_repeats <= 0`, assert
   the scan returns `None` (`REQ-006`).

### Method

- Append the class; reuse the existing guard-construction helper in this file.
- Read the existing test cases to copy their boundary inputs exactly.

### Details

- The "writes nothing" assertion distinguishes the scan (row 4) from the
  recording wrapper: the mid-round path must not double-write `guard_hint`.

## Compatibility considerations

- Additive; the 34 existing tests are not edited (`REQ-006`).

## Security considerations

- N/A: test-only.

## Rollback considerations

- Delete the added class; `git checkout -- tests/agent/test_tool_loop_guard.py`
  restores HEAD.

## Validation plan

- `uv run pytest tests/agent/test_tool_loop_guard.py -q --timeout=120` — all 34
  existing tests plus the two new classes pass.
- `uv run ruff check tests/`, `uv run ruff format --check tests/`.

## Completion criteria

`_scan_empty_result_repeat()` matches `check_empty_result_repeat()`'s scan output
on every boundary case and writes no diagnostic; `check_empty_result_repeat()`
still writes exactly one `guard_hint` and returns the same text; the disabled
option returns `None`; all existing tests pass.

## Out of Scope

- The round-level pairing tests — `tests/agent/test_tool_runner.py` (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestNonRecordingScanIsEquivalentToTheCheck (REQ-007) | Pending | — | — | Phase 2 |
| 2 | Add TestDisabledOptionIsInert (REQ-006) | Pending | — | — | Phase 2 |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-007, REQ-013
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `tests/agent/test_tool_loop_guard.py`
