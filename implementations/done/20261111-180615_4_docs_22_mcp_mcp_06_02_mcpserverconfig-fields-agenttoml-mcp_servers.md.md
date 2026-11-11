## Goal
Remove the `failure_policy` bullet from the MCP server configuration field reference so the document no longer describes a field that `REQ-001` deletes (Plan Phase 1, frozen-table row 4).

## Scope
**Release unit**: N/A: not part of a release unit

- **Target file**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` (frozen-table row 4).

## Assumptions
- The `failure_policy` bullet (line 53) is the only `docs/` mention of the field (verified 2026-11-11: `rg -n "failure_policy" docs/` hits this line only).

## Design decisions
- Delete the whole bullet rather than reword it: a documentation entry for a field that no longer exists is stale content, and `rules/coding.md` Deprecation policy leaves no alias to describe.
- No other section of the document changes: the surrounding bullets (`required`, `tool_names`, `role`, `key`) describe surviving fields.

## Alternatives considered
- Replace the bullet with a historical note ("previously reserved") — rejected: `docs/` documents the current schema only, and the Plan Issue asks for removal, not annotation.

## Implementation
### Target file
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure
1. Delete the bullet at line 53.

### Method
Single-bullet deletion; leave the surrounding blank line structure such that the field list ends after the `required` bullet.

### Details
Before (line 53):

```markdown
- `failure_policy`: reserved for runtime call-failure behavior. Only `fail-fast` exists and nothing branches on it.
```

After: line removed; it is followed by a blank line and then "**About `tool_names`:**", and that blank line stays (deleting it would merge the bullet list with the following paragraph).

## Compatibility considerations
- The document edit must land in the same cycle as the code removal (documents 1 and 2); a document describing a deleted field is a `check_docs_consistency.py` finding class.
- No other document quotes `failure_policy` or the `(fail-fast)` warning suffix (Plan consumer scan record; re-verified 2026-11-11).

## Security considerations
Not applicable (documentation-only change).

## Rollback considerations
Single-commit revert restores the bullet; no runtime coupling.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — no findings.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` — no new findings (Plan Documentation Impact).
- `rg -n "failure_policy" docs/` — no hit.

## Completion criteria
- `rg` finds no `failure_policy` mention in `docs/` and the four documentation checks pass.
- No file other than the target document changed.

## Out of Scope
- The code removal in `scripts/shared/mcp_config.py` and `scripts/agent/startup_reporter.py` (documents 1 and 2).
- ADR wording about lease-less recovery, owned by the archived adrrev005 plan and the ADR-001 issue (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-190116 | 20261111-190248 | bullet line 53 deleted; changed: docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md; Details After-text corrected (no preceding blank line exists) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-190248 | no tests; documentation checks only N/A: no tests; documentation checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-190248 | documentation checks in this document's Validation plan check_docs_consistency --domain mcp, check_docs_quality, check_docs_content_policy, check_docs_japanese pass; check_docs_structure: no finding on edited doc (3 pre-existing size warnings on unrelated docs) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-190248 | this document is the documentation change this document is the documentation change; rg -n failure_policy docs/ returns no hit |

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
- **Requirement ID**: `REQ-001` (Plan row AC-1)
- **Source issue**: issues/20261111-163923_compat009_workflow-legacy-compat-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-170504_compat009_workflow-legacy-compat-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-180615
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`