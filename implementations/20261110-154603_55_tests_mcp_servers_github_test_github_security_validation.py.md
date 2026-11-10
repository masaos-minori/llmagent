## Goal
Align `tests/mcp_servers/github/test_github_security_validation.py` with the removed skip-when-empty posture branch and the registered `path_denylist` exception (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Row 16 (`github_service_security.py`) removes the posture text for an empty `protected_branches` (lines 318-345 of the source); the status that the posture function reports for the empty case is decided in row 16's document, and `TestInapplicableChecks.test_empty_protected_branches` (line 104) must follow it.
- `path_denylist = []` stays permitted (ADR-004 exception), so `test_empty_path_denylist` (line 109) and the `NOT_APPLICABLE` expectation stay; `_safe_cfg` (line 46) keeps `protected_branches=["main"]` and a non-empty `path_denylist`.
- The shipped `config/github_mcp_server.toml` (`protected_branches` non-empty, `path_denylist = []`) must still load; that is covered by the load-level tests in row 54/52.

## Design decisions
- Rewrite `test_empty_protected_branches` to match row 16's decision; do not keep an expectation (`NOT_APPLICABLE`) that the code no longer produces.
- Do not touch the `REQUIRED_CHECK_IDS` expectations (line 31): the check id `server.protected_branches` stays.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/mcp_servers/github/test_github_security_validation.py`

### Procedure
- `TestInapplicableChecks.test_empty_protected_branches` (lines 104-107): replace with the status row 16 specifies for an empty list (a posture failure, because load rejects it, or removal of the test if row 16 drops the empty case); name the test after that outcome.
- Update the class docstring (line 101): `A rule that is switched off` now covers `path_denylist`, `max_file_size_kb` and `audit_log_path`, not `protected_branches`.
- `test_configured_rules_are_ok` (lines 124-130) is unchanged.

### Method
- Read row 16's document (`implementations/20261110-154603_16_*`) before editing; the two must agree on the empty-case status.
- Keep `_results` and `_safe_cfg` helpers as they are.

### Details
- If row 16 leaves the empty case reporting `NOT_APPLICABLE`, this test needs no change; record that in the step note.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_security_validation.py -v`

## Completion criteria
- No test asserts a behavior the posture code no longer produces.
- The `path_denylist` empty case is still covered.
- The file passes.

## Out of Scope
- Changing the posture function (row 16) or `config/github_mcp_server.toml` (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/mcp_servers/github/test_github_security_validation.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/github/test_github_security_validation.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (per the Plan row); aligns with `REQ-004` (empty `protected_branches`, `path_denylist` exception)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/mcp_servers/github/test_github_security_validation.py`
