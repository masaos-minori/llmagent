## Goal
- Document the allowlist normalization and rejection rules next to `browser_allowed_domains` in the shipped configuration (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the comment block above `browser_allowed_domains` in `config/web_search_mcp_server.toml`.
- Out of scope: any value change (the shipped list stays empty) and the `[dedup]` table, which another Plan edits.

## Assumptions
- Overlap judgment (Plan overlap check): the dedup keyless-gate Plan adds `pending_timeout_minutes` to this file's `[dedup]` table; this document edits only the comment above `browser_allowed_domains`. Different lines; compatible.
- Verified in Step 3a: the current comment describes exact hostname matching only (`config/web_search_mcp_server.toml:12-15`), and the file is already copied by `deploy/deploy.sh`.
- Written after the loader procedure (seq 03) so the comment states implemented behavior.

## Design decisions
- Comment-only change; the loader is the authority and the comment states its rules.

## Alternatives considered
- N/A: comment-only row.

## Implementation
### Target file
`config/web_search_mcp_server.toml`

### Procedure
1. Replace the comment above `browser_allowed_domains` with a short description: entries are bare hostnames; they are lowercased, converted to IDNA ASCII, and a single trailing dot is removed; a scheme, path, query, fragment, user information, port, a blank or non-string entry, or a duplicate stops startup; an empty list disables `browser_fetch` only; search-result URLs are not automatically authorized.

### Method
- Keep the key and its empty value unchanged.

### Details
- English comment, one short paragraph.

## Compatibility considerations
- N/A: comment only.

## Security considerations
- N/A: no value changes.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py` (loads the real file at import); the documentation and configuration checkers named in `rules/tool-gates.md` "When to run which tool".

## Completion criteria
- The comment states the rules consistently with the loader; the file still loads; no value changed.

## Out of Scope
- Value changes, the `[dedup]` table, and other keys.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the comment described in Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation commands named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (normalization rule documented), `REQ-002` (rejection rules documented)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `config/web_search_mcp_server.toml`
