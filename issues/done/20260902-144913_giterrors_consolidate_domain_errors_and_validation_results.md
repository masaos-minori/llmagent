# Consolidate Git MCP domain errors and structured validation results

## Priority
Medium

## Summary
Use one canonical exception hierarchy and one structured validation result across the Git MCP
modules, migrating verified callers before removing compatibility code.

## Background
No existing issue was found covering `GitServiceError` duplication or `RepoValidationResult`.
Investigation confirmed `GitServiceError` is currently defined twice —
`scripts/mcp_servers/git/errors.py` and `scripts/mcp_servers/git/git_models.py` — and
`RepoValidationResult` is still referenced in `git_service.py`, `repository_state.py`, and
tests.

## Problem
Duplicate domain exception definitions and string-only compatibility results can cause handlers
to miss errors that appear semantically identical but are different Python classes. Deprecated
validation shims also hide whether callers use the current security model or an older path that
returns only an error message.

## Reason for Change
An exception-identity mismatch (`isinstance` against the wrong `GitServiceError` class) can
silently fail to trigger the registered error handler, turning a caught-and-handled failure
into an unhandled one.

## Implementation Intent
Keep the canonical `GitServiceError` definition in `errors.py`; remove or replace the duplicate
declaration. Find all `RepoValidationResult` callers and classify them as active, test-only, or
obsolete; replace active string-only validation results with a structured result containing an
error code, message, stage, and validated target where applicable. Update imports, FastAPI
exception handlers, service handlers, and tests. Remove `RepoValidationResult` only after all
verified callers have migrated.

## Target Files or Areas
- `scripts/mcp_servers/git/errors.py`
- `scripts/mcp_servers/git/git_models.py`
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/git_server.py`
- `tests/test_git_server.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Keep the canonical `GitServiceError` definition in `errors.py`.
- Remove or replace the duplicate `GitServiceError` declaration in `git_models.py`.
- Find all `RepoValidationResult` callers and classify them as active, test-only, or obsolete.
- Replace active string-only validation results with a structured result containing an error code, message, stage, and validated target where applicable.
- Update imports, FastAPI exception handlers, service handlers, and tests.
- Remove `RepoValidationResult` only after all verified callers have migrated.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- Only one canonical `GitServiceError` class is defined.
- All Git MCP modules and handlers import the canonical exception type.
- Domain errors are converted to the intended API response consistently.
- No active production caller references `RepoValidationResult`.
- Validation failures retain structured error information after migration.
- Tests prove that exception identity cannot bypass the registered server handler.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md`'s error-handling description once implementation and tests
establish the current behavior, if it references either type.

## Out of Scope
- Protected-branch/ref authorization content itself (`gitauth`).
- The write-protection pipeline's stage ordering (`gitpipeline`).
- Placeholder-method removal in `repository_state.py` beyond error/validation types (`gitcleanup`).

## Dependencies
N/A: none — independently actionable.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, re-confirm both `GitServiceError` definitions and all `RepoValidationResult`
call sites (`grep -rn "class GitServiceError\|RepoValidationResult" scripts/ tests/`), since
this issue's evidence may go stale. Migrate callers before deleting `RepoValidationResult`; do
not delete it speculatively.
