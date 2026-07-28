## Goal

Add optional test to verify schema validation is invoked on all tool execution paths where schemas are available.

## Scope

**In-Scope:**
- Create a test that patches `validate_tool_arguments` to verify it's called on every path

**Out-of-Scope:**
- Fixing any actual gaps found during testing (would be a separate issue)
- Any changes beyond the test

## Assumptions

1. The current validation is called at `tool_runner.py:145` when `runtime_tools` is available
2. When no schema exists, validation cannot be performed (expected behavior)

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Are there any code paths where `runtime_tools` is available but validation is skipped? | Trace all execution paths through `execute_one_tool_call` | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_schema_validation_coverage.py`
  - `scripts/agent/tool_runner.py` — reference for understanding validation flow

- **Blast Radius:**
  - Very low churn — new test file only
  - Very low risk since change is test-only

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `tool_runner.py`:
```python
# Current validation flow:
async def execute_one_tool_call(ctx, tc, turn):
    # ... parse tool call
    validation_error = _validate_tool_args(ctx, name, args)
    if validation_error is not None:
        result = validation_error
    elif ctx.services_required.gateway is not None:
        result = await ctx.services_required.gateway.execute(ctx, name, args)
    # ... handle result
```

Test structure:
```python
import pytest
from unittest.mock import AsyncMock, patch
from agent.tool_runner import execute_one_tool_call

@pytest.mark.asyncio
async def test_validate_tool_arguments_called_on_all_paths():
    # Patch _validate_tool_args to track calls
    with patch("agent.tool_runner._validate_tool_args") as mock_validate:
        # Call execute_one_tool_call with various scenarios
        # Verify _validate_tool_args was called on each path
        pass

@pytest.mark.asyncio
async def test_validate_tool_arguments_not_called_when_no_schema():
    # Patch runtime_tools to return None for schema
    # Verify _validate_tool_args is NOT called when no schema exists
    pass
```

## Implementation

### Target file
`tests/test_schema_validation_coverage.py` (new file)

### Procedure
1. Create `tests/test_schema_validation_coverage.py`
2. Add imports for pytest, asyncio, unittest.mock, execute_one_tool_call
3. Implement `test_validate_tool_arguments_called_on_all_paths` — patch `_validate_tool_args`, verify it's called on each path
4. Implement `test_validate_tool_arguments_not_called_when_no_schema` — patch runtime_tools to return None for schema, verify `_validate_tool_args` is NOT called
5. Save the file

### Method
Create new test file with patched `_validate_tool_args` to verify validation is called on all paths.

### Details
- Use `@pytest.mark.asyncio` decorator for async tests
- Use `patch("agent.tool_runner._validate_tool_args")` to mock validation
- Track calls to `_validate_tool_args` using `mock_validate.assert_called_once()` or similar
- For schema-less scenario: patch `ctx.services_required.runtime_tools` to return None for schema
- Verify `_validate_tool_args` is NOT called when no schema exists

## Compatibility considerations

N/A — new test file has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: delete the new test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_schema_validation_coverage.py` | Mock-based assertion coverage | `uv run pytest -k "schema" -v` | Test passes |

## Out of scope

- Fixing any actual gaps found during testing (would be a separate issue)
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-165525_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-032823
- Related target files: scripts/agent/tool_runner.py, scripts/agent/tool_arg_validator.py
