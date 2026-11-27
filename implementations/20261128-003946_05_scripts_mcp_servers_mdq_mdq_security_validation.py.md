# Implementation Procedure — scripts/mcp_servers/mdq/mdq_security_validation.py

## Goal

Make an empty FTS index over existing documents a not-ready posture finding instead of a warning
(REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005 (an unexpectedly empty FTS index is not ready). Acceptance criterion: AC-4.

## Assumptions
- Full form: this row changes the posture gate that blocks the HTTP bind, so the gate's outcome
  changes for a store that currently passes with a warning.
- Only `FAILED` blocks Ready (`scripts/shared/security/result_dto.py` line 98), so the status change
  is what makes the condition not ready; no new status or reason code is added.
- `REASON_DEPENDENCY_UNREACHABLE` is already in the closed vocabulary, so the reason code stays.
- The assertion that pins the current warning lives in `tests/mcp_servers/mdq/test_mdq_security_validation.py`
  (Plan row 20), which is a Plan row with its own document, so it is not a companion here.

## Design decisions
- The empty-index case is treated as a failed check, not as a policy violation with a warning,
  because the Plan states the condition is not ready.
- `NOT_APPLICABLE` is kept when index stats were not collected, so a store with no rows is not
  reported as failed.

## Alternatives considered
- Keep the warning and gate `ready` separately: rejected, because `ready` is derived from the
  dependency map and the posture validation alone (`scripts/mcp_servers/health_response.py` line 65),
  so a warning cannot make the service not ready.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_security_validation.py`

### Procedure
- In `_index_check` (lines 218-234), return `SecurityCheckStatus.FAILED` for the case where the FTS
  row count is zero while documents or chunks exist, keeping the same check id and reason code.
- Leave the `NOT_APPLICABLE` branch (line 219) and the healthy branch (lines 231-234) unchanged.

### Method
- The message text is kept so operators still see which condition failed; the status is the only
  change.

### Details
- The posture gate in `scripts/mcp_servers/mdq/mdq_server.py` reads only `_security_posture.validated`,
  so the bind gate now refuses a bind for an empty index over rows.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_health_posture.py`
  - Procedure: add the not-validated bind case for an empty FTS index over rows; the existing
    validated-posture assertion (line 34) stays, and the warning assertion itself is not in this file.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py` — the bind gate
    refuses the posture for an empty index over rows.

## Compatibility considerations
- `tests/conftest.py` sets a non-empty auth token and the shipped posture carries every check as OK,
  so the module-import posture stays validated for the existing tests.
- The health body shape is unchanged; only the posture status for one condition changes.

## Security considerations
- N/A: no path, permission, or secret handling changes; the change makes a data-consistency finding
  gate the bind.

## Rollback considerations
- Reverting restores the warning status; a service that was refused a bind becomes bindable again, so
  rollback is a code revert only.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py tests/mcp_servers/mdq/test_mdq_security_validation.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- An empty FTS index with rows present is not ready and the bind gate refuses it (AC-4); a store with
  no rows is still not applicable.

## Out of Scope
- The readiness vocabulary mapping (row 4); the definition comparison (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_health_posture.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 15) |

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
- **Requirement ID**: REQ-005 (an unexpectedly empty FTS index is not ready)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/mcp_servers/mdq/mdq_security_validation.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`
