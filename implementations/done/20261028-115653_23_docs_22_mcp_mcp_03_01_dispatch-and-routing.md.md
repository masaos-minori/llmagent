# Procedure: document the wiring order and the routing error contract

## Goal

Describe the mandatory wiring order and the four routing result kinds (Plan REQ-008).

## Scope

- Modify only `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`.
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

`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure

- In the routing section, add the wiring order: the health registry is passed at `ToolExecutor` construction; the `RuntimeToolRegistry` is attached with `set_runtime_registry()` after discovery completes and `None` is rejected.
- Replace the "Critical failure mode" sentence: when the registry is not wired, `ToolExecutor.execute()` returns a `routing:not_ready` result and no tool runs.
- Add the error contract: a routing failure returns `ToolCallResult` with `is_error=True` and `error_type="routing"`; the output starts with `routing:<kind>:`, kinds `not_ready`, `unknown_tool`, `posture_excluded`, `server_unavailable`; dynamic `UNAVAILABLE` / `HALF_OPEN` results keep their existing form.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- Keep implementation detail minimal (`skills/DESIGN.md` Docs content policy): state the contract, not code.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261028-182149 | Added wiring order + routing error contract to ToolRouteResolver section; augmented Critical failure mode with routing:not_ready. Verified against route_resolver.py/tool_executor.py source. |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | — | 20261028-182149 | quality/structure/content_policy/japanese clean. consistency --domain mcp: 1 pre-existing warning in mcp_03_03 (set_health_registry typo), out of scope. |

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
- **Requirement ID**: REQ-008 (dispatch doc)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md