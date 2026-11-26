## Goal
- Make both request models strict, bound `browser_fetch` arguments to the server contract, and validate the allowlist at configuration load through the shared normalizer (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `SearchRequest`, `BrowserFetchRequest`, and `WebSearchConfig.from_dict` in `scripts/mcp_servers/web_search/web_search_models.py`.
- Out of scope: the exception classes and response fields of the fetch-boundary Plan (a separate, already archived Plan whose procedures are pending), and the tool schema generation (seq 04).

## Assumptions
- Overlap judgment (Plan overlap check): the fetch-boundary Plan's models procedure adds exception classes and two defaulted fields on `BrowserFetchResponse`; this document edits the request models and the configuration parse. Different symbols; compatible; the phases rebase onto each other.
- Verified in Step 3a: both request models are plain `BaseModel` (`web_search_models.py:254-321`); `browser_allowed_domains` is read with `list(get_typed(d, ..., list, ...))` and its entries are never type-checked (`:180-182`); `max_response_kb` is bounded at 65536 while `HARD_BROWSER_MAX_RESPONSE_KB = 4096` (`:63,306-312`); `StrictRequestModel` exists in `scripts/mcp_servers/request_contract.py`.
- Implemented after the normalizer procedure (seq 01).

## Design decisions
- `max_response_kb` is bounded by `HARD_BROWSER_MAX_RESPONSE_KB`; clamping to the configured maximum stays in the service path and is stated in the field description (Plan decision D-4).
- A bad allowlist entry fails at import time through the existing `_cfg = WebSearchConfig.load()`, as other config errors do (Plan decision D-2).

## Alternatives considered
- Expose the configured maximum in the model: rejected, it would turn clamping into rejection and tie the model to a runtime value.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_models.py`

### Procedure
1. Import `StrictRequestModel` from `mcp_servers.request_contract` and `validate_allowlist` from `mcp_servers.web_search.host_normalization`.
2. Change `SearchRequest` and `BrowserFetchRequest` to derive from `StrictRequestModel`.
3. In `BrowserFetchRequest`, give `url` `min_length=1` and a description naming the allowlist, and set `max_response_kb` to `ge=1, le=HARD_BROWSER_MAX_RESPONSE_KB` with a description stating that the server clamps it to the configured maximum.
4. In `WebSearchConfig.from_dict`, replace the plain `list(...)` of `browser_allowed_domains` with `validate_allowlist(get_typed(...))` so the stored list is normalized and every bad entry raises `ValueError`.
5. Update the class docstrings (strictness, bounds).

### Method
- The `search_web` model keeps its field constraints; only the base class changes, so unknown arguments are rejected.
- `validate_allowlist` raises with the setting name and entry index, never the value, so the startup error leaks no configuration content.

### Details
- `web_search_tools.py` (seq 04) generates its schemas from these two models, so field descriptions are written here.

## Compatibility considerations
- Unknown arguments are rejected instead of silently dropped; `max_response_kb` values between 4097 and 65536, previously clamped, are now rejected; an operator allowlist containing an invalid entry now stops startup. The shipped allowlist is empty and unaffected.

## Security considerations
- Strict models close the silent-drop path; startup errors do not echo allowlist values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py tests/mcp_servers/web_search/test_web_search_tool_schema.py` (updated by the later procedures) and the existing web search suite `uv run pytest tests/mcp_servers/web_search`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `lint-imports`; `wc -c` below 24576; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Both models reject unknown arguments; `url` empty and `max_response_kb` above the ceiling are rejected; an invalid or duplicate allowlist entry raises at config parse and a valid one is stored normalized; an empty list loads; the models test procedure (seq 11) passes; all validation commands pass.

## Out of Scope
- Exception classes, response fields, schema generation, the posture check, runtime matching, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the models test procedure (seq 11) against the change | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (load-time allowlist rejection), `REQ-003` (strict models and bounds)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/web_search_models.py`
