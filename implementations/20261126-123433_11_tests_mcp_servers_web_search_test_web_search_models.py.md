## Goal
- Pin the strict request models and the load-time allowlist rejection in the models test file (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tests/mcp_servers/web_search/test_web_search_models.py`.
- Out of scope: the normalizer's own unit tests (its companion) and the schema parity tests (the tools companion).

## Assumptions
- This file is named by two rows of the Plan (the models row and the configuration row), so it keeps its own document instead of being a companion.
- Implemented after the models procedure (seq 03); the rejection tests are written first and must fail on the old code.
- Verified in Step 3a: the file exists and tests the config bounds and models (`tests/mcp_servers/web_search/test_web_search_models.py`); the loader currently accepts any list for `browser_allowed_domains`.

## Design decisions
- Test through `WebSearchConfig.from_dict` with inline dicts so no real configuration file is needed; one extra test loads the real shipped file.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_models.py`

### Procedure
1. Add parametrized rejection cases for `from_dict`: an entry with a scheme, a path, a query, a fragment, user information, a port, a blank string, a non-string (integer and `None`), a malformed label, and a duplicate after normalization; assert a `ValueError` whose message names `browser_allowed_domains` and the index and does not contain the entry value.
2. Add acceptance cases: an empty list; an uppercase, an IDNA U-label, and a trailing-dot entry, each stored normalized.
3. Add model cases: an unknown argument is rejected by `SearchRequest` and `BrowserFetchRequest`; an empty `url` is rejected; `max_response_kb` of 0 and of one above `HARD_BROWSER_MAX_RESPONSE_KB` are rejected and the ceiling itself is accepted.
4. Add one test that `WebSearchConfig.load()` succeeds on the shipped file with an empty allowlist.

### Method
- Keep every existing bound test unchanged.

### Details
- Do not print or assert on real allowlist values from the shipped file beyond emptiness.

## Compatibility considerations
- Test-only.

## Security considerations
- Tests assert that error messages do not echo configured values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Every rejection and acceptance case passes; the new rejection tests fail on the pre-change code; existing tests are untouched; all validation commands pass.

## Out of Scope
- Normalizer unit tests, schema parity, posture, runtime matching, and audit tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests described in Implementation > Procedure | Pending | — | — | |
| 2 | Confirm the rejection tests fail before seq 03 and pass after | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (load-time rejection), `REQ-003` (strict models and bounds)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `tests/mcp_servers/web_search/test_web_search_models.py`
