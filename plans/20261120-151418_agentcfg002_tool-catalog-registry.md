## Goal
- Remove the static tool catalog (`[[tool_definitions]]`) and per-server tool-name lists (`tool_names`) from `config/agent.toml`, move the static server-ownership and required-capability checks into a dedicated machine-readable registry, and make live `/v1/tools` discovery the single source of tool schema, description, capabilities, and server key.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete every `[[tool_definitions]]` block and `tool_names` entry from `config/agent.toml`.
  - Remove `ToolConfig.tool_definitions` (field, section builder, config-field-registry entry) and `McpServerConfig.tool_names` (field, validator, section builder, reload/valid-key entries).
  - Reject any remaining `tool_definitions` / `tool_names` key in `agent.toml` with a specific message (no compatibility reader).
  - Replace the `_check_tool_definitions` `tool_definitions`-vs-live comparison with a drift check against the new static ownership/capability registry and the routing registry; make a static-vs-live server-ownership mismatch fatal.
  - Express a required server's requirement as a required capability / registry-manifest entry instead of a tool-name list, and detect a missing required capability at startup.
  - Remove the `tools_definitions.toml` wording from the validation warnings.
  - Migrate tests that build tool definitions from TOML fixtures to a factory independent of TOML.
  - Update the documentation that describes `[[tool_definitions]]` as the LLM-facing schema source.
- **Out-of-Scope**:
  - Safety, approval, preview, and resource metadata (`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`).
  - The tool-exposure policy (`issues/20261120-114209_agentcfg001_tool-policy-mode.md`).
  - The `アサインees` typo in an `agent.toml` tool description (removed with its `[[tool_definitions]]` block).
  - The home of `McpServerConfig.role`, timeouts, rotation, stagger, and `required` (the MCP lifecycle components decide; this issue removes only `tool_names`).

- **Dependencies**: The Issue is ordered after `issues/20261120-114209_agentcfg001_tool-policy-mode.md` and before `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`.
  - **Depends on**: `plans/done/20261120-123941_agentcfg001_tool-policy-mode.md` | phase all | both edits touch `AgentConfig`/`ToolConfig`/`McpServerConfig`; `agentcfg001` is not yet implemented (its Plan rows are not `Completed`), so implement it first to avoid conflicting `agent.toml` edits.

## Background
Source: consolidated `agent.toml` reduction backlog. Tool names, descriptions, input schemas, and server ownership are duplicated across the MCP servers, the static registries, `[[tool_definitions]]`, `tool_names`, the `RuntimeToolRegistry`, and test fixtures. The duplication produces schema and ownership drift and is the main reason `agent.toml` is large. Live `/v1/tools` discovery already builds a `RuntimeTool` carrying schema, description, capabilities, and server key, and `_stream_llm()` already treats the `RuntimeToolRegistry` as the sole LLM-facing authority (it raises when the registry is absent).

## Problem
The same tool facts live in several places: the live server responses, `[[tool_definitions]]` (LLM-facing schema template + startup drift input), `tool_names` (per-server required-tool lists), the `RuntimeToolRegistry`, and test fixtures. Drift between copies can hide a missing or reassigned tool, and `agent.toml` grows with data that discovery already recomputes. A secondary defect: the `_check_tool_definitions` warning text names `tools_definitions.toml`, a file that does not exist (the field is read from `agent.toml`), which misleads an operator.

## Reason for Change
Drift between the copies can hide a missing or reassigned tool, and the wrong file name in the warning misleads an operator. Removing the static catalog collapses the source of tool metadata to live discovery and unblocks the metadata consolidation of `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`.

## Implementation Intent
The `RuntimeTool` built from live `/v1/tools` stays the runtime source of description, schema, capabilities, and server key. Static server ownership and required-capability expectations move to a machine-readable registry (a dedicated TOML manifest) that the drift check reads. The static checks stay fail-closed: duplicate tool names and routing drift remain fatal, and a removed config key is rejected with a specific message rather than silently ignored.

