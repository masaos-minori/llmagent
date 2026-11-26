## Goal
- Remove the `server.supported_extensions` posture check from the write security validator (REQ-006, `supported_extensions` removal).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the check block at lines 93-96 and the docstring paragraph that explains why it is always `not_applicable`; the pinned test updates in the companion.
- Out of scope: the config field removal (seq 03), the health-view removal (seq 12), the shared inventory removal (seq 13).

## Assumptions
- Verified in Step 3a: the check at lines 93-96 reports `NOT_APPLICABLE` with reason "supported_extensions is parsed but not enforced by the write service"; after seq 03 the setting no longer exists, so the check has nothing to report.
- The Plan records no new posture checks for the traversal limits, so the check set shrinks by exactly this one id.

## Design decisions
- Delete the check entirely rather than reclassifying it: the control it named is removed by owner decision (20261126), so a `not_applicable` placeholder would assert a contract that no longer exists.

## Alternatives considered
- Reporting the check as failed until enforcement exists — rejected by the owner decision (remove, not enforce).

## Implementation
### Target file
`scripts/mcp_servers/file/write_security_validation.py`

### Procedure
1. Remove the `SecurityCheckResult(check_id="server.supported_extensions", ...)` block (lines 93-96).
2. Remove the docstring paragraph (lines 93-96 region, the "always not_applicable" explanation) that describes the removed check.

### Method
- Remaining checks and the shared-base delegation are unchanged.

### Companion test files
- `tests/mcp_servers/file/test_file_security_validation.py`
  - Procedure: remove the pins at lines 47, 333-335, 337-341 and the helper `supported_extensions` parameter at lines 258, 264, 394.
  - Validation: assert the write check set no longer contains the id.

## Compatibility considerations
- Check-set comparison consumers see one fewer id; the shared inventory (seq 13) must drop the same id in the same change set to keep the posture contract consistent.

## Security considerations
- N/A: the change removes a posture entry for a control that never existed; no enforcement is lost.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Companion tests: remove the pins listed above; assert the write check set no longer contains the id.
- `uv run pytest tests/mcp_servers/file/test_file_security_validation.py -v`; `uv run pytest tests/shared/test_security_posture_contract.py -v` (seq 13 companion); full `rules/toolchain.md` sequence.

## Completion criteria
- No `server.supported_extensions` check is produced by the write validator; pinned tests pass (AC-5).

## Out of Scope
- Config field (seq 03), health view (seq 12), shared inventory (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (`supported_extensions` removal from code, posture, tests, documentation)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/write_security_validation.py`, `tests/mcp_servers/file/test_file_security_validation.py`
