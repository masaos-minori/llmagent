## Goal

Attach the same redaction-filter helper to `tool_transport_invoker.py`'s module-level logger, so `_record_transport_error()`'s `logger.warning("transport failure for %r: %s (state=%s)", ...)` (lines 155-157) is covered by redaction.

## Scope

- Modify `tool_transport_invoker.py`'s module-level logger initialization (line 22).

## Assumptions

- The new `attach_redaction_filter()` helper exists (covered in previous row).
- `_record_transport_error()` logs the `TransportError`'s `str(e)` which may contain server-provided fields.

## Design decisions

- Call `attach_redaction_filter(logger)` immediately after the existing `logger = logging.getLogger(__name__)` line.

## Alternatives considered

- Importing `_RedactionFilter` directly into this module — rejected: violates the principle of keeping private symbols contained within `shared/logger.py`.
- Adding a parameter to `register_secret()` to also attach the filter — rejected: mixes concerns.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. Import the new helper.
2. Call `attach_redaction_filter()` on the module-level logger.

### Method

- **Step 1**: After line 22 (`logger = logging.getLogger(__name__)`):

```python
# Line 22 (unchanged):
logger = logging.getLogger(__name__)

# After line 22:
from shared.logger import attach_redaction_filter  # REQ-006

attach_redaction_filter(logger)  # REQ-006
```

### Details

**Step 1 — Attach redaction filter:**

After line 22 (`logger = logging.getLogger(__name__)`):

```python
from shared.logger import attach_redaction_filter  # REQ-006

attach_redaction_filter(logger)  # REQ-006
```

This ensures that any `TransportError` logged via `_record_transport_error()` will have its content redacted according to the registered secrets.

## Compatibility considerations

- Existing log-output assertions in `tests/shared/test_tool_transport_invoker.py` and `tests/shared/test_tool_transport_invoker_merge.py` may need updating if they check for unredacted content.
- No behavioral change to the transport logic itself — only log output is affected.

## Security considerations

- Applies secret redaction to previously-unprotected loggers — security improvement.

## Rollback considerations

- Reverting removes the redaction filter but does not affect other functionality.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py -v`
- Verify existing assertions still pass (or update them if they check for unredacted content).
- Static analysis: `uv run ruff check scripts/shared/tool_transport_invoker.py`, `uv run mypy scripts/shared/tool_transport_invoker.py`.

## Completion criteria

- Redaction filter attached to module-level logger.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `_record_transport_error()` behavior — out of scope.
- Modifying `TransportError` or `ToolCallResult` schema — out of scope.
- Modifying `HttpTransport.call()` — covered in previous row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Attach redaction filter to module-level logger | Completed | 20260917-191707 | 20260917-191707 |  |
| 2 | Update test assertions if needed | Completed | 20260917-191707 | 20260917-191707 |  |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-191708 | 20260917-191708 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-191708 | 20260917-191708 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-103224_mcpagent06_http-retry-backoff-safe-diagnostics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-124248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/tool_transport_invoker.py