## Requirements
- `REQ-001`: The `RuntimeToolRegistry.llm_tool_definitions()` output is the sole LLM-facing tool-schema source; no config-driven fallback to `ToolConfig.tool_definitions` exists in any runtime path.
- `REQ-002`: `ToolConfig.tool_definitions` is removed (dataclass field, `config_section_builders` builder, `config_field_registry` entry) and every `[[tool_definitions]]` block is removed from `config/agent.toml`.
- `REQ-003`: `McpServerConfig.tool_names` is removed (dataclass field, `_validate_tool_names`, section builder, reload/valid-key entries) and every `tool_names` entry is removed from `config/agent.toml`.
- `REQ-004`: The `_check_tool_definitions` `tool_definitions`-vs-live comparison is replaced by a drift check comparing live `/v1/tools` against the new static ownership/capability registry and the routing registry; duplicate tool names and routing drift stay fatal.
- `REQ-005`: A required server's requirement is expressed as a required capability / registry-manifest entry (not a tool-name list); a missing required capability is detected at startup.
- `REQ-006`: A static-vs-live server-ownership mismatch reported by the drift check is fatal.
- `REQ-007`: The `tools_definitions.toml` wording is removed from the validation warnings.
- `REQ-008`: Any remaining `tool_definitions` or `tool_names` key in `config/agent.toml` is rejected with a specific message (Current-Specification-Only; no compatibility reader).
- `REQ-009`: Tests that build tool definitions from TOML fixtures use a factory independent of TOML.
- `REQ-010`: Discovery fetches `/v1/tools` once per server during discovery.
- `REQ-011`: Documentation that describes `[[tool_definitions]]` as the LLM-facing schema source is corrected.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b: every row `Verified`, `audit_plan_target_paths.py` reports 0 findings, `check_plan_target_overlaps.py` reports no overlaps).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `config/agent.toml` | Delete | Remove every `[[tool_definitions]]` block and `tool_names` entry; keep the file on its existing `deploy.sh` cp line | `REQ-002`, `REQ-003`, AC-1 | `[[tool_definitions]]` (63 blocks) and `tool_names` (10 entries) present in `config/agent.toml` (checked in Step 2) | `tests/agent/test_config_builders.py`, `tests/integration/test_production_security_regression.py` | Verified |
| `scripts/agent/config_dataclasses.py` | Modify | Remove `ToolConfig.tool_definitions` and its doc comment | `REQ-002`, AC-1 | `ToolConfig.tool_definitions` field and "no runtime fallback" comment (checked in Step 2) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_section_builders.py` | Modify | Remove the `tool_definitions` section builder | `REQ-002` | `tool_definitions` builder in `config_section_builders` (checked in Step 2) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/services/config_field_registry.py` | Modify | Remove the `tool_definitions` config-field-registry row | `REQ-002` | `ConfigFieldRegistry("tool_definitions", ...)` row (checked in Step 2) | — | Verified |
| `scripts/shared/mcp_config.py` | Modify | Remove `McpServerConfig.tool_names`, `_validate_tool_names`, and its section builder; keep `required` | `REQ-003`, REQ-005 | `McpServerConfig.tool_names` field and `_validate_tool_names` (checked in Step 2) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `scripts/agent/services/tool_validation.py` | Modify | Replace the `tool_definitions`-vs-live comparison with the registry+routing drift check; drop the `tools_definitions.toml` wording | `REQ-004`, `REQ-006`, `REQ-007` | `_check_tool_definitions` compares `ctx.cfg.tool.tool_definitions` to live lists and emits `tools_definitions.toml` warnings (checked in Step 2) | `tests/agent/services/test_mcp_tool_discovery.py`, `tests/shared/test_tool_routing_validation.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery.py` | Modify | Route the required-server check through the required-capability model; keep duplicate-name and drift findings fatal | `REQ-004`, `REQ-005`, AC-3, AC-4 | `_check_required_tools` iterates `McpServerConfig.tool_names` for required servers; drift reuses fetched entries (checked in Step 2) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `scripts/shared/tool_routing_validation.py` | Modify | Compare live tool lists against the new static registry instead of `agent.toml` tool names | `REQ-004`, `REQ-006` | `validate_routing_against_live` compares config tool lists to the registry (checked in Step 2) | `tests/shared/test_tool_routing_validation.py` | Verified |
| `config/tool_catalog.toml` | Create | New machine-readable server-ownership and required-capability registry read by the drift check | `REQ-004`, `REQ-005`, AC-3 | No such registry exists today; ownership lives only in `agent.toml` (checked in Step 2) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `tests/agent/test_config_builders.py` | Modify | Drop the `tool_definitions` fixture / builder assertions that no longer apply | `REQ-002`, `REQ-003`, AC-1 | Test parses `agent.toml` and exercises the removed builders (checked in Step 2) | — | Verified |
| `tests/agent/services/test_mcp_tool_discovery.py` | Modify | Rewrite the required-tool and drift tests for the registry model | `REQ-004`, `REQ-005`, AC-3, AC-4 | Tests drive `_check_required_tools` and the drift findings off `tool_names` / `tool_definitions` (checked in Step 2) | — | Verified |
| `tests/shared/test_tool_routing_validation.py` | Modify | Feed the drift check a registry-shaped input instead of `agent.toml` tool names | `REQ-004`, `REQ-006` | Test asserts config-vs-registry tool matching (checked in Step 2) | — | Verified |
| `tests/agent/test_llm_turn_runner.py` | Modify | Remove references to a `tool_definitions` config fallback that no longer exists | `REQ-001` | Test references `tool_definitions` (checked in Step 2) | — | Verified |
| `tests/agent/test_tool_preparation.py` | Modify | Drop `tool_definitions` fixture references | `REQ-002` | Test references `tool_definitions` (checked in Step 2) | — | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

