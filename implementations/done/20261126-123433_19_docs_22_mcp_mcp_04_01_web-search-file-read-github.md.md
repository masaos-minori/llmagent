## Goal
- Document allowlist normalization and matching, that search-result URLs are not automatically authorized for `browser_fetch`, audit redaction, health wording, and Bearer authentication in `/v1/tools` examples in the web search section (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the web search section of `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`.
- Out of scope: the fetch-boundary bullets (a separate, already archived Plan whose documentation procedure is pending), and the GitHub and file-read sections (other Plans).

## Assumptions
- Overlap judgment (Plan overlap check): this file is also targeted by the file MCP hardening Plan and the MCP design docs update Plan, and by the fetch-boundary Plan's documentation procedure. This document edits only the allowlist, authorization-scope, audit, health-wording, and authentication passages of the web search section; the others edit other sections or the fetch-boundary bullets. Compatible; the phases rebase onto each other.
- Written after the code procedures so each statement cites implemented behavior; the section currently says `browser_allowed_domains` is an exact host match and describes health generally (`mcp_04_01...md:44-55`).

## Design decisions
- Add bullets and examples to the existing web search section; do not restructure.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

### Procedure
1. Describe the allowlist rules: entries are normalized (lowercase, IDNA ASCII, one trailing dot removed), matching is exact on the normalized host, and an invalid or duplicate entry stops startup; an empty list disables `browser_fetch` only.
2. State that a URL returned by `search_web` is not automatically authorized for `browser_fetch`; only an allowlisted host is fetched.
3. Describe the audit behavior for these tools: the query hash as target, a redacted URL for fetches, no raw query or URL query string, and exactly one record per call including rejections; reference the shared audit document for the field list.
4. Reword the health text so it does not imply constant health: `/health` reports the current provider state, and the error metadata (`last_error_type`, last failure time) is historical information that does not by itself mean the tool is currently failing.
5. In `/v1/tools` and `/health` examples that show requests, include the `Authorization: Bearer <token>` header.

### Method
- Use names and values from the implemented code; the code wins on any difference.

### Details
- Keep the fetch-boundary bullets exactly as the other Plan's documentation procedure leaves them.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only; examples use a placeholder token, never a real one.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- The documentation checkers named in `rules/tool-gates.md` "When to run which tool", through `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The section states the five items consistently with the code and the documentation gates report no finding.

## Out of Scope
- The fetch-boundary bullets, the GitHub and file-read sections, and code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the web search section | Completed | 20261126-141323 | 20261126-141323 | Changed: docs/22_mcp/mcp_04_01_web-search-file-read-github.md |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261126-141323 | 20261126-141323 | documentation checkers passed |

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
- **Requirement ID**: `REQ-007` (allowlist, authorization scope, audit, health wording, authentication documentation)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
