# Plan: Make RuntimeToolRegistry the sole runtime tool authority

## Goal
Remove the static `tool_definitions` fallback and static counts from the runtime paths so that LLM tool exposure and the `/mcp status`, `/mcp tools`, and `/help` displays all report one authority, `RuntimeToolRegistry`.

## Priority
High

## Scope
- **In-Scope**:
  - Remove the static `tool_definitions` fallback from `LLMTurnRunner._stream_llm()` in `scripts/agent/llm_turn_runner.py`; raise a typed configuration/wiring error when the registry is absent.
  - Replace the `/mcp status` static count in `scripts/agent/commands/cmd_mcp.py` with registry totals (LLM-visible, disabled, unavailable).
  - Update the `/help` implementation in `scripts/agent/commands/registry.py` to read runtime totals from the registry.
  - Preserve an empty but concrete registry as a valid no-tools LLM surface only where component mandatoriness allows it.
  - Revise `ToolConfig.tool_definitions` comments in `scripts/agent/config_dataclasses.py` after all runtime consumers are gone.
  - Update command tests that assert the static count; add tests for the runtime totals.
  - Register the current fallback and count behavior in ADR-003 Known Deviations until the fix lands.
  - Update the agent and MCP documents that describe `/mcp status`, `/mcp tools`, and tool authority.
- **Out-of-Scope**:
  - Changes to `RuntimeToolRegistry` discovery or availability logic.
  - Removing the static definition file or its drift validation.
  - MCP route or dispatch changes.
  - Editing the contradictory routing comment in `scripts/shared/tool_constants.py` — assigned to `issues/20261111-163800_sideeffect001_side-effect-classification-central.md` (see Dependencies).
