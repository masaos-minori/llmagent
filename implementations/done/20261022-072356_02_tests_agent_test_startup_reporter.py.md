## Goal

Add regression tests to `tests/agent/test_startup_reporter.py` that lock the
status-word behavior introduced in `scripts/agent/startup_reporter.py`: a
warning-only source reports `WARNING` (not `FAIL`), a `FATAL` outcome reports
`FATAL`, and an all-`SKIPPED` source reports `SKIPPED` (`REQ-007`; tests
`T-001`..`T-003`).

## Scope

- **In-Scope**:
  - Add a test asserting a warning-only RAG source renders `WARNING` and not `FAIL`
    (`T-001`, `REQ-001`).
  - Add a test asserting a RAG source with a `FATAL` outcome renders `FATAL`
    (`T-002`, `REQ-002`).
  - Add a test asserting a RAG source whose only outcome is `SKIPPED` renders
    `SKIPPED` (`T-003`, `REQ-003`).
  - Keep the existing four tests intact (`T-004`, `REQ-007`).
- **Out-of-Scope**:
  - Any change to `scripts/agent/startup_reporter.py` (that is a separate
    procedure).
  - Adding tests for sources other than `rag_consistency` (the existing
    `_readiness_message_for_rag` helper already drives one source per call; the
    three status words are produced identically for all three sources).

## Assumptions

- **ASM-001**: The existing module-level helpers `_readiness_message_for_rag`
  (line 67) and `_rag_line` (line 82) render a readiness summary for a pipeline
  with a single outcome of a given `StartupCheckStatus` and return the `RAG
  consistency:` line — reusable for the new cases without constructing a new
  pipeline each time.
- **ASM-002**: The status word is emitted immediately after `RAG consistency:` in
  the summary line, so `line.startswith("  RAG consistency: <WORD>")` pins the
  exact word.
- **ASM-003**: The three summary lines share one vocabulary (see the companion
  `startup_reporter.py` procedure), so locking the word for `rag_consistency`
  covers the behavior for `readiness` and `mcp_tool_discovery` too.

## Design decisions

- Reuse `_readiness_message_for_rag(status)` rather than building bespoke
  pipelines: it already exercises the real `report_readiness()` path and returns
  the rendered message, so each new test asserts on the actual output.
- Assert on the presence of the expected word and the absence of the legacy
  `FAIL` word for the warning-only case (`AC-001`); assert `startswith` for the
  `SKIPPED` case to pin the exact status position (`AC-003`).

## Alternatives considered

- Building a dedicated empty-pipeline fixture per test (mirroring
  `test_report_readiness_emits_readiness_summary`): rejected — the existing
  `_readiness_message_for_rag` helper already produces a one-outcome pipeline and
  is the established pattern in this file, so a new fixture would duplicate it.

## Implementation

### Target file

`tests/agent/test_startup_reporter.py`

### Procedure

1. Append `test_report_readiness_rag_line_shows_warning_not_fail` (new) after the last
   existing test (after line 99); assert the RAG line contains `WARNING` and not
   `FAIL` (`T-001`).
2. Append `test_report_readiness_rag_line_shows_fatal` (new); assert the RAG line
   contains `FATAL` (`T-002`).
3. Append `test_report_readiness_rag_line_shows_skipped_when_all_skipped` (new); assert
   the RAG line starts with `  RAG consistency: SKIPPED` (`T-003`).

### Method

Append the three functions at the end of the module (after
`test_report_readiness_rag_line_without_skip_shows_zero_skipped`, line 99). Each
calls `_readiness_message_for_rag(StartupCheckStatus.<CASE>)` and asserts on the
line returned by `_rag_line(...)`. The new function names are marked (new) below.

### Details

Append after line 99:

```python
def test_report_readiness_rag_line_shows_warning_not_fail() -> None:
    """REQ-001: a warning-only RAG check reports WARNING, not FAIL."""
    line = _rag_line(_readiness_message_for_rag(StartupCheckStatus.WARNING))

    assert "WARNING" in line
    assert "FAIL" not in line


def test_report_readiness_rag_line_shows_fatal() -> None:
    """REQ-002: a RAG check with a FATAL outcome reports FATAL."""
    line = _rag_line(_readiness_message_for_rag(StartupCheckStatus.FATAL))

    assert "FATAL" in line


def test_report_readiness_rag_line_shows_skipped_when_all_skipped() -> None:
    """REQ-003: a RAG check whose only outcome is SKIPPED reports SKIPPED."""
    line = _rag_line(_readiness_message_for_rag(StartupCheckStatus.SKIPPED))

    assert line.startswith("  RAG consistency: SKIPPED")
```

## Compatibility considerations

The new tests extend the existing suite; they do not modify any existing test.
They assert only on the status word, which the existing four tests never pinned
(`T-004`), so they add coverage without constraining unrelated behavior.

## Security considerations

N/A: test-only additions; no auth, secret, or crypto impact.

## Rollback considerations

Remove the three appended functions — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_startup_reporter.py` | Behavior: warning-only → `WARNING`, `FATAL` → `FATAL`, all-`SKIPPED` → `SKIPPED` | `pytest` | AC-007 |
| `tests/agent/` (full) | Regression | `pytest` | All green (AC-006, AC-007) |

## Completion criteria

- `test_report_readiness_rag_line_shows_warning_not_fail` (new) passes: warning-only RAG line shows `WARNING`, not `FAIL` (AC-001).
- `test_report_readiness_rag_line_shows_fatal` (new) passes: FATAL RAG line shows `FATAL` (AC-002).
- `test_report_readiness_rag_line_shows_skipped_when_all_skipped` (new) passes: all-`SKIPPED` RAG line starts with `  RAG consistency: SKIPPED` (AC-003).
- The existing four tests still pass (AC-007).

## Out of Scope

`scripts/agent/startup_reporter.py`, non-`rag_consistency` sources, governance documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-101600 | Appended T-001/T-002/T-003 regression tests to test_startup_reporter.py |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-101600 | Added warning-only->WARNING, FATAL->FATAL, all-SKIPPED->SKIPPED cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-101600 | ruff/mypy(1 file clean)/bandit H:0 M:0 (B101 assert=Low, expected in tests); pytest 7 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-101600 | N/A: no docs map to `test_startup_reporter.py` N/A: no docs/00_index.md task-scope mapping for test_startup_reporter.py |

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
- **Requirement ID**: REQ-007
- **Source issue**: `issues/done/20261021-220426_star003_fix-readiness-summary-mislabeling-warning-only-sources-as-fail.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-233223_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100900
- **Related target files**: `tests/agent/test_startup_reporter.py`