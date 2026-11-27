## Goal

Remove the statement that `config_dependent` is `false` for the MDQ tools, so the documented value matches the corrected tool metadata (REQ-008 documentation, REQ-001 metadata).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 7 is not listed in any `### Release units` entry)

## Assumptions
- Documentation-only row: the lightweight fill applies.
- Cross-plan overlap: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also targets this file. It is compatible — that plan does not change the same sentence; this row corrects only the MDQ value.
- No tool generates this statement (`grep` over `tools/` finds no generator writing `config_dependent`), so the correction is a direct edit of the prose.

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure
- In line 25, change the MDQ part of the sentence so MDQ tools are `true`, matching `scripts/mcp_servers/mdq/mdq_tools.py` (seq 07).
- Leave the file servers and `rag_pipeline` statements unchanged.

### Method
- N/A: one sentence change.

### Details
- The `false` list currently names the file servers, `mdq`, and `rag_pipeline`; only `mdq` is removed from it.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Completion criteria
- No doc still claims MDQ tools are configuration-independent (AC-7).
- The documented value matches the declared metadata after seq 07.

## Out of Scope
- The tool metadata change itself (seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the documentation checker named in `rules/tool-gates.md` | Pending | — | — | `uv run python tools/check_docs_content_policy.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-008 (documentation of the availability metadata), REQ-001 (per-tool availability)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`
