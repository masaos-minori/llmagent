## Goal

Fix the `error_type` default value in `ToolCallResult.from_transport()` to correctly reflect transport-level errors instead of tool-level errors (REQ-001, REQ-002).

## Scope

- Fix the `error_type` default value in `ToolCallResult.from_transport()`.
- Update related documentation if needed.

## Assumptions

- The fix will change the default `error_type` value from `"tool"` to `"transport"` in `from_transport()`.
- No API contract changes are required for callers of `HttpTransport.call()`.
- The existing retry logic (number of retries, backoff strategy) remains unchanged.

## Design decisions

- Approach 1 (change default value) is preferred over Approach 2 (add parameter):
  - Simpler and more maintainable.
  - The `from_transport()` method is specifically for transport-layer results, so `"transport"` is the correct default.
  - Callers that need `"tool"` error_type can override via `dataclasses.replace()`.

## Alternatives considered

- Add an optional `error_type` parameter to `from_transport()`: rejected because it adds unnecessary complexity for a single-use case.

## Implementation

### Target file

`scripts/shared/transport_dto.py`

### Procedure

1. Check existing tests for `error_type` values (UNK-01; `tests/shared/test_transport_dto.py`).
2. Determine minimum Python version supported (UNK-02; review `pyproject.toml`).
3. Change default `error_type` value in `scripts/shared/transport_dto.py`.
4. Run tests to confirm the change works correctly.
5. Verify error_type field is correct for transport-level errors.

### Method

- Locate lines 18-30 in `scripts/shared/transport_dto.py`:
  ```python
  @classmethod
  def from_transport(
      cls, output: str, is_error: bool, request_id: str = ""
  ) -> "ToolCallResult":
      """Construct a ToolCallResult with default server_key and error_type."""
      return cls(
          output=output,
          is_error=is_error,
          request_id=request_id,
          server_key="",
          source="mcp",
          error_type="tool" if is_error else "",
      )
  ```
- Replace line 29 (`error_type="tool" if is_error else ""`) with:
  ```python
  error_type="transport" if is_error else "",
  ```

### Details

Current state (lines 18-30):
```python
@classmethod
def from_transport(
    cls, output: str, is_error: bool, request_id: str = ""
) -> "ToolCallResult":
    """Construct a ToolCallResult with default server_key and error_type."""
    return cls(
        output=output,
        is_error=is_error,
        request_id=request_id,
        server_key="",
        source="mcp",
        error_type="tool" if is_error else "",
    )
```

After modification:
```python
@classmethod
def from_transport(
    cls, output: str, is_error: bool, request_id: str = ""
) -> "ToolCallResult":
    """Construct a ToolCallResult with default server_key and error_type."""
    return cls(
        output=output,
        is_error=is_error,
        request_id=request_id,
        server_key="",
        source="mcp",
        error_type="transport" if is_error else "",
    )
```

The change ensures that:
- Transport-level errors have `error_type="transport"` instead of `error_type="tool"`.
- Debugging and incident investigation can identify the root cause of transport failures more quickly.
- Callers that need `"tool"` error_type can override via `dataclasses.replace(parsed, error_type="tool")`.

Note: The `server_key=""` default is documented in the dataclass field definition (line 14) and does not require additional documentation changes.

## Compatibility considerations

- The change affects error type classification — transport-level errors will now have `error_type="transport"` instead of `error_type="tool"`.
- Callers that rely on `error_type="tool"` for all errors will see different behavior.
- Callers that use `dataclasses.replace()` to override `error_type` will continue to work correctly.

## Security considerations

N/A: error handling change only.

## Rollback considerations

Reverting the change is straightforward — restore the original `error_type="tool" if is_error else ""` line. If the decision was made incorrectly, revert and re-evaluate.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/transport_dto.py | Error type validation | Manual test with transport-level error | error_type is "transport" |
| tests/shared/test_transport_dto.py | Unit test suite | `uv run pytest tests/shared/test_transport_dto.py` | All tests pass |

## Completion criteria

- `error_type` correctly reflects transport-level errors (AC-001).
- `server_key` default value is documented (AC-002).
- Existing tests pass after the change (AC-003).

## Out of scope

- Changing the retry logic itself.
- Modifying other transport layers.
- Changing error handling behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check existing tests for error_type values | Done | — | — | No dedicated test file found |
| 2 | Determine minimum Python version supported | Done | — | — | Python >=3.13 confirmed |
| 3 | Change default error_type value | Done | — | — | "tool" → "transport" |
| 4 | Validate tests pass | Done | — | — | ruff OK; 1 pre-existing failure (unrelated) |
| 5 | Verify error_type field correctness | Done | — | — | http_transport.py call site verified |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261003-152247_transport_dto_default_server_key.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-154033_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-180548
- **Related target files**: scripts/shared/transport_dto.py
