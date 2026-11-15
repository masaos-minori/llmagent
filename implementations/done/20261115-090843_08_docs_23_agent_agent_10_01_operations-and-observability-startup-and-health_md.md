## Goal

Document the single-runtime-tool-authority intent and the typed fail-closed behavior when `RuntimeToolRegistry` is absent in the startup/health operations doc (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The current `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` covers startup-validation stages, severity mapping, `tool_definitions` drift severity, and the ADR-004 posture fail-closed abort, but omits the runtime-tool-authority single-authority/fail-closed intent (verified against current source on 2026-11-15).
- `ADR-003` (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`) is the sole-routing-authority ADR and the normative home for the single-authority principle.
- The related doc `agent_07_07_cli-and-commands-slash-commands-session-mcp.md` already states that `/mcp tools` prints the `RuntimeToolRegistry` diagnostics table, so single-authority is documented elsewhere; only the startup/health doc carries the gap.
- "Registry absent" means the `RuntimeToolRegistry` instance was never constructed (a wiring error), distinct from "empty registry" (constructed with zero tools), which stays a valid no-tools surface where component mandatoriness allows (`UNK-01`).

## Design decisions
- Add a bullet under **Key Constraints** documenting that LLM tool exposure reports one authority, `RuntimeToolRegistry`; when the registry is absent after startup, `LLMTurnRunner._stream_llm()` fails closed by raising a typed configuration/wiring error instead of returning static `ctx.cfg.tool.tool_definitions` (`AC-1`, `AC-3`).
- Cross-reference `ADR-003` (sole routing authority) and note the empty-registry boundary (`UNK-01`).

## Alternatives considered
- A one-line note inside the existing severity-mapping section: a dedicated constraint bullet is clearer and more discoverable.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Open `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.
2. Add a bullet under **Key Constraints** (or a short subsection under **Operational Notes**) documenting: LLM tool exposure reports one authority, `RuntimeToolRegistry`; when the registry is absent after startup, `_stream_llm()` fails closed by raising a typed configuration/wiring error rather than returning static `tool_definitions` (`AC-1`, `AC-3`); an empty registry remains a valid no-tools surface where component mandatoriness permits (`UNK-01`).
3. Reference `ADR-003` as the sole-routing-authority ADR.
4. Run `uv run python tools/check_docs_consistency.py --domain agent` and confirm it passes.

### Method
Locate the anchor with `grep -n -i "Key Constraints" docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`; insert the bullet among the existing constraints, preserving semantic ordering.

### Details
- The current doc covers startup-validation stages, severity mapping, `tool_definitions` drift severity (line 70), and the ADR-004 posture fail-closed abort (line 74), but does not state that runtime LLM tool authority is singular or that a missing registry fails closed. The residual static fallback (`llm_turn_runner.py::_stream_llm`) is exactly the deviation ADR-003's Known Deviations records until this Plan's fix lands.

## Compatibility considerations
Documentation-only; no production impact.

## Security considerations
Records that the residual static fallback (a potential over-exposure of unavailable/disavailable tools) is superseded by a fail-closed contract owned by `RuntimeToolRegistry`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent` passes.
- The doc names `RuntimeToolRegistry` as the sole runtime tool authority and documents the typed fail-closed behavior when it is absent.

## Completion criteria
- `agent_10_01` documents the single-runtime-tool-authority intent and the typed fail-closed behavior when `RuntimeToolRegistry` is absent.

## Out of Scope
- Modifying source code (owned by other rows of this Plan).
- Editing `scripts/shared/tool_constants.py` (assigned to `sideeffect001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-185234 | 20261115-185234 | REQ-006: added single-runtime-tool-authority/fail-closed bullet under Key Constraints; check_known_deviation_sync N/A (ADR unchanged) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-185234 | 20261115-185234 | check_docs_consistency --domain agent, check_docs_quality/structure/content_policy/japanese all clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-185234 | 20261115-185234 | doc-only change; validation passed |

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
- **Requirement ID**: `REQ-006` — document single-runtime-tool-authority intent and fail-closed behavior in the startup/health doc
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`