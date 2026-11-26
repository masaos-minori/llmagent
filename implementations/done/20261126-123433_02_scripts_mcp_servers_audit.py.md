## Goal
- Add the shared audit-emission contract to `audit.py`: an exactly-once emission guard, a hash helper for query-like values, and a URL redaction helper, and remove the plaintext query-preview example from the module docstring (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: additive helpers and one docstring correction in `scripts/mcp_servers/audit.py`, plus the test companion.
- Out of scope: using the helpers in the web search server (seq 07); the CI/CD and MDQ adoption (their own issues); the existing `AuditRecord` fields and `_audit_log` signature.

## Assumptions
- Verified in Step 3a: `_build_audit_record` and `_audit_log` are used by every MCP server and several tests, so the change must be additive (`rg _audit_log tests scripts/mcp_servers`); the docstring contains `query_preview='search term'` (`audit.py:28`).
- The audit-record identifier fields (session, request) already exist; the GitHub write retry-policy work that this Plan depended on is merged.
- Plan overlap check: no other Frozen Plan edits this file.

## Design decisions
- `AuditEmission` (new) is a per-call guard: `emit()` writes once and returns whether it wrote; a second call writes nothing and logs a warning, so a `finally` block can never raise over an in-flight exception.
- The hash is the first 16 hex characters of SHA-256 over the stripped, lowercased value (the same shape the web search detail already uses as `query_hash`).

## Alternatives considered
- Raise on a second emission: rejected, raising inside `finally` would mask the original error.

## Implementation
### Target file
`scripts/mcp_servers/audit.py`

### Procedure
1. Replace the detail example `latency_ms=120 query_preview='search term'` in the module docstring with `latency_ms=120 query_len=12 host='example.com'`, and add one sentence stating that audit records must not contain raw query text or URLs (use the helpers below).
2. Add `hash_query_value` (new), taking a string and returning its 16-character hash.
3. Add `redact_url(url: str) -> str` (new) and the path rule constants it uses.
4. Add `AuditEmission` (new) with a constructor taking the server logger, session id, request id, action, and server key, an `emit()` method taking target, outcome, error type, and detail, and an `emitted` property; it calls the existing `_audit_log`.

### Method
- `redact_url` (new): split with `urllib.parse.urlsplit`; a `ValueError` or a missing scheme or host returns the fixed string `invalid-url`. Output is `scheme://host` plus the redacted path: the port, user information, query, and fragment are dropped. Path rule: keep at most 8 segments (a ninth and later segment collapses to one `...`); keep a segment only when it matches `[A-Za-z0-9._~-]{1,24}` and is not a token-shaped string (length of 16 or more made of letters and digits only, or a hexadecimal string of 16 or more); every other segment becomes `*`.
- `emit()`: build the record through `_audit_log` with the guard's identifiers; set the emitted flag before returning.

### Details
- No existing function signature changes; `AuditRecord` is unchanged.
- Write the helper tests first and confirm they fail before the helpers exist.

### Companion test files
- `tests/mcp_servers/test_audit_redaction.py` (new)
  - Procedure: cover the guard (one write for two emits, warning on the second, `emitted` state, identifiers in the record), the hash helper (deterministic, trimmed and case-insensitive, 16 hex characters, differs for different input), and the URL helper (signed URL query, token in the path, OAuth parameters, personal data in query and in user information, fragment, port, an IPv6 host, a long path, an unparseable URL, and an assertion that no fixture secret appears in the serialized output); assert the module docstring contains no plaintext query-preview example.
  - Validation: `uv run pytest tests/mcp_servers/test_audit_redaction.py tests/mcp_servers/test_server_logging_sinks.py`.

## Compatibility considerations
- Additive only; every existing caller of `_audit_log` is unaffected. The removed docstring example changes no behavior.

## Security considerations
- The helpers return no raw sensitive value by construction; the hash is not reversible from the output and the URL helper drops every component that commonly carries secrets.

## Rollback considerations
- N/A: revert the commit (the web search server procedure, seq 07, depends on the helpers).

## Validation plan
- `uv run pytest tests/mcp_servers/test_audit_redaction.py tests/mcp_servers/test_server_logging_sinks.py tests/mcp_servers/test_mdq_audit.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `wc -c scripts/mcp_servers/audit.py` below 24576; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The three helpers exist with the documented behavior; no existing audit test changes; the docstring has no plaintext query example; all validation commands pass.

## Out of Scope
- Web search server changes, CI/CD and MDQ adoption, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the helpers and the docstring change | Completed | 20261126-141323 | 20261126-141323 | Changed: scripts/mcp_servers/audit.py |
| 2 | Add the companion tests first, then confirm they pass | Completed | 20261126-141323 | 20261126-141323 | Changed: tests/mcp_servers/test_audit_redaction.py (new) |
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
- **Requirement ID**: `REQ-006` (shared audit-emission contract and redaction helpers)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/audit.py`, `tests/mcp_servers/test_audit_redaction.py`
