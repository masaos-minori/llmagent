# HealthChecker uses __import__("httpx") instead of top-level import

## Priority
Low

## Summary
Replace inline `__import__("httpx")` calls in `HealthChecker.verify_running_async()` with a standard top-level import of `httpx`, matching the pattern used throughout the rest of the codebase.

## Background
`http_lifecycle_health_checker.py` uses `__import__("httpx")` inline at two locations:
- Line 49: `async with __import__("httpx").AsyncClient(timeout=timeout) as client:`
- Line 60: `except __import__("httpx").RequestError as exc:`

Meanwhile, `http_lifecycle.py` imports `httpx` at the top level (line 31):
```python
import httpx
```

And uses it normally:
```python
async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=hc_timeout)) as client:
```

## Problem
The inline `__import__("httpx")` pattern is inconsistent with the rest of the codebase and introduces several issues:

1. **Readability**: Inline imports are harder to read than top-level imports
2. **IDE support**: IDEs cannot provide autocomplete for `__import__("httpx")` results
3. **Static analysis**: Tools like mypy cannot infer types from inline imports
4. **Consistency**: Other modules in the same package use top-level imports

The inline import was likely added to avoid a circular import dependency, but this is unnecessary because:
- `http_lifecycle_health_checker.py` does not import anything from `http_lifecycle.py`
- There is no circular dependency between these modules
- The only shared dependency is `McpServerConfig` from `shared.mcp_config`

## Reason for Change
Inconsistent import patterns reduce code maintainability and make static analysis harder. Aligning with the existing convention (top-level import) eliminates the inline import anti-pattern.

## Implementation Intent
Add `import httpx` at the top of `http_lifecycle_health_checker.py` and replace both inline `__import__("httpx")` references with `httpx`. No behavioral change expected.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle_health_checker.py`

## Required Changes
- Add `import httpx` at the top of the file (after existing imports)
- Replace `__import__("httpx").AsyncClient` with `httpx.AsyncClient`
- Replace `__import__("httpx").RequestError` with `httpx.RequestError`

## Constraints
- Must not introduce any behavioral change
- Must preserve the existing exception handling logic

## Acceptance Criteria
- No inline `__import__("httpx")` calls remain
- Code passes type checking (mypy) without errors
- No regressions in health check functionality

## Testing Expectations
- Unit test verifying health check still works after import change
- Type check pass (mypy) without new errors
- Regression test for HTTP health check response parsing

## Documentation Impact
None — no docstring changes needed.

## Out of Scope
- Refactoring the health check logic
- Adding new features to the health checker

## Dependencies
N/A: none

## Unresolved Questions
- Was there ever a circular import dependency that justified the inline import?
- Should the inline import be replaced with a conditional import (`if TYPE_CHECKING`) instead?

## AI Implementation Instruction
Do not add any new functionality. Simply replace the two inline `__import__("httpx")` calls with a standard top-level `import httpx` and use `httpx.AsyncClient` and `httpx.RequestError` respectively. Verify no type errors are introduced.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-172956
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py
