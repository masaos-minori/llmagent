# Implementation Procedure: `tests/agent/test_tool_result_formatter.py`

## Goal

Unit-test the failure-text contract directly, without a full round fixture. Implements `REQ-004`: the text carries the fixed `[Tool execution failed: ...]` marker, the exception class name, the message, and an empty message still yields a usable line.

## Scope

Add `TestExecutionFailureText` (new) to `tests/agent/test_tool_result_formatter.py`, following the `TestTurnLimitHint` pattern (`tests/agent/test_tool_result_formatter.py:177`), and add `build_execution_failure_text` to the module import block (`:9-14`). Do not modify any existing test.

## Assumptions

- `turn_limit_hint` is already imported and tested in this file (`:9`, `:177`); add `build_execution_failure_text` to the same import.
- Construct exceptions directly (`ValueError("disk full")`, `RuntimeError()`) to drive the marker/class/message and empty-message cases.

## Design decisions

- **Direct unit test of the builder.** The builder is a pure string function; testing it here (as `TestTurnLimitHint` tests `turn_limit_hint`) decouples the text contract from the round-wiring tested in `tests/agent/test_tool_runner.py` (row 3).

## Alternatives considered

- **Asserting the marker through a full `execute_all_tool_calls` round.** Rejected: that belongs to row 3; the text contract itself is cleaner to pin at the builder.

## Implementation

### Target file

`tests/agent/test_tool_result_formatter.py`

### Procedure

1. Add `build_execution_failure_text` to the import block (`tests/agent/test_tool_result_formatter.py:9-14`):

   ```python
   from agent.tool_result_formatter import (
       build_execution_failure_text,
       build_github_preview,
       build_preview,
       mask_args,
       turn_limit_hint,
   )
   ```

2. Add `class TestExecutionFailureText` after `TestTurnLimitHint` (below `:194`):

   ```python
   class TestExecutionFailureText:
       def test_marker_class_and_message_present(self) -> None:
           text = build_execution_failure_text(ValueError("disk full"))
           assert "[Tool execution failed:" in text
           assert "ValueError" in text
           assert "disk full" in text
           assert text.endswith("]")

       def test_empty_message_still_usable(self) -> None:
           text = build_execution_failure_text(RuntimeError())
           assert "[Tool execution failed:" in text
           assert "RuntimeError" in text
           assert text.endswith("]")
   ```

### Method

Edit in place: update the import (one edit), append the class (one edit). Verify with `git diff` that only the import and the new class changed.

## Compatibility considerations

N/A: adds one test class; no production code touched.

## Security considerations

N/A: test-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py -v`: `TestExecutionFailureText` (new) passes; all existing cases pass unmodified.

## Completion criteria

- `TestExecutionFailureText` (new) asserts the marker, the class name, the message, and the empty-message case.
- Every existing test in the file passes.

## Out of Scope

- The builder implementation in `scripts/agent/tool_result_formatter.py` (row 2).
- The round-level row-text assertion in `tests/agent/test_tool_runner.py` (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestExecutionFailureText` (new) following the `TestTurnLimitHint` pattern | Completed | — | 20261023-181912 | Follows the existing text-builder test pattern Stale detector clean after marking TestExecutionFailureText (new). Import added alphabetically. |
| 2 | Run the formatter unit tests | Completed | — | 20261023-181912 | Existing cases must pass unmodified 30 formatter tests pass (28 existing unmodified + 2 new TestExecutionFailureText). Test-only; no production/doc change. |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: tests/agent/test_tool_result_formatter.py