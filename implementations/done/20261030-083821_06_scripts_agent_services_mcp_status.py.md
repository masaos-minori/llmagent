# Implementation Procedure: mcp_status.py static-vs-dynamic health display

## Goal

Make MCP diagnostics show static availability and dynamic health as separate,
separately-labeled values (REQ-005; plan AC-4).

## Scope

**In scope:**
- `scripts/agent/services/mcp_status.py`: compute `static_visibility` (new) and `dynamic_health` (new)
  per probed server row.
- Disclosed supporting edits (plan UNK-04, Needs confirmation — neither file is a target
  row): one field on `McpProbeResult` (`scripts/agent/services/models.py:49`) and the
  row-rendering lines in `scripts/agent/commands/cmd_mcp.py`.
- Disclosed supporting test edit in `tests/agent/test_mcp_health_posture.py` (this row's
  Related Tests file in the plan table, not itself a target row).

**Out of scope:**
- Probe semantics (`availability` / `reachable` / health-body interpretation) unchanged.
- Circuit thresholds and the half-open policy (plan Out-of-Scope).

## Assumptions
- Verified at HEAD `124e340b4`: `McpStatusService._probe_single_server_with_interpretation`
  already assembles `availability` (runtime probe state, `McpAvailability` enum —
  `enums.py:20-29`) and `health` = registry state via `_resolve_health_state`
  (`mcp_status.py:48-50`, `:104`, `:140`), plus `health_reason` from the health body
  (`:112-115`). `McpServerConfig.is_disabled` is `startup_mode == StartupMode.NONE`
  (`shared/mcp_config.py:106-108`) — the config-level static exclusion from the LLM tool
  surface (ADR-003 static availability).
- `dynamic_health` (new) composes registry state (already present) with row 02's reason
  derivation and `retry_after_seconds()`; reason is included only when state is
  `UNAVAILABLE`/`HALF_OPEN`.

## Design decisions
- `static_visibility: bool` on `McpProbeResult`, set to `not cfg.is_disabled` in
  `mcp_status` — static visibility is a config fact, distinct from the dynamic probe and
  registry states already carried by `availability`/`health`.
- `dynamic_health` (new) is assembled from existing fields at render time (state value +
  optional reason + optional `retry_after=` seconds) rather than as another stored field:
  the registry state is already on the row as `health`, so only the renderer gains the
  explicit labeled composition — minimal model churn (one new field total).
- Renderer (`cmd_mcp.py`): the per-server status block gains lines
  `Static visibility: visible|excluded` and `Dynamic health: <STATE>[ reason=<code>]
  [ retry_after=<s>]`, keeping every existing line unchanged.

## Alternatives considered
- Folding both into the existing `health` string: rejected — AC-4 requires distinct,
  separately-labeled values; a merged string repeats today's ambiguity (plan Problem).
- Exposing the full `DynamicAvailabilityHint` (new) per row: rejected — diagnostics rows must
  work even for servers never called this process (no results exist); registry-derived
  values are the only always-available source.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
1. Set `static_visibility=not cfg.is_disabled` when constructing each `McpProbeResult`.
2. Add the supporting field to `McpProbeResult` in `agent/services/models.py`
   (disclosed, UNK-04).
3. Add the two renderer lines in `cmd_mcp.py`'s per-server status formatting
   (disclosed, UNK-04), composing reason/`retry_after` (new) from
   `registry.retry_after_seconds(key)` and state.

### Method
- One field, one assignment, two display lines; no probe-flow restructuring.

### Details
- `_resolve_health_state` falls back to `UNAVAILABLE` when the registry is absent — keep
  that fallback in the composed display (registry=None → `reason=server_unavailable`,
  `retry_after` (new) omitted).

## Compatibility considerations
- `cmd_mcp` status-table consumers (human operators) see added lines only; existing lines
  byte-identical (characterization via existing cmd_mcp/status tests).
- `McpProbeResult` field addition is additive with a default (`static_visibility: bool =
  True`) so any other construction sites keep compiling.

## Security considerations
- Display only surfaces registry-owned codes; health-body free text already passes
  through existing truncation/interpretation guards (`_format_health_interpretation`)
  unchanged.

## Rollback considerations
- Removing the field + lines reverts display; `health`/`availability` columns remain the
  today-shape fallback.

## Validation plan
- `tests/agent/test_mcp_health_posture.py` (disclosed extension): a disabled server
  (`startup_mode=none`) renders `excluded` while its registry state still renders in the
  dynamic line; an enabled server renders `visible`; UNAVAILABLE row carries
  `retry_after=<int>`; HEALTHY row carries neither reason nor retry_after.
- `uv run pytest tests/agent/test_mcp_health_posture.py tests/agent -k mcp`; mypy.

## Completion criteria
- Diagnostics output shows static visibility and dynamic health as two labeled values
  per server (AC-4); all pre-existing posture-gating tests in the test file pass
  unchanged.

## Out of Scope
- Guard/runner behavior (rows 04-05), hint production (rows 01-03), docs (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `static_visibility` (new) to `McpProbeResult` and set it in `mcp_status` (UNK-04, Needs confirmation) | Completed | 20261030-203503 | 20261030-203727 |  |
| 2 | Add `cmd_mcp.py` renderer lines for static/dynamic display (UNK-04) | Completed | — | 20261030-203727 |  |
| 3 | Extend `tests/agent/test_mcp_health_posture.py` display assertions | Completed | — | 20261030-203727 |  |
| 4 | Run `uv run pytest tests/agent` and mypy | Completed | — | 20261030-203727 |  |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `scripts/agent/services/mcp_status.py`