- **Dependencies**:
  - **Depends on**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md` | phase all | owns the single edit to the contradictory `tool_constants.py` routing comment that this Plan must also stop citing; this Plan treats `tool_constants.py` as read-only and leaves the edit to that Issue.
  - `plans/20261111-110144_adrrev017_docs-history-wording.md` (sequencing note, documentation only): edits ADR-003 and `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` wording; re-verify ADR-003 text after it lands to avoid a documentation conflict. If that Plan is not open, this note does not apply.

## Background
Source: `memo-issue.md` (Issue F), re-verified against current source on 2026-11-15.

- `Confirmed by repository evidence`: `LLMTurnRunner._stream_llm()` in `scripts/agent/llm_turn_runner.py` lines 354-366 uses `registry.llm_tool_definitions()` when a registry exists and otherwise `ctx.cfg.tool.tool_definitions`. (checked in Step 2/3)
- `Confirmed by repository evidence`: `scripts/agent/commands/cmd_mcp.py` line 128 prints `f"  Tools {len(ctx.cfg.tool.tool_definitions)} (from config/tools_definitions.toml)"`, and lines 245-294 of the same command render a `RuntimeToolRegistry` diagnostics table (`"Tools (RuntimeToolRegistry):"`). Both the static count and the registry diagnostics appear in one `/mcp status` output. (checked in Step 2/3)
- `Confirmed by repository evidence`: `scripts/agent/commands/registry.py` line 101 in `_cmd_help()` reads `n_tools = len(ctx.cfg.tool.tool_definitions)` — this is the `/help` tool-count source. (checked in Step 2/3)
- `Confirmed by repository evidence`: `ToolConfig.tool_definitions` (`scripts/agent/config_dataclasses.py` line 214) carries a comment (lines 207-218) that itself states it is "Still read at runtime in two places: `llm_turn_runner.py::_stream_llm()` ... and `cmd_mcp.py` + `registry.py`". (checked in Step 2/3)
- `Confirmed by repository evidence`: the contradictory routing comment in `scripts/shared/tool_constants.py` lines 122-126 ("`ToolRegistry` ... is the canonical/fallback routing source") contradicts lines 10-11 ("Not a routing source"). Shared with `sideeffect001`. (checked in Step 2/3)
- `Confirmed by repository evidence`: ADR-003 is `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` ("RuntimeToolRegistry as the Sole Routing Authority"), the correct home for the Known Deviations entry. (checked in Step 2/3)
- `Needs confirmation`: the exact `/help` command test path and the command tests that assert the static count (candidates: `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_command_registry_consistency.py`).

## Problem
Two tool authorities coexist at runtime. When the registry is absent, the LLM receives static definitions that may not match the live MCP surface, and operator-facing commands show a static `tool_definitions` count next to the `RuntimeToolRegistry` diagnostics table. The runtime authority is documented as the registry, but code still honors a static fallback.

## Reason for Change
This is a wiring and correctness risk (the LLM can be offered tools that are unavailable or disabled) and the discrepancy is visible to operators. No separate deadline; severity follows the runtime-correctness criterion.

## Implementation Intent
- Treat registry absence after startup as a typed wiring error (fail closed), not a trigger for a fallback.
- Keep an empty but concrete registry valid as a no-tools surface, subject to component mandatoriness rules.
- Make all operator displays read runtime totals from the registry (LLM-visible, disabled, unavailable).
- Narrow static `tool_definitions` to drift validation and fixtures only, after the last runtime consumer is removed.

## Requirements
- `REQ-001`: Remove the static fallback from `LLMTurnRunner._stream_llm()`; raise a typed configuration or wiring error when the registry is absent.
- `REQ-002`: Replace the `/mcp status` static count in `cmd_mcp.py` with registry totals including LLM-visible, disabled, and unavailable counts.
- `REQ-003`: Update the `/help` implementation in `registry.py` to read runtime totals from the registry instead of `ctx.cfg.tool.tool_definitions`.
- `REQ-004`: Revise `ToolConfig.tool_definitions` comments in `config_dataclasses.py` after all runtime consumers are gone.
- `REQ-005`: Update command tests that assert the static count; add tests for the runtime totals and the typed fail-closed error.
- `REQ-006`: Register the current fallback/count behavior in ADR-003 Known Deviations until the fix lands, and update the agent/MCP documents describing `/mcp status`, `/mcp tools`, and tool authority.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).
Amended 2026-11-15 (scope): replaced the Agent/MCP docs group row with the concrete target `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` after adversarial verification found only that doc has a single-runtime-tool-authority/fail-closed gap; `agent_10_01` moved from Reference Files to Implementation Target Files.

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Modify | Delete the `else ctx.cfg.tool.tool_definitions` fallback in `_stream_llm()`; raise a typed error when the registry is absent. | REQ-001 | `_stream_llm()` lines 354-366, `registry.llm_tool_definitions() if registry else ...tool_definitions` (checked in Step 2/3) | unit tests for `_stream_llm()` with/without registry | Verified |
| `scripts/agent/commands/cmd_mcp.py` | Modify | Replace the static `len(ctx.cfg.tool.tool_definitions)` count (line 128) with registry totals from `tool_registry.diagnostics()`. | REQ-002 | static count line 128; registry diagnostics table lines 245-294 (checked in Step 2/3) | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| `scripts/agent/commands/registry.py` | Modify | Read the tool count from the registry in `_cmd_help()` instead of `ctx.cfg.tool.tool_definitions`. | REQ-003 | `_cmd_help()` line 101 `n_tools = len(ctx.cfg.tool.tool_definitions)` (checked in Step 2/3) | command registry tests | Verified |
| `scripts/agent/config_dataclasses.py` | Modify | Revise the `ToolConfig.tool_definitions` comment (lines 207-218) once the last runtime consumer is removed. | REQ-004 | comment at lines 207-218 admits two runtime readers (checked in Step 2/3) | N/A | Verified |
| `tests/agent/commands/test_cmd_mcp.py` | Modify | Update assertions that expect the static tool count; assert registry totals. | REQ-005 | existing `/mcp status` command test | this file | Verified |
| `tests/agent/commands/test_command_registry_consistency.py` | Modify | Update any static-count assertion in the command-registry test. | REQ-005 | command consistency test | this file | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Add a Known Deviations entry for the residual static fallback/count until the fix lands. | REQ-006 | ADR-003 is the sole-routing-authority ADR (checked in Step 2/3) | `check_known_deviation_sync.py` | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Document the single-runtime-tool-authority intent and the typed fail-closed behavior when `RuntimeToolRegistry` is absent (REQ-006/AC-1/AC-3), which the current startup/health doc omits. | REQ-006 | current doc covers startup-validation stages, severity mapping, `tool_definitions` drift severity (line 70), ADR-004 posture fail-closed (line 74), but not runtime-tool-authority single-authority/fail-closed intent | `check_docs_consistency.py --domain agent` | Verified |

Rules:
- One row per file. No directory, glob pattern, component/module name, file group, or vague phrase appears as a row.
- Test, configuration, schema, migration, deployment, or documentation files are their own rows, not folded into the source file they accompany.
- `Validation Status` is `Verified` for every row before freeze. Every path was confirmed to exist via `rg`/`ls`/`find` in Step 2/3.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/runtime_tool_registry.py` | `diagnostics()` shape (LLM-visible/disabled/unavailable totals) the displays must report. | REQ-002, REQ-003 |
| `scripts/shared/tool_constants.py` | The contradictory routing comment (lines 122-126); read to understand current state, edit assigned to `sideeffect001`. | REQ-004, Scope |
| `scripts/services/tool_validation.py` | `_check_tool_definitions` drift validation still consumes `tool_definitions`; must remain intact. | REQ-004 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` (Known Deviations section only) | Where the interim deviation is registered. | REQ-006 |

## Acceptance Criteria
- `AC-1`: No LLM call receives static tool definitions at runtime. (`REQ-001`)
- `AC-2`: `/mcp status`, `/mcp tools`, and `/help` report the registry as the single authority. (`REQ-002`, `REQ-003`)
- `AC-3`: Registry absence raises a typed fail-closed error and does not trigger a fallback. (`REQ-001`)
- `AC-4`: Static definitions remain only for drift validation and fixtures. (`REQ-004`)
- `AC-5`: The interim fallback/count behavior is registered in ADR-003 Known Deviations while the fix is open. (`REQ-006`)

## Tests
- Unit tests for `_stream_llm()` with and without a registry (typed error, empty registry, populated registry). (`REQ-001`, `AC-1`, `AC-3`)
- Command tests asserting registry totals in `/mcp status` and `/help` replace the static-count assertions. (`REQ-002`, `REQ-003`, `AC-2`)
- Config-dataclass test confirming the revised `tool_definitions` comment no longer claims runtime readers. (`REQ-004`, `AC-4`)
- Run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports`, targeted pytest, `uv run python tools/check_known_deviation_sync.py`, and `uv run python tools/check_docs_consistency.py --domain agent`. (`REQ-005`, `REQ-006`)

