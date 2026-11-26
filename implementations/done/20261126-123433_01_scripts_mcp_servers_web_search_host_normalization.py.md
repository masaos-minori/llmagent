## Goal
- Create the single host-normalization and allowlist-entry validation function that configuration loading, the posture check, and runtime authorization all use (REQ-001, one normalization; REQ-002, strict entry rejection).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new leaf module `scripts/mcp_servers/web_search/host_normalization.py` and its test companion.
- Out of scope: wiring it into the models, the posture check, and the provider (seq 03, 05, 06).

## Assumptions
- Plan Assumptions carried over: IDNA conversion uses the standard-library `idna` codec, so no dependency is added.
- Verified in Step 3a: the runtime lowercases the URL host and compares it verbatim to the raw configured set (`search_provider.py:100-123`), and the posture mirror rejects only uppercase and ` \t:/` characters (`web_search_security_checks.py:48-60`), so no IDNA, trailing-dot, or userinfo handling exists today.
- Plan overlap check: this new file overlaps no other Frozen Plan. The web search fetch-boundary Plan is already archived with its procedures pending; its provider procedure keeps `_check_domain` unchanged, which this Plan changes in seq 06 (compatible, different edits).

## Design decisions
- One module with no imports from the rest of the web search package, so the models, posture, and provider modules can all import it without a cycle.
- A normalization failure raises `HostNormalizationError` (new) (a `ValueError`) carrying a `reason` code; messages never echo the offending value.

## Alternatives considered
- Put the function in `web_search_models.py`: rejected, the provider and posture modules would import a large config module for one function (Plan decision D-1).

## Implementation
### Target file
`scripts/mcp_servers/web_search/host_normalization.py` (new)

### Procedure
1. Create the module with the repository module docstring format and a `Dependency direction:` line (standard library only).
2. Add `HostNormalizationError(ValueError)` (new) with a `reason` attribute.
3. Add `normalize_host(value: object) -> str` (new) and `validate_allowlist(entries: object) -> list[str]` (new).

### Method
- `normalize_host` (new): reject a non-string (reason not_string) and a blank string; reject any of whitespace, a scheme separator, `/`, `?`, `#`, `@`, `:`, `\` and `%` (reasons scheme, path, query, fragment, userinfo, port, malformed); lowercase; remove exactly one trailing dot; convert to ASCII with the standard-library `idna` codec (a `UnicodeError` becomes reason malformed); then check each label is 1 to 63 characters of lowercase letters, digits, and hyphen, not starting or ending with a hyphen, and the host is at most 253 characters. Return the ASCII form.
- `validate_allowlist` (new): require a list, normalize each entry with `normalize_host` (new), and raise `HostNormalizationError` (new) for the first failure with a message naming the setting and index (`browser_allowed_domains[3]`) and the reason, never the value; reject a duplicate after normalization (reason duplicate, naming both indexes); return the normalized list in the original order. An empty list is valid.

### Details
- The same `normalize_host` (new) is used for the URL host at runtime (seq 06), so a configured entry and a request host are compared in one form.
- Write the tests first and confirm they fail before the module exists.

### Companion test files
- `tests/mcp_servers/web_search/test_host_normalization.py` (new)
  - Procedure: cover uppercase, IDNA (a U-label and its A-label), a trailing dot, scheme, path, query, fragment, user information, port, blank, non-string, malformed labels, over-long labels, duplicates after normalization, an empty list, and the error message naming the index but not the value.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_host_normalization.py`.

## Compatibility considerations
- New module with no caller until seq 03, 05, and 06.

## Security considerations
- Fail-closed on every malformed input; messages carry no allowlist values; the module performs no I/O or DNS lookup.

## Rollback considerations
- N/A: revert the commit; nothing imports the module until seq 03.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_host_normalization.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `uv run lint-imports`; `uv run bandit -r scripts/mcp_servers/web_search/host_normalization.py -c pyproject.toml`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Every case of the companion test passes; the function names and error attributes match this document; the module imports only the standard library; all validation commands pass.

## Out of Scope
- Wiring into configuration, posture, and runtime authorization, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the module described in Implementation > Procedure/Method/Details | Completed | 20261126-141323 | 20261126-141323 | Changed: scripts/mcp_servers/web_search/host_normalization.py (new) |
| 2 | Add the companion tests first, then confirm they pass | Completed | 20261126-141323 | 20261126-141323 | Changed: tests/mcp_servers/web_search/test_host_normalization.py (new); 49 tests, failed before the module existed |
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
- **Requirement ID**: `REQ-001` (one normalization function), `REQ-002` (strict entry rejection)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/host_normalization.py`, `tests/mcp_servers/web_search/test_host_normalization.py`
