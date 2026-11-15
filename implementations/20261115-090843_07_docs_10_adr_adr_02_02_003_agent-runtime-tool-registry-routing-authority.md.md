## Goal

Register the residual static `tool_definitions` fallback and static operator counts as a Known Deviation in ADR-003 until this Plan's fix lands. (`REQ-006`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-003 (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`) is the sole-routing-authority ADR and the correct home for the Known Deviations entry.
- The fix (this Plan) removes the residual fallback/counts; the Known Deviation documents the pre-fix state while the fix is open.

## Design decisions
- Add a Known Deviations row stating that, until the fix lands, the LLM-facing static fallback (`llm_turn_runner.py::_stream_llm`) and the static operator counts (`cmd_mcp.py`, `registry.py`) coexist with the `RuntimeToolRegistry` sole-authority principle.
- Keep Known Deviations in sync via `tools/check_known_deviation_sync.py`.

## Alternatives considered
- Documenting the deviation inline in the body: the Known Deviations section is the structured, checkable home.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Open the "Known Deviations" section of ADR-003.
2. Add a row documenting the residual deviation: while this Plan's fix is open, (a) `_stream_llm()` falls back to `ctx.cfg.tool.tool_definitions` when the registry is absent, and (b) `/mcp status` (`cmd_mcp.py`) and `/help` (`registry.py`) print a static `len(ctx.cfg.tool.tool_definitions)` count alongside the `RuntimeToolRegistry` diagnostics table. Note that these are removed by this Plan once it lands.
3. Run `uv run python tools/check_known_deviation_sync.py` and confirm it passes.

### Method
Locate the Known Deviations table with `grep -n -i "Known Deviation" docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; append the row; run the sync checker.

### Details
- The ADR already states (line 34) that routing authority is consolidated into `RuntimeToolRegistry`; this Known Deviation records the known runtime discrepancy (fallback + static counts) that the sole-authority principle does not yet fully reflect until the fix lands.

## Compatibility considerations
Documentation-only; no production impact.

## Security considerations
Records that a static fallback (a potential over-exposure of unavailable/disavailable tools) is a known, tracked deviation pending removal.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run python tools/check_known_deviation_sync.py` passes.
- ADR-003's Known Deviations section lists the residual fallback/count.

## Completion criteria
- ADR-003 Known Deviations documents the residual static fallback and counts until the fix lands.

## Out of Scope
- Changing the routing decision itself (implementation lives in `runtime_tool_registry.py`).
- The agent/MCP doc updates (separate row, `REQ-006`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` — register residual static fallback/count in ADR-003 Known Deviations
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
