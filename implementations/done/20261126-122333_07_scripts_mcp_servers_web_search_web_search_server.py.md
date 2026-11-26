## Goal
- Report the same error type in the audit record as the service records in metrics for the new `browser_fetch` outcomes (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the audit error-type classification in `scripts/mcp_servers/web_search/web_search_server.py` and its test companion.
- Out of scope: audit redaction, gate ordering, and exactly-once emission (the sibling configuration and audit Plan).

## Assumptions
- Overlap judgment (Plan overlap check): the configuration and audit Plan also modifies this file, in `_build_audit_target_and_detail` and the `call_tool` gate and emission structure. This document changes only `_classify_upstream_error` and the `except` ladder entry for the new errors; the two edits are on different functions and compatible, and the phases rebase onto each other.
- Implemented after the models procedure (seq 03) and the service procedure (seq 05), whose type vocabulary it mirrors.
- Verified in Step 3a: the server keeps its own `_classify_upstream_error` (a deliberate duplicate to avoid an import cycle) and `call_tool` re-raises `WebSearchUpstreamError` after setting `error_type` from it; the 502 handler returns `{"error": str(exc)}` (`web_search_server.py:111-119,191-205,294-299`).

## Design decisions
- Extend the existing server-side classifier instead of importing the service's: same duplicate-by-design pattern, with a parity test that fails if the two vocabularies diverge.

## Alternatives considered
- Move the mapping into the models module and import it from both: rejected for this Plan to keep the models change additive (a follow-up may unify them).

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. Import the two new errors from `web_search_models`.
2. In `_classify_upstream_error`, before the existing fallbacks, return `http_<category>` for the status error, unsupported_content for the unsupported-content error, and keep the existing results for the other classes.
3. Keep the `except WebSearchUpstreamError` branch of `call_tool` as the single place that sets `error_type` for these errors; add no new branch.
4. Update the classifier docstring.

### Method
- The status error's `category` attribute selects the suffix (`redirect`, client_error, rate_limited, `server_error`, `other`).

### Details
- The HTTP status of the response stays 502 through the existing handler.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_server.py`
  - Procedure: for each category and for unsupported content, call the classifier and assert the type; add a parity test that every error type the service classifier (seq 05) returns for these errors equals the server classifier's; assert an audit record for a browser fetch that raises a status error carries the `http_*` type.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py tests/mcp_servers/web_search/test_web_search_audit.py`.

## Compatibility considerations
- Audit `error_type` gains new values for fetch failures that previously surfaced as `unexpected_error` or a passthrough result; consumers of the audit log that enumerate values should tolerate additions (documented in the audit document update of the sibling Plan).

## Security considerations
- N/A: classification only; the audit record carries the type string and no upstream content.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py tests/mcp_servers/web_search/test_web_search_audit.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `wc -c` of the server file below 24576; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Each category and unsupported content yields the documented audit type; the parity test passes; existing server and audit tests pass; all validation commands pass.

## Out of Scope
- Redaction, gate ordering, exactly-once emission, the service, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-133738 | 20261126-133738 | Changed: scripts/mcp_servers/web_search/web_search_server.py |
| 2 | Add the companion test cases, then confirm they pass | Completed | 20261126-133738 | 20261126-133738 | Changed: tests/mcp_servers/web_search/test_web_search_server.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-133738 | 20261126-133738 | ruff format/check, mypy (CI invocation), lint-imports, bandit, module size, validation gates passed; full suite: 26 failed and 88 errors from a pre-existing NameError in scripts/agent/commands/cmd_mcp.py, unrelated to this change; targeted tests pass |

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
- **Requirement ID**: `REQ-007` (audit error type aligned with the result classification)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`, `tests/mcp_servers/web_search/test_web_search_server.py`
