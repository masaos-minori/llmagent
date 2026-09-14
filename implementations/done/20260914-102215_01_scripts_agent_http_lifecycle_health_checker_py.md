## Goal

Replace inline `__import__("httpx")` calls in `HealthChecker.verify_running_async()` with a standard top-level import of `httpx`, aligning with the codebase convention (REQ-001).

## Scope

- Replace two inline `__import__("httpx")` references with a top-level `import httpx` in `scripts/agent/http_lifecycle_health_checker.py`

## Assumptions

- No behavioral change is expected from replacing `__import__("httpx")` with `httpx`
- The conditional import at line 30 (`from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT`) remains unchanged — it is inside a method and avoids any circular import at module load time
- Adding a top-level `import httpx` is safe because `http_lifecycle.py` does not import from `http_lifecycle_health_checker.py`

## Design decisions

1. Add a top-level `import httpx` rather than using `TYPE_CHECKING` — `httpx.AsyncClient` and `httpx.RequestError` are used at runtime, not just for type hints, so `TYPE_CHECKING` is inappropriate here
2. Do not refactor health check logic or add new features — this is a straightforward import alignment task

## Alternatives considered

1. Using `TYPE_CHECKING` instead of a top-level import — rejected because `httpx.AsyncClient` and `httpx.RequestError` are used at runtime, not just for type hints
2. Leaving the inline imports as-is — rejected because they are inconsistent with the rest of the codebase and introduce several issues (readability, IDE support, static analysis, consistency)

## Implementation

### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

1. Search codebase for usages of `__import__("httpx")` to confirm no other instances exist
2. Add top-level import and replace inline references
3. Run type checking and tests

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `http_lifecycle.py:31` to confirm top-level `import httpx` exists (REQ-001; `scripts/agent/http_lifecycle_health_checker.py`)
- Re-run `rg "__import__.*httpx" scripts/agent/` to confirm only the two known instances exist (REQ-001; `scripts/agent/http_lifecycle_health_checker.py`)

Phase 2: Core Logic — replace inline imports with top-level import
- Add `import httpx` at the top of `http_lifecycle_health_checker.py` (after existing imports, REQ-001)
- Replace `__import__("httpx").AsyncClient` with `httpx.AsyncClient` at line 49 (REQ-001)
- Replace `__import__("httpx").RequestError` with `httpx.RequestError` at line 60 (REQ-001)

Phase 3: Deployment & Verification
- Run `uv run mypy scripts/agent/http_lifecycle_health_checker.py` to verify no type errors (REQ-002)
- Run existing tests to confirm no regression (REQ-003)

### Details

**Phase 1:** Verify via read/grep that:
- Inline `__import__("httpx")` confirmed at `scripts/agent/http_lifecycle_health_checker.py`:
  - Line 49: `async with __import__("httpx").AsyncClient(timeout=timeout) as client:`
  - Line 60: `except __import__("httpx").RequestError as exc:`
- Top-level `import httpx` exists in `http_lifecycle.py:31`
- No other instances of `__import__("httpx")` exist in `scripts/agent/` beyond the two above

**Phase 2:** Make the following changes:

1. **Add top-level import** after existing imports in `http_lifecycle_health_checker.py`:
   ```python
   import httpx
   ```

2. **Replace line 49**:
   Before:
   ```python
   async with __import__("httpx").AsyncClient(timeout=timeout) as client:
   ```
   After:
   ```python
   async with httpx.AsyncClient(timeout=timeout) as client:
   ```

3. **Replace line 60**:
   Before:
   ```python
   except __import__("httpx").RequestError as exc:
   ```
   After:
   ```python
   except httpx.RequestError as exc:
   ```

## Compatibility considerations

This is a low-risk refactoring change. No backward compatibility concerns — `httpx` is already a dependency of the project (used by `http_lifecycle.py`), so it will be available in all environments where the code runs.

## Security considerations

No security impact — this is a cosmetic change that improves code maintainability without altering behavior.

## Rollback considerations

Simple revert: restore the original inline imports. The underlying functionality remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Type check — verify mypy passes after import change | `uv run mypy scripts/agent/http_lifecycle_health_checker.py` | Clean (no errors) |
| scripts/agent/http_lifecycle_health_checker.py | Static check — verify no remaining inline imports | `rg "__import__.*httpx" scripts/agent/http_lifecycle_health_checker.py` | Zero matches |
| scripts/agent/http_lifecycle_health_checker.py | Unit test — verify health check functionality preserved | `uv run pytest tests/ -k health -x -q` | All tests pass |

## Completion criteria

- [ ] No inline `__import__("httpx")` calls remain in the file (REQ-001)
- [ ] Code passes type checking (mypy) without errors (REQ-002)
- [ ] No regressions in health check functionality (REQ-003)
- [ ] Existing exception handling logic preserved (REQ-004)

## Out of scope

- Refactoring health check logic
- Adding new features to the health checker

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm evidence | Completed | — | 20260914-120100 | |
| 2 | Phase 2: Replace inline imports with top-level import | Completed | — | 20260914-120100 | |
| 3 | Phase 3: Run type checking and tests | Completed | — | 20260914-120100 | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260913-172956_healthchecker_inline_import.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-212629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-102215
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py
