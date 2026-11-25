## Goal

Add the typed error family — `ShutdownSuppressedError(RuntimeError)` base with `EnsureSuppressedError` (new) and `RestartSuppressedError` (new), plus `RestartBlockedError` (new) (REQ-005, REQ-008).

## Scope
**Release unit**: R3-ownership

## Assumptions
- `StartSuppressedError` stays in `scripts/agent/lifecycle_router.py:45` for caller compatibility (`startup_mcp_starter.py:23`); this row does not move it (Plan Assumptions).

## Design decisions
- The family lives in this module because it already owns the lifecycle error vocabulary (`HttpStartupError` `:28`, `TerminationOutcome` `:46`).
- All are `RuntimeError` subclasses so existing callers handle them unchanged.

## Alternatives considered
- Moving `StartSuppressedError` here — rejected: it would touch a non-lifecycle consumer, against the Issue's keep-in-lifecycle-modules instruction.

## Implementation
### Target file
`scripts/agent/http_lifecycle_errors.py`

### Procedure
Define the base and three subclasses after the existing error classes (`:19-61`).

### Method
Plain exception classes with one-line docstrings stating non-retryable semantics (AC-4).

### Details
- `RestartBlockedError` is raised by `restart()` on an unconfirmed old exit (row 03); the suppression classes are raised by the router (row 06).

## Compatibility considerations
- Additive classes; no existing class changes; `tool_transport_invoker.py:282` and `startup_mcp_starter.py:188` already handle the `RuntimeError` family.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py` (typed-error tests, row 11).

## Completion criteria
- The four classes exist, subclass `RuntimeError`, and the suppression/refusal tests catch them by type.

## Out of Scope
- The raise sites in the router and manager (rows 06, 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (restart refusal vocabulary), REQ-008 (typed suppression errors)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/http_lifecycle_errors.py`
