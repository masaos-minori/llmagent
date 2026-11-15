## Goal

Confirm that ADR-003's Known Deviations correctly records no residual deviation, because this Plan's fix (`_01` `llm_turn_runner.py`, `_02` `cmd_mcp.py`, `_03` `registry.py`) already removed the static `tool_definitions` fallback and static operator counts. (`REQ-006`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-003 (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`) is the sole-routing-authority ADR and the correct home for the Known Deviations entry.
- **Resolved by implementation:** this Plan's fix (`_01` `llm_turn_runner.py`, `_02` `cmd_mcp.py`, `_03` `registry.py`) already removed the static fallback (`_stream_llm()` now raises when the registry is absent) and the static operator counts (`/mcp status` and `/help` now read `RuntimeToolRegistry.diagnostics()`). The residual deviation this row was drafted to register no longer exists.

## Design decisions
- Adversarial verification (Step 3a) confirms the static fallback and static counts are removed from every runtime path (`grep` shows no `ctx.cfg.tool.tool_definitions` reader in `cmd_mcp.py`/`registry.py` and a typed `raise` in `llm_turn_runner.py`). There is no current deviation to register.
- Therefore NO Known Deviations row is added; ADR-003's Known Deviations section correctly stays "Not applicable". Adding a row describing a removed fallback would contradict Invariant INV-02 and record a non-existent deviation.
- Keep Known Deviations in sync via `tools/check_known_deviation_sync.py`.

## Alternatives considered
- Documenting the deviation inline in the body: the Known Deviations section is the structured, checkable home.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Verify (via `grep`) that the static fallback and static counts are removed from every runtime path. Record the confirmation.
2. Confirm ADR-003's Known Deviations section currently reads "Not applicable" and that `check_known_deviation_sync.py` reports no issues.
3. Make no ADR edit: there is no residual deviation to register because this Plan's fix landed before this row executed.

### Method
Locate the Known Deviations table with `grep -n -i "Known Deviation" docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; append the row; run the sync checker.

### Details
- The ADR already states (line 34) that routing authority is consolidated into `RuntimeToolRegistry`. Because this Plan's fix removed the fallback and static counts, there is no residual discrepancy; the Known Deviations section correctly stays "Not applicable". AC-5's "while the fix is open" condition no longer holds — the fix is closed, so the interim registration is superseded by the actual removal.

## Compatibility considerations
Documentation-only; no production impact.

## Security considerations
Records that a static fallback (a potential over-exposure of unavailable/disavailable tools) is a known, tracked deviation pending removal.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run python tools/check_known_deviation_sync.py` passes ("No issues found").
- ADR-003's Known Deviations section correctly shows "Not applicable" (no residual deviation).

## Completion criteria
- ADR-003 Known Deviations correctly records no residual static fallback/count because this Plan's fix removed them; `check_known_deviation_sync.py` passes with no issues.

## Out of Scope
- Changing the routing decision itself (implementation lives in `runtime_tool_registry.py`).
- The agent/MCP doc updates (separate row, `REQ-006`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-185114 | 20261115-185114 | REQ-006: adversarial verification - residual fallback/count REMOVED by _01/_02/_03; no ADR Known Deviation needed (INV-02); check_known_deviation_sync passes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-185114 | 20261115-185114 | check_known_deviation_sync.py: No issues found; ADR unchanged |

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