## Documentation Impact
Update ADR-003 Known Deviations and Verification, and the agent and MCP documents that describe `/mcp status`, `/help`, and tool authority (named via `docs/00_index.md` → task mapping): intent, failure behavior (fail closed), and Needs Confirmation items. Run `uv run python tools/check_known_deviation_sync.py` and `uv run python tools/check_docs_quality.py`. (`REQ-006`)

## Assumptions
- "Registry absent" means the `RuntimeToolRegistry` instance was never constructed (a wiring error), distinct from "empty registry" (constructed with zero tools), which stays a valid no-tools surface where component mandatoriness allows it.
- The `tool_constants.py` contradictory-comment edit belongs to `sideeffect001`; this Plan reads that file only, so the two Plans do not both modify it (avoids a frozen-plan overlap).
- `ADR-003` wording edits by `adrrev017` (if open) are re-verified after they land; if that Plan is not open, this assumption does not apply.
- `deploy.sh` rsyncs `scripts/` wholesale, so Python changes need no `deploy.sh` update.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | Whether an empty `RuntimeToolRegistry` is a valid no-tools startup state for optional MCP-only configurations, or a startup error. | Component mandatoriness policy. | Preserve an empty concrete registry as valid where mandatoriness allows; raise only when the registry is absent (not merely empty). Record the boundary in Design. | False |
| `UNK-02` | Which exact command tests assert the static count beyond the two candidates listed. | Resolved during implementation by searching `tests/` for `tool_definitions` count assertions. | Search `tests/` for the static-count assertion and update each. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Modify | LLM turn path; removes a runtime fallback | 12 | owner-dominant | not applicable (rsynced) |
| `scripts/agent/commands/cmd_mcp.py` | Modify | `/mcp status` operator output | 4 | shared (operator commands) | not applicable (rsynced) |
| `scripts/agent/commands/registry.py` | Modify | `/help` operator output | 3 | shared (operator commands) | not applicable (rsynced) |
| `scripts/agent/config_dataclasses.py` | Modify | comment-only after consumers gone | 20 | shared (config layer) | not applicable (rsynced) |
| `tests/agent/commands/test_cmd_mcp.py` | Modify | command test suite | 3 | shared (test suite) | not applicable (rsynced) |
| `tests/agent/commands/test_command_registry_consistency.py` | Modify | command test suite | 3 | shared (test suite) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | ADR Known Deviations | 8 | N/A | N/A |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | startup/observability doc | N/A | N/A | N/A |

