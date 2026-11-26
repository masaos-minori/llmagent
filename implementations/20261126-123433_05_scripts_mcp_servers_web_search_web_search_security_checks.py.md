## Goal
- Make the allowlist posture check use the shared normalizer and report a malformed entry as a failure instead of a warning (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_allowlist_check`, the removal of `_is_hostname_shape`, and the module docstring of `scripts/mcp_servers/web_search/web_search_security_checks.py`, plus the test companion.
- Out of scope: the numeric checks and the check ids (unchanged).

## Assumptions
- Implemented after the normalizer procedure (seq 01).
- Verified in Step 3a: a malformed entry yields a WARNING with `REASON_ALLOWLIST_INVALID` and the test asserts it (`web_search_security_checks.py:118-148`; `test_web_search_security_validation.py:183-186`). After seq 03, a malformed entry stops config load, so this path is reachable only for a directly constructed `WebSearchConfig` and stays as defense in depth.
- Plan overlap check: no other Frozen Plan edits this file.

## Design decisions
- The posture check calls `validate_allowlist` and maps a `HostNormalizationError` to FAILED with `REASON_ALLOWLIST_INVALID`, so the posture and the loader agree by construction.

## Alternatives considered
- N/A: lightweight row.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_security_checks.py`

### Procedure
1. Import `validate_allowlist` and `HostNormalizationError` from `mcp_servers.web_search.host_normalization`.
2. In `_allowlist_check`, keep the NOT_APPLICABLE result for an empty list; otherwise call `validate_allowlist` and return FAILED with the reason code `REASON_ALLOWLIST_INVALID` on error (the message states the count of entries and the first failing index and reason, not any value) or OK with the entry count.
3. Delete `_is_hostname_shape` and update the module and function docstrings that describe the WARNING outcome.

### Method
- The check id `server.browser_allowlist` and the five-element order are unchanged.

### Details
- Messages name only the setting, counts, index, and reason code.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_security_validation.py`
  - Procedure: reverse `test_a_malformed_entry_is_a_warning_not_a_failure` to expect a failed status with `allowlist_invalid`; keep the empty-list not-applicable and valid-list cases; add a check that the message contains neither the entry nor the host value.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_security_validation.py tests/mcp_servers/web_search/test_web_search_health_posture.py`.

## Compatibility considerations
- A directly constructed config with a bad entry now fails the posture (it warned before); real startup is stopped earlier by the loader.

## Security considerations
- Fail-closed posture; no allowlist value appears in the message.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_security_validation.py tests/mcp_servers/web_search/test_web_search_health_posture.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- A malformed entry reports failed with `allowlist_invalid`; the empty and valid cases are unchanged; no helper duplicates the normalization; all validation commands pass.

## Out of Scope
- Loader validation, runtime matching, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Update the companion test, then confirm it passes | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (shared normalization), `REQ-002` (malformed entries fail)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/web_search_security_checks.py`, `tests/mcp_servers/web_search/test_web_search_security_validation.py`