The complete set of tests that construct a `tool_definitions` fixture is enumerated by `tools/scan_change_consumers.py --seed tool_definitions` during implementation and migrated under `REQ-009`; the rows above are the highest-confidence members. Remaining members (for example `tests/shared/test_runtime_tool_registry.py`, `tests/agent/test_tool_loop_guard.py`, `tests/docs/test_github_config_consistency.py`, `tests/agent/test_repl_health.py`) are covered by the `REQ-009` step, not as separate frozen rows.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/runtime_tool_registry.py` | `llm_tool_definitions()` and the `RuntimeTool` shape are the contract the drift check and LLM path depend on | `REQ-001`, `REQ-004` |
| `scripts/agent/llm_turn_runner.py` | Confirms the registry is the sole LLM-facing authority (raises when absent) | `REQ-001` |
| `scripts/agent/tool_preparation.py` | Confirms no `tool_definitions` fallback in the fail-closed preparation path | `REQ-001`, `REQ-002` |
| `scripts/agent/startup_mcp_starter.py` | Consumes `McpServerConfig`; must keep valid after `tool_names` removal | `REQ-003` |
| `scripts/agent/http_lifecycle.py` | Consumes `McpServerConfig`; must keep valid after `tool_names` removal | `REQ-003` |
| `issues/20261119-145306_cliplc008_mcp-health-capability.md` | Defines the required-capability semantics and `RuntimeTool` diagnostics fields the new model must reuse | `REQ-005` |

## Acceptance Criteria
- AC-1: `config/agent.toml` holds no tool schema, description, or tool inventory. ← `REQ-002`, `REQ-003`
- AC-2: The schema passed to the LLM comes from the `RuntimeToolRegistry`. ← `REQ-001`
- AC-3: A missing required capability is detected at startup. ← `REQ-005`
- AC-4: Duplicate tool names and routing drift stay fatal. ← `REQ-004`, `REQ-006`
- AC-5: Discovery contacts each server once. ← `REQ-010`

## Tests
- Required capability present and missing; static-vs-live ownership match and mismatch; duplicate tool name; malformed schema version and input schema; production startup without `tool_definitions` and `tool_names`. ← `REQ-004`, `REQ-005`, AC-3, AC-4 (`REQ-009`)
- `agent.toml` parses with no tool schema/inventory and rejects a reintroduced key with a specific message. ← `REQ-002`, `REQ-003`, `REQ-008`, AC-1 (`REQ-009`)
- Registry exposes `llm_tool_definitions()` and the LLM path raises when it is absent. ← `REQ-001`, AC-2
- Discovery fetches `/v1/tools` once per server. ← `REQ-010`, AC-5
- Run ruff, mypy, import-linter, and the affected tests (`rules/toolchain.md`).

## Documentation Impact
Yes. `REQ-011` corrects the docs that describe `[[tool_definitions]]` as the LLM-facing schema source and the removed configuration keys. Per `docs/00_index.md` "Document References by Task", the affected topics map to `22_mcp/mcp_03_01_dispatch-and-routing.md` (tool dispatch / LLM schema source), `22_mcp/mcp_03_02_tool-registry.md` (tool registry), `22_mcp/mcp_03_05_lifecycle-and-new-server.md` and `22_mcp/mcp_06_11_new-tool-registration-procedure.md` / `22_mcp/mcp_06_12_new-mcp-server-addition-checklist.md` (new-server / new-tool registration), and `22_mcp/mcp_06_01_configuration-file-inventory.md` (configuration-file inventory). `docs/*.md` are updated by the next pipeline phase, not here.

## Assumptions
- `RuntimeToolRegistry.llm_tool_definitions()` returns one entry per tool with `name`/`description`/`inputSchema`; removing the config catalog does not change this contract.
- The new registry manifest is loaded at startup alongside `agent.toml` and is available to `tool_validation.py`.
- `cliplc008`'s required-capability schema is the canonical one and the new model reuses it unchanged.
- `agent.toml` remains deployed via its existing `deploy.sh` cp line; only the new manifest needs a new cp line.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Where the machine-readable ownership/capability registry lives and who owns it. | No such registry exists today; the Issue marks this `不明`. | Resolved by Design: a dedicated TOML manifest `config/tool_catalog.toml` owned by the agent configuration, read by the drift check. Finalize location/owner at implementation if a better home is found. | False |
| UNK-02 | Whether `role`, timeouts, rotation, stagger, and `required` of `McpServerConfig` stay in a launch/connection manifest. | Decided by the MCP lifecycle components, out of scope here. | This issue removes only `tool_names`; the other fields stay in `McpServerConfig` unchanged. Not resolved by this Plan; no action. | False |
| UNK-03 | `agentcfg001` (`tool_policy_mode`) is listed as a dependency but its Plan rows are not `Completed`. | Repository evidence: `tool_policy_mode`/`disabled_tools` are not in `config_dataclasses.py`; its Plan exists in `plans/done/` with `In Progress` rows. | Implement `agentcfg001` first (recorded as a `Depends on` sequencing dependency). Does not block this Plan's creation. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `config/agent.toml` | Delete | Medium | N/A (not tracked in 30d churn) | N/A (config data) | not applicable (file stays on existing cp line) |
| `scripts/agent/config_dataclasses.py` | Modify | High | 8 | High (single author) | not applicable (rsynced) |
| `scripts/agent/config_section_builders.py` | Modify | Medium | 4 | High (single author) | not applicable (rsynced) |
| `scripts/agent/services/config_field_registry.py` | Modify | Low | 2 | High (single author) | not applicable (rsynced) |
| `scripts/shared/mcp_config.py` | Modify | High | 5 | High (single author) | not applicable (rsynced) |
| `scripts/agent/services/tool_validation.py` | Modify | Medium | 1 | High (single author) | not applicable (rsynced) |
| `scripts/agent/services/mcp_tool_discovery.py` | Modify | Medium | 2 | High (single author) | not applicable (rsynced) |
| `scripts/shared/tool_routing_validation.py` | Modify | Medium | N/A (not measured) | High (single author) | not applicable (rsynced) |
| `config/tool_catalog.toml` | Create | Medium | N/A (new file) | N/A (new file) | add cp line |

## Design
Path B (affects more than three files, introduces a new registry, and changes the public `AgentConfig`/`ToolConfig`/`McpServerConfig` schema and its parsing). Rationale recorded in Step 3.

**Design decision 1 — Registry location and ownership (resolves UNK-01).** The static ownership/capability data leaves `agent.toml` and lives in a dedicated TOML manifest `config/tool_catalog.toml`, owned by the agent configuration (same owner as `agent.toml`). It maps each server key to its owned tools/capabilities and to any required capabilities. Rationale: it is data (not code), so it crosses no import boundary (`shared` is a leaf per `.importlinter`), it is loadable by both `tool_validation.py` and discovery, and it keeps `agent.toml` reduction intact. Alternative considered: a Python module under `scripts/shared/`; rejected because ownership data belongs with configuration, not code, and a manifest avoids a new import chain. Finalize the exact filename/schema at implementation.

**Design decision 2 — Required-capability model (replaces `tool_names`, resolves REQ-005).** `McpServerConfig.required` stays (ADR-004 server escalation); `McpServerConfig.tool_names` is removed. A required server's requirement moves to the registry manifest as a required-capability declaration, and `McpToolDiscoveryService`'s required-check (`_check_required_tools`) becomes a required-capability check: for each `required` server, the manifest declares the needed capability and discovery confirms a surfaced tool provides it; a missing capability is fatal (AC-3). The model reuses `cliplc008`'s required-capability schema unchanged.

**Design decision 3 — Current-Specification-Only (RESOLVES REQ-008).** No compatibility reader is added. A remaining `tool_definitions` or `tool_names` key in `agent.toml` is rejected with a specific message at parse time, so stale configs fail loudly instead of silently ignoring the removed key.

**Design decision 4 — Drift check reshaping (RESOLVES REQ-004, REQ-006).** `_check_tool_definitions` stops comparing against `ctx.cfg.tool.tool_definitions`; the drift check compares live `/v1/tools` against the new registry (ownership) and the routing registry (routing). Duplicate tool names across servers and routing drift remain fatal; a static-vs-live ownership mismatch is a new fatal finding.

**Double-fetch finding.** Within `McpToolDiscoveryService`, the drift check reuses the already-fetched `(server_key, server_url, entry)` tuples (no second call), so there is no intra-discovery double fetch. The module docstring references a cross-module redundancy with `repl_health.py`'s drift-check fetch, but neither `repl_health.py` nor that helper exist in the current source (stale reference). `REQ-010` therefore means: confirm no other caller issues a second `/v1/tools` call and dedupe if found; the discovery module itself already fetches once per server.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`. Phases that land together in one commit cannot be validated alone: declare them as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Remove the static catalog from config and dataclasses** (`REQ-002`, `REQ-003`, `REQ-008`, AC-1)
   - [ ] Delete every `[[tool_definitions]]` block and `tool_names` entry from `config/agent.toml` (`config/agent.toml`).
   - [ ] Remove `ToolConfig.tool_definitions` (field + doc comment) from `scripts/agent/config_dataclasses.py` (`REQ-002`).
   - [ ] Remove the `tool_definitions` section builder from `scripts/agent/config_section_builders.py` (`REQ-002`).
   - [ ] Remove the `tool_definitions` row from `scripts/agent/services/config_field_registry.py` (`REQ-002`).
   - [ ] Reject a reintroduced `tool_definitions`/`tool_names` key in `agent.toml` with a specific message (`REQ-008`).
2. **Phase 2: Remove `McpServerConfig.tool_names`** (`REQ-003`, AC-1)
   - [ ] Remove `McpServerConfig.tool_names`, `_validate_tool_names`, and its section builder from `scripts/shared/mcp_config.py`; keep `required`.
   - [ ] Update the consumers that referenced `tool_names` (`startup_mcp_starter.py`, `http_lifecycle.py`) to the post-removal shape.
3. **Phase 3: Create the ownership/capability registry** (`REQ-004`, `REQ-005`, UNK-01)
   - [ ] Add `config/tool_catalog.toml` with per-server ownership and required-capability declarations (Design decision 1).
   - [ ] Load the manifest at startup and expose it to the drift check.
4. **Phase 4: Replace the drift check and make ownership mismatch fatal** (`REQ-004`, `REQ-006`, `REQ-007`, AC-4)
   - [ ] Rewrite `_check_tool_definitions` in `scripts/agent/services/tool_validation.py` to compare live `/v1/tools` against the new registry and routing registry; drop the `tools_definitions.toml` wording.
   - [ ] Add a fatal static-vs-live ownership-mismatch finding (`REQ-006`).
   - [ ] Update `scripts/agent/services/mcp_tool_discovery.py` and `scripts/shared/tool_routing_validation.py` to the registry-shaped input.
5. **Phase 5: Required-capability model** (`REQ-005`, AC-3) — lands with Phase 4 (release unit below)
   - [ ] Convert `_check_required_tools` in `scripts/agent/services/mcp_tool_discovery.py` to a required-capability check driven by the manifest (`REQ-005`).
   - [ ] Detect a missing required capability at startup as fatal (`AC-3`).
6. **Phase 6: Test fixture migration** (`REQ-009`, AC-1, AC-3)
   - [ ] Migrate the highest-confidence TOML-fixture tests (`tests/agent/test_config_builders.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/test_llm_turn_runner.py`, `tests/agent/test_tool_preparation.py`) to a non-TOML factory.
   - [ ] Enumerate and migrate the remaining `tool_definitions`-fixture tests via `tools/scan_change_consumers.py --seed tool_definitions`.
7. **Phase 7: Single-fetch verification** (`REQ-010`, AC-5)
   - [ ] Confirm discovery fetches `/v1/tools` once per server and dedupe any second call found (`REQ-010`).
8. **Phase 8: Deployment & documentation** (`REQ-011`, deploy hand-off)
   - [ ] Add a `deploy.sh` cp line for `config/tool_catalog.toml` (`REQ-004` target).
   - [ ] Correct the docs that describe `[[tool_definitions]]` as the LLM-facing schema source (`REQ-011`).
   - [ ] Run ruff, mypy, import-linter, and the affected tests; deploy per `skills/deploy/SKILL.md` (committed and pushed first; deploying is the user's decision with an approval gate).

### Release units
**Unit**: `tool_names` removal and required-capability model | **Phases**: 2, 4, 5 | **Reason**: removing `McpServerConfig.tool_names` in Phase 2 breaks `_check_required_tools` before the required-capability model lands in Phase 4-5, and the two must be validated together.
**Unit**: static-catalog removal | **Phases**: 1, 3, 4 | **Reason**: the drift check (Phase 4) reads the new registry (Phase 3) while `agent.toml`/dataclass catalog removal (Phase 1) removes its old input; landing together keeps startup valid.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/agent.toml` | Integration | parse config; assert no `tool_definitions`/`tool_names`; reintroduce a key and assert rejection | clean parse; reintroduced key fails with a specific message (`REQ-002`, `REQ-003`, `REQ-008`) |
| `scripts/shared/mcp_config.py` | Unit | build `McpServerConfig` without `tool_names`; required-server check via manifest | no `tool_names`; missing required capability is fatal (`REQ-003`, `REQ-005`) |
| `scripts/agent/services/tool_validation.py` | Unit/Integration | drift match, drift mismatch, ownership mismatch, malformed schema | matching passes; drift/ownership mismatch fatal (`REQ-004`, `REQ-006`) |
| `scripts/agent/services/mcp_tool_discovery.py` | Integration | required capability present/missing; duplicate name; single fetch | missing capability fatal; duplicate fatal; one `/v1/tools` per server (`REQ-005`, `REQ-010`) |
| `scripts/shared/runtime_tool_registry.py` / `llm_turn_runner.py` | Unit | `llm_tool_definitions()` present; absent registry raises | LLM schema from registry; raises when absent (`REQ-001`) |
| `config/tool_catalog.toml` | Integration | load manifest; ownership match/mismatch | loads; mismatch is fatal (`REQ-004`, `REQ-006`) |

## Risks
- **Risk**: Removing `McpServerConfig.tool_names` breaks `_check_required_tools` before the required-capability model lands. → **Mitigation**: Phase 2, 4, 5 form a release unit that lands together; the required check is converted atomically.
- **Risk**: Many `docs/` files describe `[[tool_definitions]]` as the LLM-facing schema source; an incomplete update misleads operators (the `_stream_llm()` fallback claim in `mcp_03_01` is already stale). → **Mitigation**: `REQ-011` enumerates the affected docs via the consumer scan; correct them in the documentation phase.
- **Risk**: The registry location/owner (UNK-01) is a design choice finalized at implementation. → **Mitigation**: Design decision 1 fixes `config/tool_catalog.toml` as the default; the procedure re-confirms the home before coding.
- **Risk**: Current-Specification-Only rejection (REQ-008) can fail a production startup if a deployed `agent.toml` still contains a removed key. → **Mitigation**: verify the shipped `agent.toml` is already clean (it is: the blocks/entries are removed as part of this change) and that no external config supplies them.
- **Risk**: High bus factor (single author) on the touched modules. → **Mitigation**: small, independently revertable phases; full test + import-linter run in Phase 8.
- **Risk**: Open dependency on `agentcfg001` (UNK-03). → **Mitigation**: recorded as a `Depends on` sequencing dependency; implement it first.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the static catalog from config and dataclasses | Pending | — | — | Touches `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py` |
| 2 | Remove `McpServerConfig.tool_names` | Pending | — | — | Touches `scripts/shared/mcp_config.py`; release unit with Steps 4-5 |
| 3 | Create the ownership/capability registry | Pending | — | — | Touches `config/tool_catalog.toml` |
| 4 | Replace the drift check; make ownership mismatch fatal | Pending | — | — | Touches `scripts/agent/services/tool_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/tool_routing_validation.py`; release unit with Steps 1, 3, 5 |
| 5 | Required-capability model | Pending | — | — | Touches `scripts/agent/services/mcp_tool_discovery.py`; release unit with Steps 2, 4 |
| 6 | Test fixture migration | Pending | — | — | Touches `tests/agent/test_config_builders.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/test_llm_turn_runner.py`, `tests/agent/test_tool_preparation.py` |
| 7 | Single-fetch verification | Pending | — | — | Read-only confirmation; no target row unless a second call is deduped |
| 8 | Deployment & documentation | Pending | — | — | `deploy.sh` cp line for `config/tool_catalog.toml`; doc corrections; ruff/mypy/import-linter/tests |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-114210_agentcfg002_tool-catalog-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-151418
- **Related target files**: `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py`, `scripts/shared/mcp_config.py`, `scripts/agent/services/tool_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/tool_routing_validation.py`, `config/tool_catalog.toml`, `tests/agent/test_config_builders.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/test_llm_turn_runner.py`, `tests/agent/test_tool_preparation.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Implementation Intent; `_stream_llm()` raises when registry absent | `scripts/shared/runtime_tool_registry.py`, `scripts/agent/llm_turn_runner.py` | Step 1 (verify), Step 7 | AC-2 | `llm_tool_definitions()` present; absent registry raises | Confirmed by repository evidence |
| `REQ-002` | Background; `ToolConfig.tool_definitions` field + builder + registry row | `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py` | Step 1 | AC-1 | `agent.toml` parses with no `[[tool_definitions]]` | Confirmed by repository evidence |
| `REQ-003` | Background; `McpServerConfig.tool_names` field + validator + builder | `config/agent.toml`, `scripts/shared/mcp_config.py` | Step 2 | AC-1 | build `McpServerConfig` without `tool_names` | Confirmed by repository evidence |
| `REQ-004` | Required Changes; `_check_tool_definitions` compares `tool_definitions` to live lists | `scripts/agent/services/tool_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/tool_routing_validation.py` | Step 4 | AC-4 | drift match passes; drift/ownership mismatch fatal | Confirmed by repository evidence |
| `REQ-005` | Required Changes; required-server check uses `tool_names` | `scripts/shared/mcp_config.py`, `config/tool_catalog.toml`, `scripts/agent/services/mcp_tool_discovery.py` | Steps 2, 3, 5 | AC-3 | missing required capability fatal at startup | Confirmed by repository evidence |
| `REQ-006` | Implementation Intent; static-vs-live ownership mismatch fatal | `config/tool_catalog.toml`, `scripts/agent/services/tool_validation.py` | Step 4 | AC-4 | ownership mismatch fatal | Confirmed by repository evidence |
| `REQ-007` | Background; warning names non-existent `tools_definitions.toml` | `scripts/agent/services/tool_validation.py` | Step 4 | — | warning no longer names `tools_definitions.toml` | Confirmed by repository evidence |
| `REQ-008` | Constraints; Current-Specification-Only | `config/agent.toml` | Step 1 | AC-1 | reintroduced key rejected with specific message | Derived from confirmed evidence |
| `REQ-009` | Required Changes; move test fixtures off TOML | `tests/agent/test_config_builders.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/test_llm_turn_runner.py`, `tests/agent/test_tool_preparation.py` | Step 6 | AC-1, AC-3 | affected tests pass after migration | Needs confirmation |
| `REQ-010` | AI Implementation Instruction; confirm double fetch | `scripts/agent/services/mcp_tool_discovery.py` | Step 7 | AC-5 | one `/v1/tools` per server | Confirmed by repository evidence |
| `REQ-011` | Documentation Impact | `docs/22_mcp/*` (reference only) | Step 8 | — | docs corrected | Needs confirmation |