## Design
Path B: affects > 3 files and changes runtime tool-exposure behavior (introduces a typed fail-closed contract on the LLM tool list).

- **Fail-closed injection (`REQ-001`)**: `_stream_llm()` currently does `registry.llm_tool_definitions() if registry else ctx.cfg.tool.tool_definitions`. Replace with a guard that raises a typed configuration/wiring error when `registry is None`. The empty-registry case (`registry` exists, zero tools) stays valid where component mandatoriness permits (UNK-01); only a missing instance fails closed. This keeps AC-5's non-fatal save contract untouched (different path). (Step 3)
- **Operator totals (`REQ-002`, `REQ-003`)**: read `tool_registry.diagnostics()` (shared/runtime_tool_registry.py) for LLM-visible/disabled/unavailable totals in both `/mcp status` (`cmd_mcp.py`) and `/help` (`registry.py`), replacing the two static `len(ctx.cfg.tool.tool_definitions)` reads. (Step 3)
- **Comment revision (`REQ-004`)**: after Phase 1-2 remove both runtime readers, revise the `ToolConfig.tool_definitions` comment (config_dataclasses.py:207-218) to state it is drift-validation/fixtures only. Do not delete the field (drift validation and test fixtures still use it). (Step 3)
- **Interim documentation (`REQ-006`)**: register the residual static fallback/count in ADR-003 Known Deviations until the fix lands, keeping Known Deviations in sync (`tools/check_known_deviation_sync.py`). (Step 3)
- **Blast radius**: the static field is also consumed by drift validation (`tool_validation.py::_check_tool_definitions`) and fixtures — both stay. The two runtime readers are the only removals. (Step 3)

## Implementation steps
Each step cites the exact file path(s) it touches by referencing rows of `Implementation Target Files` above.

1. **Phase 1: Fail-closed LLM tool list**
   - [ ] Delete the `else ctx.cfg.tool.tool_definitions` fallback in `scripts/agent/llm_turn_runner.py`; raise a typed error when the registry is absent. [`scripts/agent/llm_turn_runner.py`] (REQ-001)
2. **Phase 2: Operator displays read the registry**
   - [ ] Replace the static `/mcp status` count with registry totals in `scripts/agent/commands/cmd_mcp.py`. [`scripts/agent/commands/cmd_mcp.py`] (REQ-002)
   - [ ] Read `/help` tool count from the registry in `scripts/agent/commands/registry.py`. [`scripts/agent/commands/registry.py`] (REQ-003)
3. **Phase 3: Comment + tests + docs**
   - [ ] Revise `ToolConfig.tool_definitions` comment after the last runtime consumer is gone. [`scripts/agent/config_dataclasses.py`] (REQ-004)
   - [ ] Register the interim deviation in ADR-003. [`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`] (REQ-006)
   - [ ] Document single-runtime-tool-authority intent and fail-closed behavior in the startup/health doc. [`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`] (REQ-006)
   - [ ] Update static-count command tests; add registry-total and typed-error tests. [`tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_command_registry_consistency.py`] (REQ-005)
