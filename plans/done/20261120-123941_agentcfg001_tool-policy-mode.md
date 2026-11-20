## Goal
- Define one closed tool-exposure policy (`tool_policy_mode` + `disabled_tools`) so that the meaning of `allowed_tools` is identical across the config comment, the startup validator, preflight, the `RuntimeToolRegistry` policy step, and `/reload`. An empty `allowed_tools` gets one stable meaning per mode instead of the current comment/runtime disagreement.

## Priority
High

## Scope
- **In-Scope**:
  - Add `tool_policy_mode` (`discovered` | `explicit_allowlist`) and `disabled_tools` to `ToolConfig`; read both from raw config in the section builder.
  - Reject an unknown mode, a `disabled_tools` name that is not a known tool, and a mode/list mismatch at startup and at `/reload` with the same result.
  - In `discovered` mode keep the registry base visibility and apply only the denylist; reject a non-empty `allowed_tools`.
  - In `explicit_allowlist` mode require a non-empty `allowed_tools`; an empty list is a fatal startup/reload error.
  - Make `tool_policy.check_preflight()` and `RuntimeToolRegistry.apply_policy()` mode-aware with identical semantics; reload re-applies the mode atomically via the two-phase apply.
  - Wire the new validators onto the field registry and route the new fields through the validated reload path so startup and reload give the same result.
  - Correct the "Empty = all tools allowed" comment; update the `allowed_tools` display in `cmd_config_display`.
  - Regenerate `registry/manifests/config_ownership.yaml`; add `tool_policy_mode` to `config/agent.toml`.
  - Contract tests for both modes, empty/unknown mode, unknown tool name, and visibility preserved after reload.
- **Out-of-Scope**:
  - Removing tool definitions and per-server tool name lists (`issues/20261120-114210_agentcfg002_tool-catalog-registry.md`).
  - Safety, approval, preview, and resource metadata (`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`).
  - Config-ownership split and system-prompt snapshot that prune the fields this issue makes typed (`issues/20261120-114212_agentcfg004_config-ownership-split.md`, `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`).
  - Any ADR decision/invariant text change; no ADR names `allowed_tools` (verified in Step 2).

