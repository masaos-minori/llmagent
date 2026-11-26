## Goal
- Make `_check_domain` compare the normalized URL host with the normalized allowlist, so runtime authorization uses the same normalization as configuration and posture (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_check_domain` in `scripts/mcp_servers/web_search/search_provider.py` and the test companion.
- Out of scope: the fetch path (`fetch_browser`), which a separate, already archived Plan rewrites in its own pending procedures.

## Assumptions
- Overlap judgment (Plan overlap check): the fetch-boundary Plan's provider procedure rewrites `fetch_browser` and keeps `_check_domain` unchanged, using it as its host policy. This document changes only `_check_domain`, so the edits are on different functions and compatible; `_check_domain` stays the allowlist policy the fetch helper calls and keeps its signature and return value.
- Implemented after the normalizer procedure (seq 01).
- Verified in Step 3a: `_check_domain` lowercases the URL hostname and compares it verbatim with the given set (`search_provider.py:90-123`); the existing tests call it with raw sets such as `{"example.com"}` and expect the hostname back (`test_web_search_provider.py:155-191`).

## Design decisions
- Normalize both sides inside `_check_domain` (the set members through a tolerant helper that skips an invalid member), so existing callers that pass raw sets keep working and configured entries stay normalized by the loader.
- Complexity of `_check_domain` is already C (12); move the allowlist match into a small helper so the function does not grow.

## Alternatives considered
- Require callers to pass pre-normalized sets: rejected, the existing tests and any direct caller pass raw sets.

## Implementation
### Target file
`scripts/mcp_servers/web_search/search_provider.py`

### Procedure
1. Import `normalize_host` and `HostNormalizationError` from `mcp_servers.web_search.host_normalization`.
2. In `_check_domain`, normalize the URL hostname with `normalize_host`; a `HostNormalizationError` raises `BrowserValidationError` ("URL has an invalid hostname").
3. Keep the IP-literal rejection, applied to the normalized host, before the allowlist test.
4. Add a small private helper `_host_in_allowlist(hostname, allowed_domains)` (new) that normalizes each set member with `normalize_host`, skips a member that fails normalization, and returns whether `hostname` matches; use it for the allowlist test and return the normalized hostname.
5. Update the docstring to say matching is on the normalized form.

### Method
- The returned hostname is the normalized ASCII form, which equals the old value for plain lowercase hosts.

### Details
- Do not touch `fetch_browser` or the response handling.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_provider.py`
  - Procedure: add cases to the `_check_domain` class for an uppercase URL host, an IDNA U-label URL against an A-label entry and the reverse, a trailing-dot URL host, a trailing-dot or uppercase entry in the raw set, an invalid URL host, and an invalid set member that never matches; keep every existing `_check_domain` test.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_provider.py -k check_domain`.

## Compatibility considerations
- Hosts that previously failed to match because of case, IDNA, or a trailing dot now match their normalized entry; non-matching hosts still fail.

## Security considerations
- Matching stays exact on the normalized host; the IP-literal rejection is unchanged and still runs unconditionally.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_provider.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `uv run radon cc scripts/mcp_servers/web_search/search_provider.py -s -n C` shows `_check_domain` not worse than before; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Uppercase, IDNA, and trailing-dot forms match; invalid hosts raise the validation error; existing `_check_domain` tests pass unchanged; all validation commands pass.

## Out of Scope
- `fetch_browser`, network authorization, loader validation, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-141323 | 20261126-141323 | Changed: scripts/mcp_servers/web_search/search_provider.py (_check_domain split to keep its complexity below the earlier C(12)) |
| 2 | Add the companion test cases, then confirm they pass | Completed | 20261126-141323 | 20261126-141323 | Changed: tests/mcp_servers/web_search/test_web_search_provider.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-141323 | 20261126-141323 | ruff format/check, mypy (CI invocation), lint-imports, bandit, module size, docstring, reference table, validation gates passed; full suite (parallel, coverage): 26 failed and 88 errors in tests/agent/* and tests/docs/test_command_docs_sync.py from a pre-existing NameError in scripts/agent/commands/cmd_mcp.py, unrelated to this change; diff-cover 100% on the changed tracked files; targeted tests pass |

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
- **Requirement ID**: `REQ-001` (runtime authorization uses the shared normalization)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/search_provider.py`, `tests/mcp_servers/web_search/test_web_search_provider.py`
