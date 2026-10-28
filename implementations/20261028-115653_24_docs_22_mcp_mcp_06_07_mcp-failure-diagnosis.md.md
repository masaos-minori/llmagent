# Procedure: replace the ValueError explanation with the routing result kinds

## Goal

Rewrite the "Unknown tool" diagnosis section around the routing result kinds (Plan REQ-008).

## Scope

- Modify only `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The code procedures of this Plan with a lower `seq` have landed.
- All text stays English (`skills/DESIGN.md` Output language).
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md`

### Procedure

- In the section "LLM sees a tool but execution fails with Unknown tool", add the result form: the output now starts with `routing:<kind>:`; map `not_ready` to "set_runtime_registry() was not called or discovery failed", `posture_excluded` to the Security Posture gate, `server_unavailable` to an unavailable or disabled server, `unknown_tool` to a missing or duplicated tool name.
- Replace the "Root cause" paragraph: the resolver raises `ToolRoutingError` (a `ValueError`) and `ToolExecutor.execute()` converts it into the `routing` result.
- Keep diagnosis steps 1-8, updating step 6 to mention the `not_ready` kind.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The section is referenced from other MCP docs; do not rename its heading.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain mcp` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: REQ-008 (diagnosis doc)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md
