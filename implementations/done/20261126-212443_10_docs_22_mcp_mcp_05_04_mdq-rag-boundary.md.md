## Goal

Run the MDQ/RAG boundary section consistency sweep against current source (REQ-002, REQ-008,
AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file is 5508 B and its scope is the MDQ/RAG boundary per the document map recorded by
  procedure 01.
- The boundary is enforced by layer-separation tests, so the sweep confirms the stated ownership
  against those tests rather than restating it.

## Design decisions
- Data ownership statements use the Plan's ownership vocabulary (Agent owns intent and workflow
  state; MCP owns final pre-handler enforcement and terminal evidence).
- The availability-fallback section is left as written by ADR-004 and referenced, not rewritten.

## Alternatives considered

N/A: the sweep is scoped by the document map.

## Implementation
### Target file
`docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`
### Procedure
- Check the Data Ownership and Agent Access Patterns sections against the implemented layer
  separation and correct any statement that contradicts the code.
- Add the proving-test reference for each claim the sweep changes.
### Method
- Verify the layer separation against `scripts/mcp_servers/mdq/` and the RAG pipeline module
  before writing.
### Details
- Proving test: `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`
  (`test_mdq_layer_has_no_rag_sqlite_references`,
  `test_agent_layer_has_no_direct_mdq_sqlite_access`).

## Compatibility considerations

N/A: documentation-only change; the enforcement section is swept by procedure 11.

## Security considerations

N/A: documentation-only change describing existing boundaries.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py`

## Completion criteria

- No boundary statement contradicts the implementation, and every claim the sweep changed cites
  a proving test that passes.

## Out of Scope

- No boundary behavior change; the pending AAL-019 classification is referenced, not resolved.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | boundary confirmed by tests. Corrections: the RAG-unavailable row has no classifier availability check (only MDQ availability is checked, as live-registry membership of search_docs); tool_transport_invoker.py is under scripts/shared/, not agent/; added proving-test references and the _validate_classification fallback. |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving test | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; 12 passed (test_mdq_rag_boundary + test_mode_classification) |

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
- **Requirement ID**: `REQ-002` (boundary consistency), `REQ-008` (terminology)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`