4. **Phase 4: Validation suite**
   - [ ] Run the full validation sequence (`rules/toolchain.md`): ruff, mypy, import-linter, bandit, targeted pytest, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain agent`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Unit: typed error without registry, empty registry, populated registry | targeted pytest | Pass |
| `scripts/agent/commands/cmd_mcp.py`, `registry.py` | Integration: `/mcp status` and `/help` report registry totals | targeted pytest | Pass |
| `scripts/agent/config_dataclasses.py` | Unit: revised comment reflects no runtime readers | review | Pass |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Known Deviations sync | `uv run python tools/check_known_deviation_sync.py` | Pass |
| Agent/MCP docs | Doc consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: Failing closed on a missing registry breaks optional MCP-only configs that legitimately have no registry. → **Mitigation**: fail closed only when the registry instance is absent, not when it is empty; preserve empty-registry validity per component mandatoriness (UNK-01).
- **Risk**: Removing the static reader while drift validation still needs the field. → **Mitigation**: keep `tool_definitions` for drift validation (`tool_validation.py`) and fixtures; remove only the two runtime readers (AC-4).
- **Risk**: Editing `tool_constants.py` in both this Plan and `sideeffect001`. → **Mitigation**: this Plan treats `tool_constants.py` as a reference file; the edit is assigned to `sideeffect001` (recorded in Dependencies).
- **Risk**: ADR-003 wording conflict with `adrrev017`. → **Mitigation**: re-verify ADR-003 text after `adrrev017` lands; record as sequencing note.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fail-closed LLM tool list (REQ-001) | In Progress | — | — | `llm_turn_runner.py` |
| 2 | Operator displays read the registry (REQ-002/003) | In Progress | — | — | `cmd_mcp.py`, `registry.py` |
| 3 | Comment + tests + docs (REQ-004/005/006) | In Progress | — | — | `config_dataclasses.py`, tests, ADR-003, agent/MCP docs |
| 4 | Validation suite | Pending | — | — | rules/toolchain.md |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261115-090843_01_scripts_agent_llm_turn_runner.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261115-090843_02_scripts_agent_commands_cmd_mcp.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261115-090843_03_scripts_agent_commands_registry.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261115-090843_04_scripts_agent_config_dataclasses.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261115-090843_05_tests_agent_commands_test_cmd_mcp.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261115-090843_06_tests_agent_commands_test_command_registry_consistency.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261115-090843_07_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261115-090843_08_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health_md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-050235
- **Related target files**: `scripts/agent/llm_turn_runner.py`, `scripts/agent/commands/cmd_mcp.py`, `scripts/agent/commands/registry.py`, `scripts/agent/config_dataclasses.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_command_registry_consistency.py`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (remove static fallback, fail closed) | `scripts/agent/llm_turn_runner.py` | Phase 1 | AC-1, AC-3 | `_stream_llm()` unit tests | Confirmed by repository evidence |
| REQ-002 | Required Changes (/mcp status count → registry) | `scripts/agent/commands/cmd_mcp.py` | Phase 2 | AC-2 | cmd_mcp command test | Confirmed by repository evidence |
| REQ-003 | Required Changes (/help reads static defs) | `scripts/agent/commands/registry.py` | Phase 2 | AC-2 | registry consistency test | Confirmed by repository evidence |
| REQ-004 | Required Changes (revise ToolConfig comments) | `scripts/agent/config_dataclasses.py` | Phase 3 | AC-4 | comment review | Confirmed by repository evidence |
| REQ-005 | Testing Expectations | `tests/agent/commands/test_cmd_mcp.py`, `test_command_registry_consistency.py` | Phase 3 | N/A: test-only | targeted pytest | Confirmed by repository evidence |
| REQ-006 | Documentation Impact | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Phase 3 | AC-5 | check_known_deviation_sync, check_docs_consistency | Confirmed by repository evidence |