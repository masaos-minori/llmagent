## Goal

Add a small public helper function to `scripts/shared/logger.py` that attaches `_RedactionFilter()` to an arbitrary `logging.Logger` instance, for use by library modules that use bare `logging.getLogger(__name__)`.

## Scope

- Add `attach_redaction_filter(logger: logging.Logger) -> None` to `scripts/shared/logger.py`.

## Assumptions

- `_RedactionFilter` is already defined in `scripts/shared/logger.py` (lines 41-52).
- The helper should follow the same style as the existing `register_secret()` function (lines 35-38).

## Design decisions

- Name the helper `attach_redaction_filter` per UNK-01 resolution (consistent with `register_secret`'s naming style).
- The helper performs `target_logger.addFilter(_RedactionFilter())` — a one-liner matching the existing pattern.

## Alternatives considered

- Importing `_RedactionFilter` directly into each caller module — rejected: violates the principle of keeping private symbols contained within `shared/logger.py`.
- Adding a parameter to `register_secret()` to also attach the filter — rejected: mixes concerns (secret registration vs. log filtering).

## Implementation

### Target file

`scripts/shared/logger.py`

### Procedure

1. Add `attach_redaction_filter()` public helper function after `register_secret()`.

### Method

- **Step 1**: Add the helper function after `register_secret()` (around line 38):

```python
# After register_secret():
def attach_redaction_filter(logger: logging.Logger) -> None:
    """Attach the _RedactionFilter to a logger so registered secrets are redacted from its output."""
    logger.addFilter(_RedactionFilter())
```

### Details

**Step 1 — Add the helper:**

After line 38 (`register_secret()` function body), add:

```python
def attach_redaction_filter(logger: logging.Logger) -> None:
    """Attach the _RedactionFilter to a logger so registered secrets are redacted from its output."""
    logger.addFilter(_RedactionFilter())
```

The function is a thin wrapper around `logger.addFilter(_RedactionFilter())`, following the same minimal-public-helper pattern as `register_secret()`.

## Compatibility considerations

- No compatibility impact. This is a new public function addition only.
- Existing callers of `register_secret()` are unaffected.

## Security considerations

- This helper enables secret redaction on previously-unprotected loggers — a security improvement.

## Rollback considerations

- Reverting removes the helper but does not affect other functionality.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_logger.py -v`
- Verify the helper attaches `_RedactionFilter` correctly.
- Static analysis: `uv run ruff check scripts/shared/logger.py`, `uv run mypy scripts/shared/logger.py`.

## Completion criteria

- `attach_redaction_filter()` function added to `scripts/shared/logger.py`.
- Helper follows the same style as `register_secret()`.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `_RedactionFilter` itself — out of scope.
- Changing `Logger._configure_logger()` behavior — out of scope.
- Any change to `http_transport.py` or `tool_transport_invoker.py` — covered in subsequent rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add attach_redaction_filter() helper | Pending | — | — | |
| 2 | Add unit test for the helper | Pending | — | — | See next row |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: scripts/shared/logger.py
