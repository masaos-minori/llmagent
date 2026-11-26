## Goal
- Update the shared audit document for redaction, the exactly-once rule, the removed fields, and the shared helpers (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`.
- Out of scope: the web search section of the MCP server document (the next procedure) and terminology and ownership corrections owned by the design-docs update Plan.

## Assumptions
- Overlap judgment (Plan overlap check): the MCP design docs update Plan also edits this document for terminology and ownership corrections. This document edits only the `target` column description, the removed fields, and the exactly-once and redaction rules. Different passages; compatible; the phases rebase onto each other.
- Written after the code procedures so each statement cites implemented behavior; the document currently describes `target` as the raw query for web search and does not state an exactly-once rule (`mcp_02_03...md:22-48`).

## Design decisions
- Add one short subsection and edit one table row; no restructuring.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure
1. In the `target` column description, replace the web search wording ("truncated query") with: the query hash for `search_web` and a redacted URL (scheme, host, redacted path) for `browser_fetch`; add that audit records never contain raw queries or URL query strings.
2. Add a subsection stating the exactly-once rule: every authenticated `/v1/call_tool` call, including disabled-tool, unknown-tool, validation, authorization, and envelope-validation rejections, produces one record; rejected calls do not change provider health counts.
3. Document the shared helpers in `scripts/mcp_servers/audit.py` (the emission guard, the hash helper, the URL redaction helper) and the path redaction rule, and list the removed web search fields (`query_preview`, `url_preview`).
4. State the `error_type` value `tool_disabled`.

### Method
- Use names and values from the implemented code; the code wins on any difference.

### Details
- Do not name CI/CD or MDQ adoption as done; say only that those servers may reuse the helpers.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only; use no real tokens or URLs in examples.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- The documentation checkers named in `rules/tool-gates.md` "When to run which tool", through `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The document states the redaction, exactly-once, removed-field, and helper facts consistently with the code and the documentation gates report no finding.

## Out of Scope
- Terminology and ownership corrections, the web search server document, and code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the audit document | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (audit redaction and exactly-once documentation)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