- **Dependencies**: The reduction backlog sequence. See the `Depends on` bullets below for hard ordering dependencies; the rest are naming/sequencing notes by id.
  - **Depends on**: `issues/20261119-145303_cliplc005_staged-reload-transaction.md` | phase all | touches the same field registry, validators, and Memory reload validation; either order works but the second to land re-verifies its tests (`tests/agent/services/test_config_reload.py`)
  - **Depends on**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md` | phase all | removes the tool lists this issue's `explicit_allowlist` mode depends on; the second to land re-verifies its tests

## Background
Filed from the consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 1). The backlog decomposes into a sequence: this issue fixes the exposure contract first, then `agentcfg002` removes the tool lists, `agentcfg003` removes safety/approval metadata, `agentcfg004` splits config ownership, `agentcfg005` prunes the system-prompt snapshot, and `agentcfg006` verifies the integration end to end. The archived Plan `plans/done/20261119-094759_adrchk004_hot-reload-validation.md` already hardened `/reload` validation for `allowed_root`, `tool_safety_tiers`, `allowed_tools`, and `approval_risk_rules` and documents the two-phase apply that guarantees a rejected reload keeps the previous value; this Plan reuses that same reload machinery for the new fields.

## Problem
The documented, validated, and runtime meanings of an empty `allowed_tools` disagree. The dataclass comment at `scripts/agent/config_dataclasses.py:216` says "Empty = all tools allowed"; `scripts/agent/production_config_validator.py:279-281` rejects `allowed_tools=[]` as "every tool is denied"; `scripts/agent/tool_policy.py:558` denies any tool not in `cfg.tool.allowed_tools`; `scripts/shared/runtime_tool_registry.py:209-235` applies `allowed_tools` as an allowlist where an empty sequence enables no tool. The comment, the startup validator, `check_preflight`, and `apply_policy` therefore cannot all be satisfied by one configuration, and removing the long tool lists from `config/agent.toml` without fixing this contract would leave every tool unusable or change visibility only after a reload.

## Reason for Change
Correctness of tool visibility. It is the first step of the `agent.toml` reduction: the later issues remove tool lists and metadata maps and need one stable exposure contract to mean something. Nothing else makes it time-sensitive.

## Implementation Intent
Introduce one closed exposure policy — a new `tool_policy_mode` enum (`discovered` |
`explicit_allowlist`) plus a `disabled_tools` denylist — and give `allowed_tools` exactly
one meaning per mode. `discovered` ignores `allowed_tools` and exposes the registry base
visibility minus `disabled_tools`; `explicit_allowlist` requires a non-empty `allowed_tools`
and exposes only those names (empty is a fatal startup/reload error). Make
`tool_policy.check_preflight` and `RuntimeToolRegistry.apply_policy` share identical
mode-aware semantics, wire the new fields through the field registry so startup and `/reload`
validate identically, correct the stale dataclass comment, and cover both modes with contract
tests. No ADR text changes; no migration alias for the old `allowed_tools` meaning.

## Requirements
- `REQ-001`: Add a `tool_policy_mode` field to `ToolConfig` accepting exactly `discovered` or `explicit_allowlist`; read it from raw config in `config_section_builders._build_tool_config`.
- `REQ-002`: Add a `disabled_tools` field to `ToolConfig` (list of tool-name strings); read it from raw config in `config_section_builders._build_tool_config`.
- `REQ-003`: At startup and at `/reload`, reject an unknown `tool_policy_mode`, reject a `disabled_tools` entry whose name is not a registered tool, and enforce mode/list compatibility (`discovered` rejects a non-empty `allowed_tools`; `explicit_allowlist` rejects an empty `allowed_tools`).
- `REQ-004`: `tool_policy.check_preflight` becomes mode-aware: `discovered` keeps the registry base visibility and applies only `disabled_tools`; `explicit_allowlist` allows only `allowed_tools` names (empty = fail closed). Its semantics must match `RuntimeToolRegistry.apply_policy`.
- `REQ-005`: `RuntimeToolRegistry.apply_policy` becomes mode-aware with the same semantics as `REQ-004`; reload re-applies the mode atomically via the existing two-phase apply so a rejected reload keeps the previous value.
- `REQ-006`: Wire `validate_tool_policy_mode` and `validate_disabled_tools` onto the field registry and route the new fields through the validated reload path so startup and reload produce the same result.
- `REQ-007`: Correct the `allowed_tools` dataclass comment at `config_dataclasses.py:216`; update the `allowed_tools` display in `cmd_config_display` to reflect the resolved mode.
- `REQ-008`: Regenerate `registry/manifests/config_ownership.yaml`; add a `tool_policy_mode` entry to `config/agent.toml`.
- `REQ-009`: Contract tests for both modes, empty/unknown mode, an unknown `disabled_tools` name, and visibility preserved after `/reload`.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Add `tool_policy_mode: str` and `disabled_tools: list[str]` fields to `ToolConfig`; correct the `allowed_tools` comment at line 216 | Holds the disputed field; new fields become typed | REQ-001, REQ-002, REQ-007 | `ToolConfig` at line 163; `allowed_tools` comment at line 216 | `tests/agent/test_startup_validation.py` | Needs confirmation |
| `scripts/agent/config_section_builders.py` | Read `tool_policy_mode` and `disabled_tools` from raw config in `_build_tool_config` | Populates the new typed fields | REQ-001, REQ-002 | `_build_tool_config` at line 185; `allowed_tools` read at line 224 | `tests/agent/services/test_config_reload.py` | Needs confirmation |
| `scripts/agent/services/config_validators.py` | Add `validate_tool_policy_mode` (enum membership) and `validate_disabled_tools` (names are registered tools) | Startup/reload type + contract validation | REQ-003, REQ-006 | `validate_allowed_tools` at line 144 | `tests/agent/test_startup_validation.py` | Needs confirmation |
| `scripts/agent/services/config_field_registry.py` | Register the two new validators on `CONFIG_FIELD_REGISTRY` | Routes new fields through validated reload path | REQ-006 | registry entry for `allowed_tools` at line 83 | `tests/agent/services/test_config_reload.py` | Needs confirmation |
| `scripts/agent/tool_policy.py` | Make `check_preflight` mode-aware (discovered: base visibility minus denylist; explicit_allowlist: allowlist, empty = fail closed) | Runtime preflight gate | REQ-004 | `check_preflight` at line 547; `allowed_tools` check at line 558 | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_approval_preflight.py` | Needs confirmation |
| `scripts/shared/runtime_tool_registry.py` | Make `apply_policy` mode-aware and denylist-aware with semantics identical to `check_preflight`; add mode/denylist inputs | Single runtime authority for tool visibility | REQ-005 | `apply_policy` at line 206; empty-sequence fail-closed at line 214-216 | `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py` | Needs confirmation |
| `scripts/agent/services/config_service_sync.py` | Pass the resolved `tool_policy_mode` and `disabled_tools` into `apply_policy` | Reload propagation of the new policy inputs | REQ-005 | `apply_policy(...)` call at line 76 | `tests/agent/services/test_config_reload.py` | Needs confirmation |
| `scripts/agent/production_config_validator.py` | Remove the blanket `allowed_tools=[]` rejection (now owned by the mode-aware typed validators; empty is valid in `discovered` mode) | Eliminates the startup contradiction with `discovered` mode | REQ-003 | `allowed_tools=[]` rejection at lines 279-282 | `tests/agent/test_production_config_validator.py` | Needs confirmation |
| `scripts/agent/commands/cmd_config_display.py` | Update the `allowed_tools` display to reflect the resolved mode instead of the unconditional "(none: all tools denied)" | User-facing visibility display | REQ-007 | display at lines 120-124 | `tests/agent/commands/test_cmd_config_char.py` | Needs confirmation |
| `registry/manifests/config_ownership.yaml` | Regenerate via `tools/generate_reference_table.py --manifests` | Keeps the ownership reference current | REQ-008 | `tools/generate_reference_table.py --manifests` writes `registry/manifests/config_ownership.yaml` | N/A | Needs confirmation |
| `config/agent.toml` | Add a `tool_policy_mode` entry to the `[tool]` section | Ships one explicit mode with the production config | REQ-008 | long `allowed_tools` list at lines 150-214; no existing mode key | `tests/agent/test_startup_validation.py` | Needs confirmation |
| `tests/agent/test_tool_policy.py` | Add mode-aware `check_preflight` cases; preserve existing coverage | Verifies REQ-004 | `check_preflight` at `scripts/agent/tool_policy.py:547` | `tests/agent/test_tool_policy.py` | Needs confirmation |
| `tests/agent/test_tool_policy_comprehensive.py` | Extend coverage for both modes and the denylist | Verifies REQ-004 | `_cfg(n)` helper exercises preflight | `tests/agent/test_tool_policy_comprehensive.py` | Needs confirmation |
| `tests/shared/test_tool_routing_validation.py` | Update `apply_policy` calls for the new signature and add mode/denylist cases | Verifies REQ-005 | `apply_policy` at `scripts/shared/runtime_tool_registry.py:206` | `tests/shared/test_tool_routing_validation.py` | Needs confirmation |
| `tests/shared/test_runtime_tool_registry.py` | Update `apply_policy` calls for the new signature; add mode cases | Verifies REQ-005 | `apply_policy(tier_map={}, ...)` call | `tests/shared/test_runtime_tool_registry.py` | Needs confirmation |
| `tests/agent/services/test_config_reload.py` | Add reload contract tests for both modes, empty/unknown mode, and visibility preserved after `/reload` | Verifies REQ-005, REQ-006 | existing `REQ-002` reload test; `apply_policy` re-applied via `_sync_services` | `tests/agent/services/test_config_reload.py` | Needs confirmation |
| `tests/agent/test_production_config_validator.py` | Remove/adjust the assertion that `allowed_tools=[]` is rejected unconditionally | Verifies REQ-003 | production validator visibility check | `tests/agent/test_production_config_validator.py` | Needs confirmation |
| `tests/agent/commands/test_cmd_config_char.py` | Update the expected `allowed_tools` display string | Verifies REQ-007 | asserts `(none: n)` display | `tests/agent/commands/test_cmd_config_char.py` | Needs confirmation |
| `tests/agent/_config_test_defaults.py` | Reconcile the comment documenting the old empty-list rejection | Keeps test documentation current | comment at lines 86-89 | `tests/agent/_config_test_defaults.py` | Needs confirmation |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | Replace the absolute empty-list denial statement with the mode-aware contract | Verifies REQ-003, REQ-007 | tool whitelist row (L33, L66) | `docs/00_index.md` Domain specs / Agent | Needs confirmation |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Add mode context to the `allowed_tools` whitelist rule | Verifies REQ-003 | whitelist rule (L33) | `docs/00_index.md` Agent | Needs confirmation |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Describe `allowed_tools` semantics per mode instead of an unconditional denial | Verifies REQ-003, REQ-007 | config reference (L34, L87) | `docs/00_index.md` Agent | Needs confirmation |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Reflect that empty `allowed_tools` is valid in `discovered` mode | Verifies REQ-003 | observation note (L131) | `docs/00_index.md` Agent | Needs confirmation |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Correct the fail-closed row to be mode-aware | Verifies REQ-003 | trust-boundary table (L157) | `docs/00_index.md` MCP security model | Needs confirmation |
| `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` | Fix the checklist gate that now permits empty `allowed_tools` in `discovered` mode | Verifies REQ-003 | fail-open checklist (L20) | `docs/00_index.md` MCP | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/config_reload.py` | Owns the two-phase reload transaction that the reload tests assert against; must be understood before touching reload behavior | REQ-005, REQ-006 → `scripts/agent/services/config_service_sync.py` |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Defines the registry as the single runtime tool authority; constrains where visibility logic may live | REQ-005 → `scripts/shared/runtime_tool_registry.py` |
| `scripts/shared/runtime_tool.py` | Defines `AgentSafetyTier`, consumed by `apply_policy`'s `tier_map` argument | REQ-005 → `scripts/shared/runtime_tool_registry.py` |
| `plans/done/20261119-094759_adrchk004_hot-reload-validation.md` | Documents the two-phase apply that guarantees a rejected reload keeps the previous value; the reused reload design | REQ-006 |
| `scripts/agent/context.py` | Shows how `ctx.cfg.tool` is threaded to `ServiceSyncer`/`apply_policy` | REQ-005 → `scripts/agent/services/config_service_sync.py` |

## Acceptance Criteria
- **AC-01** (REQ-001, REQ-002): `ToolConfig` exposes `tool_policy_mode` and `disabled_tools`; both are populated from raw config by `_build_tool_config`.
- **AC-02** (REQ-003): Startup rejects an unknown `tool_policy_mode`, a `disabled_tools` name that is not a registered tool, a non-empty `allowed_tools` in `discovered` mode, and an empty `allowed_tools` in `explicit_allowlist` mode; startup and `/reload` reject identically.
- **AC-03** (REQ-004): In `discovered` mode `check_preflight` allows every registered tool except those in `disabled_tools`; in `explicit_allowlist` mode it allows only `allowed_tools` names and fails closed on an empty list.
- **AC-04** (REQ-005): `RuntimeToolRegistry.apply_policy` exposes the same semantics as `check_preflight`; after `/reload` the resolved visibility equals the freshly-started visibility.
- **AC-05** (REQ-006): The two new validators are on `CONFIG_FIELD_REGISTRY` and run on the validated reload path.
- **AC-06** (REQ-007): The `allowed_tools` dataclass comment no longer claims "Empty = all tools allowed"; the display reflects the resolved mode.
- **AC-07** (REQ-008): `config_ownership.yaml` is regenerated; `config/agent.toml` carries an explicit `tool_policy_mode`.
- **AC-08** (REQ-009): Contract tests pass for both modes, empty/unknown mode, an unknown `disabled_tools` name, and visibility preserved after reload.

## Tests
- **T-01** (REQ-003, AC-02): `test_startup_validation.py` — unknown mode, unknown `disabled_tools` name, and mode/list mismatches are rejected at startup; mirrored in `test_production_config_validator.py` (empty no longer rejected unconditionally).
- **T-02** (REQ-004, AC-03): `test_tool_policy.py` / `test_tool_policy_comprehensive.py` — `check_preflight` allows/denies per mode and denylist.
- **T-03** (REQ-005, AC-04): `test_runtime_tool_registry.py` / `test_tool_routing_validation.py` — `apply_policy` enforces mode + denylist; `test_config_reload.py` — visibility identical after `/reload`.
- **T-04** (REQ-007, AC-06): `test_cmd_config_char.py` — display reflects the resolved mode.
- **T-05** (REQ-009, AC-08): a dedicated mode contract test covering both modes, empty/unknown mode, unknown denylist name, and reload preservation.

## Documentation Impact
Yes. Several `docs/*.md` files state, as an absolute, the exact behavior this Plan
changes — that an empty `allowed_tools` denies every tool at runtime and that
`ProductionConfigValidator` rejects `allowed_tools=[]` at load. Under the new
mode-aware contract an empty list is valid in `discovered` mode, so those statements
become false. Update the following (named via `docs/00_index.md` "Document References
by Task"), each driven by `REQ-003`/`REQ-007`:

- `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` — tool whitelist row (lines 33, 66).
- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` — `allowed_tools` whitelist rule (line 33).
- `docs/23_agent/agent_08_03_configuration-tools-memory.md` — config reference for `allowed_tools` (lines 34, 87).
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` — config observation note (line 131).
- `docs/91_security/security_01_architecture-and-trust-boundaries.md` — trust-boundary fail-closed table (line 157).
- `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` — pre-production checklist gate (line 20).

`docs/23_agent/agent_14_reference-api-subpackages-generated.md` line 108 documents
`validate_allowed_tools` ("an empty list is valid"); it is a generated reference and is
already consistent with keeping that validator type-only — review only, no edit.
`docs/40_shared/shared_01_overview.md` line 142 only states that `allowed_tools` is
validated (not an absolute empty-list claim) — no change required. After editing the
docs above, run the doc checker(s) listed in `routing.md` Docs → task mapping.

## Assumptions
- `tool_policy_mode` defaults to `explicit_allowlist` when the key is absent. This mirrors the current runtime (a non-empty allowlist is enforced; an empty list never actually meant "all allowed" at runtime and already failed production validation), so no currently-working config changes behavior, and an empty list now fails with a clear "set tool_policy_mode = discovered" error instead of the previous ambiguous rejection.
- `disabled_tools` applies in both modes as a hard denylist; `allowed_tools` gates visibility only in `explicit_allowlist`.
- "Known tool" for `disabled_tools` validation means a name registered in `RuntimeToolRegistry` (`get_all_tool_names()`), the single runtime authority per ADR-002.
- `apply_policy` gains `tool_policy_mode` and `disabled_tools` inputs (a signature change); `check_preflight` reads all three from `cfg.tool` and needs no signature change.
- The two-phase reload transaction in `config_reload.py` already propagates the validated candidate config to `ServiceSyncer.sync_all`, so registering the new validators is sufficient for reload parity.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which existing tests assert the old unconditional `allowed_tools=[]` rejection and must therefore change beyond the ones already listed | Enumerate all assertions of the "every tool is denied"/production-validator-rejects-empty behavior across the suite | Implementation discovery pass against `test_production_config_validator.py` and any snapshot/characterization tests before freezing the test-file scope | False |
| UNK-02 | Whether `discovered` mode should also consult `plan_blocked_tools`/tiers for path-bearing tools, or expose them verbatim from the registry base visibility | Current `apply_policy` base-visibility definition vs. plan-mode blocking | Confirm against `config_reload.py`/`tool_policy.py` tier handling during implementation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/runtime_tool_registry.py` | `apply_policy` mode/denylist-aware (signature change) | High — every reload and direct caller; ADR-002 single authority | ~10 commits | Low — few owners, many readers | None |
| `scripts/agent/tool_policy.py` | `check_preflight` mode-aware | High — runtime preflight gate on every tool call | ~15 commits | Low | None |
| `scripts/agent/production_config_validator.py` | Remove blanket `allowed_tools=[]` rejection | Medium — startup validation path | ~13 commits | Low | None |
| `scripts/agent/services/config_service_sync.py` | Pass new `apply_policy` inputs | Medium — reload propagation | ~3 commits | Low | None |
| `scripts/agent/config_dataclasses.py` | Add `tool_policy_mode`/`disabled_tools` fields | Low — new typed fields | Low | Low | None |
| `config/agent.toml` | Add `tool_policy_mode` entry | Low — one config key | Low | Low | Syncs via deploy; re-run startup validation after deploy |

## Design
- **Closed enum `tool_policy_mode`** with exactly two members: `discovered` and `explicit_allowlist`. Membership is validated at startup and `/reload` by a new `validate_tool_policy_mode`; an unknown value is a fatal validation error (fail closed).
- **Semantics contract (single source of truth):**
  - `discovered`: visibility = registry base visibility minus `disabled_tools`; `allowed_tools` is ignored, and a non-empty `allowed_tools` is rejected (the field is unused here).
  - `explicit_allowlist`: visibility = the `allowed_tools` names; an empty list is a fatal startup/reload error. `disabled_tools` still applies as an additional hard denylist.
  - `disabled_tools` applies in both modes. "Known tool" for validation = a name registered in `RuntimeToolRegistry` (ADR-002 single authority).
- **Default mode = `explicit_allowlist`** when the key is absent. This mirrors the current runtime (a non-empty allowlist is enforced; an empty list never meant "all allowed" at runtime and already failed production validation), so no working config changes behavior and an empty list now fails with a clear "set `tool_policy_mode = discovered`" message instead of the previous ambiguous rejection.
- **Shared semantics:** `check_preflight` (`tool_policy.py`) and `apply_policy` (`runtime_tool_registry.py`) must produce identical results. Prefer one shared helper computing the resolved allowed set from `(mode, allowed_tools, disabled_tools, base_visibility)` so the two call sites cannot drift. `check_preflight` reads all three from `cfg.tool`; `apply_policy` gains `tool_policy_mode` and `disabled_tools` inputs (a signature change) and is fed by `config_service_sync.sync_all`.
- **Validation ownership:** the new field-registry validators (`validate_tool_policy_mode`, `validate_disabled_tools`, plus tightening `validate_allowed_tools` for mode/list compatibility) own the contract; the production validator's blanket `allowed_tools=[]` rejection is removed because it contradicts `discovered` mode. Registering the new validators on `CONFIG_FIELD_REGISTRY` routes them through the existing two-phase reload transaction in `config_reload.py`, giving startup/reload parity automatically.
- **No ADR text changes** (no ADR names `allowed_tools`), and **no migration window/alias/shim** for the old `allowed_tools` meaning — the contract is defined once, going forward.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Typed fields and validators**
   - [ ] Add `tool_policy_mode: str` and `disabled_tools: list[str]` to `ToolConfig` in `scripts/agent/config_dataclasses.py`; correct the `allowed_tools` comment (REQ-001, REQ-002, REQ-007).
   - [ ] Read both from raw config in `config_section_builders._build_tool_config` (REQ-001, REQ-002).
   - [ ] Add `validate_tool_policy_mode` (enum) and `validate_disabled_tools` (names are registered tools) to `config_validators.py`; tighten `validate_allowed_tools` for mode/list compatibility (REQ-003).
   - [ ] Register the two new validators on `CONFIG_FIELD_REGISTRY` in `config_field_registry.py` (REQ-006).
2. **Phase 2: Mode-aware runtime policy**
   - [ ] Implement one shared helper that resolves the allowed set from `(mode, allowed_tools, disabled_tools, base_visibility)` (REQ-004, REQ-005).
   - [ ] Make `check_preflight` in `tool_policy.py` use the helper; no signature change (REQ-004).
   - [ ] Make `apply_policy` in `runtime_tool_registry.py` mode/denylist-aware; add `tool_policy_mode` and `disabled_tools` inputs (REQ-005).
   - [ ] Update `config_service_sync.sync_all` to pass the new `apply_policy` inputs from `ctx.cfg.tool` (REQ-005).
   - [ ] Remove the blanket `allowed_tools=[]` rejection from `production_config_validator.py` (REQ-003).
3. **Phase 3: Config and manifest**
   - [ ] Add a `tool_policy_mode` entry to `config/agent.toml` (REQ-008).
   - [ ] Regenerate `registry/manifests/config_ownership.yaml` via `tools/generate_reference_table.py --manifests` (REQ-008).
4. **Phase 4: Documentation**
   - [ ] Update the six `docs/*.md` listed under Documentation Impact to the mode-aware contract (REQ-003, REQ-007); review `agent_14` (already consistent) and skip `shared_01` (no absolute claim).
5. **Phase 5: Tests**
   - [ ] Update `apply_policy` callers/tests for the new signature (`test_runtime_tool_registry.py`, `test_tool_routing_validation.py`) and `sync_all` expectations (`test_config_reload.py`) (REQ-005).
   - [ ] Adjust `test_production_config_validator.py` for the removed blanket rejection (REQ-003).
   - [ ] Update the display assertion in `test_cmd_config_char.py` (REQ-007).
   - [ ] Add mode-aware `check_preflight` cases (`test_tool_policy.py`, `test_tool_policy_comprehensive.py`) (REQ-004).
   - [ ] Add a dedicated contract test for both modes, empty/unknown mode, unknown `disabled_tools` name, and visibility preserved after `/reload` (REQ-009).
6. **Phase 6: Validation**
   - [ ] Run lint, type-check, and the full test suite; confirm no regressions (AC-08).
   - [ ] Run the doc checker(s) for the edited docs per `routing.md` Docs → task mapping.

### Release units
**Unit**: `apply_policy` signature change | **Phases**: 2 | **Reason**: adding `tool_policy_mode`/`disabled_tools` inputs to `apply_policy` invalidates every caller (`config_service_sync.sync_all`) and its direct-call tests until they are updated in the same commit; they cannot be validated alone

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `runtime_tool_registry.apply_policy` | Unit: both modes, empty/unknown mode, denylist, base visibility preserved | `uv run pytest tests/shared/test_runtime_tool_registry.py tests/shared/test_tool_routing_validation.py` | passes |
| `tool_policy.check_preflight` | Unit: allow/deny per mode and denylist | `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_preflight.py` | passes |
| Reload parity | Integration: visibility identical after `/reload` for each mode | `uv run pytest tests/agent/services/test_config_reload.py` | passes |
| Startup/reload validation | Unit: unknown mode, unknown denylist name, mode/list mismatch rejected identically at startup and reload | `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_production_config_validator.py` | passes |
| Typed fields + section builder | Unit: `tool_policy_mode`/`disabled_tools` populated from raw config | `uv run pytest tests/agent/test_startup_validation.py` | passes |
| Display | Unit: resolved-mode display | `uv run pytest tests/agent/commands/test_cmd_config_char.py` | passes |
| Manifest | Deterministic regeneration | `uv run python tools/generate_reference_table.py --manifests` then `git diff --stat` | only `config_ownership.yaml` changes |
| Full suite | Regression | `uv run pytest` | green |
| Docs | Doc checker per `routing.md` | (checker named in routing.md Docs mapping) | passes |

## Risks
- **Risk**: The `apply_policy` signature change breaks every caller and its direct-call tests until updated together, potentially failing the build mid-sequence. → **Mitigation**: declare it a release unit and land `runtime_tool_registry.py` + `config_service_sync.py` + the affected tests in one commit; the shared helper keeps `check_preflight` and `apply_policy` from drifting.
- **Risk**: Widely-referenced field — `allowed_tools` appears across many tests and three docs; an incomplete sweep leaves stale assertions or misleading docs. → **Mitigation**: the Unknowns discovery pass enumerates all empty-list assertions before freezing scope; the Documentation Impact section names every doc that states the old absolute behavior.
- **Risk**: Changing the default or semantics could silently alter tool visibility for existing configs. → **Mitigation**: default to `explicit_allowlist` (mirrors current runtime), and the production validator already rejected empty lists today, so no working config's behavior changes; only the ambiguous empty-list case gains a clear, intentional error.
- **Risk**: `disabled_tools` "known tool" definition depends on the registry, which `agentcfg002` will reshape. → **Mitigation**: validate against the current `RuntimeToolRegistry.get_all_tool_names()` (ADR-002 authority); re-verify when `agentcfg002` lands.
- **Risk**: Documentation drift across six `docs/*.md`. → **Mitigation**: update all six in Phase 4 and run the doc checker per `routing.md` before freeze.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Typed fields and validators | In Progress | — | — |  |
| 2 | Mode-aware runtime policy (release unit) | In Progress | — | — | `apply_policy` signature change lands with its callers/tests |
| 3 | Config and manifest | In Progress | — | — |  |
| 4 | Documentation | In Progress | — | — | six `docs/*.md` |
| 5 | Tests | In Progress | — | — |  |
| 6 | Validation | Pending | — | — | full suite + doc checker |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261120-132256_01_scripts_agent_config_dataclasses.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261120-132256_02_scripts_agent_config_section_builders.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261120-132256_03_scripts_agent_services_config_validators.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261120-132256_04_scripts_agent_services_config_field_registry.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261120-132256_05_scripts_agent_tool_policy.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-132256_06_scripts_shared_runtime_tool_registry.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-132256_07_scripts_agent_services_config_service_sync.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-132256_08_scripts_agent_production_config_validator.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-132256_09_scripts_agent_commands_cmd_config_display.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-132256_10_registry_manifests_config_ownership.yaml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-132256_11_config_agent.toml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-132256_16_tests_agent_services_test_config_reload.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261120-132256_19_tests_agent__config_test_defaults.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261120-132256_20_docs_23_agent_agent_06_03_tool-execution-and-approval-concurrency-safety.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261120-132256_21_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261120-132256_22_docs_23_agent_agent_08_03_configuration-tools-memory.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261120-132256_23_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261120-132256_24_docs_91_security_security_01_architecture-and-trust-boundaries.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261120-132256_25_docs_22_mcp_mcp_06_13_pre-production-fail-open-checklist.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-123941
- **Related target files**: `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/tool_policy.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/agent/services/config_service_sync.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/commands/cmd_config_display.py`, `registry/manifests/config_ownership.yaml`, `config/agent.toml`, plus the test and doc rows below.

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | New `tool_policy_mode` field; read from raw config | `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py` | Phase 1 | AC-01 | section-builder/startup test | Open |
| REQ-002 | New `disabled_tools` field; read from raw config | `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py` | Phase 1 | AC-01 | section-builder/startup test | Open |
| REQ-003 | Reject unknown mode / unknown denylist name / mode/list mismatch at startup and reload | `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/production_config_validator.py` | Phase 1–2 | AC-02 | startup + production-validator tests | Open |
| REQ-004 | `check_preflight` mode-aware, identical to `apply_policy` | `scripts/agent/tool_policy.py` | Phase 2 | AC-03 | `check_preflight` unit tests | Open |
| REQ-005 | `apply_policy` mode/denylist-aware; reload re-applies atomically | `scripts/shared/runtime_tool_registry.py`, `scripts/agent/services/config_service_sync.py` | Phase 2 | AC-04 | registry + reload tests | Open |
| REQ-006 | New validators on the field registry, validated reload path | `scripts/agent/services/config_field_registry.py` | Phase 1 | AC-05 | reload validation test | Open |
| REQ-007 | Correct dataclass comment; update display | `scripts/agent/config_dataclasses.py`, `scripts/agent/commands/cmd_config_display.py` | Phase 1–2 | AC-06 | display test | Open |
| REQ-008 | Regenerate ownership manifest; add mode to agent.toml | `registry/manifests/config_ownership.yaml`, `config/agent.toml` | Phase 3 | AC-07 | deterministic regen + startup test | Open |
| REQ-009 | Contract tests for both modes, empty/unknown mode, unknown denylist name, reload preservation | tests | Phase 5 | AC-08 | dedicated contract test; full suite | Open |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-132256 -->