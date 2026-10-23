# Implementation Procedure: `scripts/agent/tool_result_formatter.py`

## Goal

Add the private helper that builds the LLM-facing text for a tool call whose execution raised, captured by `_run_group_call` in `scripts/agent/tool_runner.py`. Implements `REQ-003` (the failure row reuses the existing six-field shape) and `REQ-004` (the text names the exception class and message behind a fixed bracketed marker distinguishing an execution failure from a tool-reported error and from a preparation rejection, in the style of `turn_limit_hint`), while keeping `scripts/agent/tool_runner.py` inside its byte-size headroom (`REQ-013`).

## Scope

Add exactly one private function `build_execution_failure_text` to `scripts/agent/tool_result_formatter.py`, with a docstring in the module's existing style. Do not modify any existing function (`turn_limit_hint`, `mask_args`, `build_preview`, or the `_preview_*` helpers) or the module's public surface. The caller in `scripts/agent/tool_runner.py` is added in row 1.

## Assumptions

- The six-field row has no `error_type` position (`scripts/agent/tool_runner.py:150`, `scripts/agent/tool_preparation.py:37`), so the failure is carried as a text marker, consistent with preparation rejections and transport errors.
- An empty exception message must still yield a usable single-line marker (no dangling colon or brackets).

## Design decisions

- **Text builder in the formatting module, not in `tool_runner.py`.** `tool_result_formatter.py` already owns result preview and hint text (`turn_limit_hint`, `:12-24`); `tool_runner.py` has only 858 B of headroom before the 16384 B gate. Keeping the helper private avoids a new row in the generated agent reference table (`docs/23_agent/agent_13_reference-api-generated.md:179`, `:184` list public symbols only).
- **Fixed bracketed marker + class + message.** The marker brackets the text so the model can tell an execution failure apart from a bare tool-reported error string or a preparation-rejection reason; the class name and `str(exc)` let it gauge severity. `str(exc)` in LLM-facing output follows the precedent at `scripts/shared/tool_transport_invoker.py:209`, `:219`.

## Alternatives considered

- **Building the marker inline in `_run_group_call`.** Rejected: it would push text construction into `tool_runner.py`, consuming its byte headroom and splitting the result-text ownership that `turn_limit_hint` already establishes here.

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py`

### Procedure

1. Add `build_execution_failure_text` directly after `turn_limit_hint` (below `scripts/agent/tool_result_formatter.py:24`), before `mask_args`. Match `turn_limit_hint`'s one-paragraph docstring style:

   ```python
   def build_execution_failure_text(exc: Exception) -> str:
       """Build the LLM-facing text for a tool call whose execution raised.

       Mirrors turn_limit_hint(): a fixed bracketed marker that distinguishes an
       execution failure from a tool-reported error and from a preparation
       rejection, followed by the exception class name and message so the model
       can gauge severity. An empty message still yields a usable single-line
       marker.
       """
       class_name = type(exc).__name__
       message = str(exc).strip()
       detail = f"{class_name}: {message}" if message else class_name
       return f"[Tool execution failed: {detail}]"
   ```

   The marker `[Tool execution failed: ...]` is the fixed bracketed sentinel asserted by the unit test in `tests/agent/test_tool_result_formatter.py` (row 4). Keep it a single literal so both the builder and the test reference the same string.

### Method

Edit in place: insert the function between `turn_limit_hint` and `mask_args`. Verify with `git diff` that only the new function was added and every existing function is byte-identical to HEAD.

### Details

- `str(exc).strip()` normalizes surrounding whitespace so a message of only spaces collapses to the class-name-only marker.
- The function is module-private (leading underscore convention is not required for a non-exported name, but it is not added to any `__all__`; the module has none). It is imported by name in `scripts/agent/tool_runner.py` (row 1).

## Compatibility considerations

N/A: the module's public functions are unchanged; this adds one private helper consumed by exactly one production caller (row 1).

## Security considerations

N/A: the helper only formats `type(exc).__name__` and `str(exc)`; redaction of paths/URLs in the logging path is handled by `scripts/shared/logger.py:64` `_RedactionFilter`, and the row is truncated by the caller through `_truncate_for_llm`.

## Rollback considerations

N/A: revert the commit (single added function).

## Validation plan

- Unit: `uv run pytest tests/agent/test_tool_result_formatter.py -v`; the new `TestExecutionFailureText` (row 4) asserts the marker, the class name, the message, and the empty-message case.
- Module-size gate: `uv run python tools/check_module_size.py --top 5`. Both files pass; `tool_runner.py` stays under 16384 B.
- Architecture boundary: `PYTHONPATH=scripts uv run lint-imports`. No new contract broken.

## Completion criteria

- `build_execution_failure_text` exists, returns a single-line string containing the fixed `[Tool execution failed: ...]` marker, the exception class name, and `str(exc)` when non-empty, and a usable class-name-only marker when the message is empty.
- Every existing function in the module is byte-identical to HEAD; `check_module_size.py` passes with no new finding.

## Out of Scope

- The caller in `scripts/agent/tool_runner.py` (row 1).
- Any change to the failure-row tuple shape (`scripts/agent/tool_preparation.py:37`) — a structured field would be a separate issue (`UNK-02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the private `build_execution_failure_text` helper in `scripts/agent/tool_result_formatter.py` | Pending | — | — | Private helper; keeps `agent_13` unchanged |
| 2 | Run validation (formatter unit tests, module-size, import checks) | Pending | — | — | Unit test authored in row 4 |

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
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-013`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: scripts/agent/tool_result_formatter.py
