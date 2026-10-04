## Goal

Clarify the `strict_mode` behavior in `ToolRouteResolver` documentation to prevent future confusion during code reviews and refactoring (REQ-001, REQ-002).

## Scope

- Update the class-level docstring of `ToolRouteResolver` to clarify the `strict_mode` behavior.
- Ensure consistency between class-level and parameter-level documentation.

## Assumptions

- The fix will update the class-level docstring to clarify the `strict_mode` behavior.
- No API contract changes are required for callers of `HttpTransport.call()`.
- The existing retry logic (number of retries, backoff strategy) remains unchanged.

## Design decisions

- Approach 1 (update class-level docstring) is preferred over Approach 2 (keep current documentation):
  - Provides better visibility for developers who only read the class-level docstring.
  - Ensures consistent documentation across all levels.
  - Prevents misinterpretation during code reviews and refactoring.

## Alternatives considered

- Keep current documentation as-is, since the parameter-level docstring already correctly explains the `strict_mode` behavior: rejected because developers who only read the class-level docstring may assume that `strict_mode=False` means `ValueError` is not raised.

## Implementation

### Target file

`scripts/shared/route_resolver.py`

### Procedure

1. Check existing tests for `strict_mode` behavior (UNK-01; `tests/shared/test_route_resolver.py`).
2. Determine minimum Python version supported (UNK-02; review `pyproject.toml`).
3. Update class-level docstring in `scripts/shared/route_resolver.py`.
4. Run tests to confirm the change works correctly.
5. Verify documentation consistency manually.

### Method

- Locate lines 26-31 in `scripts/shared/route_resolver.py`:
  ```python
  class ToolRouteResolver:
      """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

      RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
      when the tool is not found there.
      """
  ```
- Replace the class-level docstring with:
  ```python
  class ToolRouteResolver:
      """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

      RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
      when the tool is not found there. Note: both `strict_mode=True` and `strict_mode=False`
      always raise ValueError on an unresolved tool — the difference is in error-message
      wording only.
      """
  ```

### Details

Current state (lines 26-31):
```python
class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
    when the tool is not found there.
    """
```

After modification:
```python
class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
    when the tool is not found there. Note: both `strict_mode=True` and `strict_mode=False`
    always raise ValueError on an unresolved tool — the difference is in error-message
    wording only.
    """
```

The added clarification ensures that:
- Developers who only read the class-level docstring understand that `ValueError` is always raised on unresolved tools.
- The distinction between `strict_mode=True` and `strict_mode=False` is clear: it's only about error-message wording, not about whether `ValueError` is raised.
- Consistency with the parameter-level docstring is maintained.

## Compatibility considerations

- The change affects documentation but not runtime behavior.
- Callers that rely on `ValueError` being raised will continue to work correctly.
- The error message wording difference between `strict_mode=True` and `strict_mode=False` remains unchanged.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Reverting the change is straightforward — restore the original class-level docstring. If the decision was made incorrectly, revert and re-evaluate.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/route_resolver.py | Documentation consistency validation | Manual review | Documentation consistent |
| tests/shared/test_route_resolver.py | Unit test suite | `uv run pytest tests/shared/test_route_resolver.py` | All tests pass |

## Completion criteria

- Class-level docstring accurately reflects the `strict_mode` behavior (AC-001).
- Documentation remains consistent with parameter-level docstring (AC-002).
- Existing tests pass after the change (AC-003).

## Out of scope

- Changing the retry logic itself.
- Modifying other transport layers.
- Changing error handling behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check existing tests for strict_mode behavior | Done | — | — | |
| 2 | Determine minimum Python version supported | Done | — | — | Python >=3.13 confirmed |
| 3 | Update class-level docstring | Done | — | — | Added strict_mode clarification |
| 4 | Validate tests pass | Done | — | — | ruff OK; 20 passed |
| 5 | Verify documentation consistency | Done | — | — | Manual review |

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
- **Source issue**: issues/20261003-152247_route_resolver_strict_mode_documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-154435_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-064552
- **Related target files**: scripts/shared/route_resolver.py
