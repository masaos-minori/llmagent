## Goal

Create a new unit test file `tests/shared/test_transport_dto.py` pinning `from_transport()` behavior: `is_error=True` → `"tool"`, `is_error=False` → `""`, `source == "mcp"`, `server_key == ""`. (REQ-003 / AC-4)

## Scope

- Create a new file `tests/shared/test_transport_dto.py`
- Add unit tests for `ToolCallResult.from_transport()` covering:
  - `is_error=True` → `error_type == "tool"`
  - `is_error=False` → `error_type == ""`
  - `source == "mcp"`
  - `server_key == ""`

## Assumptions

- The file will follow the conventions of sibling files in `tests/shared/` (e.g. `test_action_result.py`)
- The directory `tests/shared/` already exists
- Adding this file does not collide with any expected test-discovery convention

## Design decisions

- Follow sibling files in `tests/shared/` (e.g. `test_action_result.py`) for naming and structure conventions
- Pin the exact behavior of `from_transport()` — this is a regression fix, so the test must prevent future regressions

## Alternatives considered

- Adding tests to an existing file in `tests/shared/` — rejected because a dedicated file provides clearer ownership and prevents drift from unrelated tests

## Implementation

### Target file

`tests/shared/test_transport_dto.py`

### Procedure

1. Create `tests/shared/test_transport_dto.py` with unit tests for `from_transport()`

### Method

- Create a new test file following the pattern of sibling files in `tests/shared/`
- Add tests for both `is_error=True` and `is_error=False` cases

### Details

**New file: `tests/shared/test_transport_dto.py`:**
```python
"""Unit tests for ToolCallResult.from_transport().

Pins the behavior of from_transport(): is_error=True → error_type="tool",
is_error=False → error_type="", source="mcp", server_key="".
"""

import pytest

from scripts.shared.transport_dto import ToolCallResult


class TestFromTransport:
    """Tests for ToolCallResult.from_transport()."""

    def test_from_transport_is_error_true_yields_tool(self) -> None:
        """is_error=True yields error_type='tool'."""
        result = ToolCallResult.from_transport(
            output="error message",
            is_error=True,
            request_id="123",
        )
        assert result.error_type == "tool"
        assert result.source == "mcp"
        assert result.server_key == ""
        assert result.is_error is True

    def test_from_transport_is_error_false_yields_empty(self) -> None:
        """is_error=False yields error_type=''."""
        result = ToolCallResult.from_transport(
            output="success",
            is_error=False,
            request_id="456",
        )
        assert result.error_type == ""
        assert result.source == "mcp"
        assert result.server_key == ""
        assert result.is_error is False
```

## Compatibility considerations

- This is a new file addition — no existing code is modified
- The file follows the conventions of sibling files in `tests/shared/`
- No test-discovery convention conflicts expected

## Security considerations

- This is a test file — no security implications
- The test pins the correct `error_type` classification, preventing future regressions

## Rollback considerations

- If the test fails due to the current `"transport"` default, it confirms the regression exists
- The test should be added alongside the fix (SEQ-01), not before it

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_transport_dto.py` | Unit: `from_transport()` classification | `.venv/bin/python -m pytest tests/shared/test_transport_dto.py -q -p no:cacheprovider -p no:randomly` | Both tests pass after SEQ-01; `is_error=True` → `"tool"`, `is_error=False` → `""` |

## Completion criteria

- File `tests/shared/test_transport_dto.py` exists
- Tests cover `is_error=True` → `"tool"` and `is_error=False` → `""`
- Tests cover `source == "mcp"` and `server_key == ""`
- All tests pass after SEQ-01 is applied

## Out of scope

- Modifying any existing test file
- Changing the `error_type` vocabulary ("transport" | "tool" | "")
- Changing `server_key` handling
- Changing the transport error path
- Changing retry logic or health tracking
- Renaming or re-scoping `from_transport()`; redesigning `ToolCallResult`
- Optional: asserting `ctx.diagnostics.save_transport_failure` is not called for an HTTP tool-level error

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/shared/test_transport_dto.py` | Pending | — | — | REQ-003 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261005-121408_trn001_http-tool-level-errors-are-reported-with-error_type-transport-instead-of-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-224839_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115650
- **Related target files**: tests/shared/test_transport_dto.py
