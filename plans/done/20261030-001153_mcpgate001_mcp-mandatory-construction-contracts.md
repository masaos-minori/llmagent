# Plan: MCP Posture Gating and Component Mandatoriness Construction Contracts

**Plan ID:** 20261030-001153-mcpgate001
**Source Issue:** `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` (SHA256: 99e69956602488b81209288ba8833d11ba99ec454f9f46da9246f2f177cb2459)
**Task Classification:** Path B (medium; contract data addition + constructor change with 45-test migration)
**Status:** Draft

## Goal
Finish making the MCP execution path fail-closed by construction: `RuntimeToolRegistry`
must not accept a missing posture allowlist, and component mandatoriness must come from
one machine-readable registry that `config/agent.toml` `required` values are validated
against at startup.

## Priority
Medium (P2). The issue lowers the memo's High rating: the production path already passes
a posture allowlist, Safety/Integrity failures are fatal regardless of config, and the
health registry is already mandatory (`mcpexec004`, archived). Remaining risk is latent
configuration drift. Not time-sensitive.

## Scope
**In-Scope**:
- `RuntimeToolRegistry`: `allowed_servers` becomes a required constructor input;
  remove `None`-means-allow-all; explicit empty set = deny all.
- New machine-readable component-mandatoriness registry (`registry/` file) with the
  fields the issue enumerates, as a derived encoding of the approved classification in
  `agent_08_04`, plus a loader and startup cross-validation.
- Startup validation: `required` values validated against the registry; unknown or
  conflicting classifications are fatal.
- Diagnostics and operator reference generated from the registry
  (`tools/generate_reference_table.py` guard-block pattern).
- Migration of the 45 measured `RuntimeToolRegistry(` test constructions (12 files).
- ADR-004 and MCP operator documentation updates.

**Out-of-Scope**:
- Health-registry mandatoriness (done: `issues/done/20261027-155847_mcpexec004_*`),
  dynamic tool-health hints (`toolhint001`).
- Changing which components are classified mandatory (the registry records, not re-decides).
- Startup publication ordering machinery — the current flow already orders posture
  before publication (verified; test-only confirmation).
- Which component classifications change (none; all 10 servers stay `required`).

**Dependencies**:
- adrauth001 plan (`plans/20261029-214650_adrauth001_adr-authority-model.md`): the
  registry's authority ADR and placement among generated contracts depend on the ADR
  authority model (issue Dependencies section).
- Blocks adrcov001's component-mandatoriness manifest.
- Related: toolexec001 consumes posture and tool-definition generation identifiers.

## Background
### Codebase Context (directly verified 2026-10-30, HEAD `c5a8285dd` + staged plans)
- `scripts/shared/runtime_tool_registry.py`: `allowed_servers: frozenset[str] | None =
  None` in `__init__`; docstring: `None` "means no gate was supplied and today's
  behavior is kept"; filter applies only when not `None` (`_posture_excluded` path
  verified around :91-95).
- Production chain (all verified):
  `scripts/agent/services/mcp_health.py:217` `collect_server_postures` →
  `PostureGate` (:95, carries `required` from config) → `allowed_server_keys` (:238,
  fully-green gates only) → `scripts/agent/startup_validation.py:114-120` (posture
  gates collected, then `McpToolDiscoveryService(ctx, posture_gates=...)`, then
  `runtime_tools`/`set_runtime_registry` publication) → `scripts/agent/services/
  mcp_tool_discovery.py:92-104` (`posture_gates` required argument, no default; empty
  mapping is a valid explicit value = no MCP tools) → `:110` `allowed_servers =
  frozenset(allowed_server_keys(...))` → `scripts/agent/services/
  mcp_tool_discovery_registry.py:59-62` (`_build_runtime_tools`, `allowed_servers`
  required) → `:92` the only production `RuntimeToolRegistry(` construction.
- Fatal gate: `mcp_health.py:139-147` `_is_fatal_gate` — `gate.required or
  gate.failure_class in _SAFETY_INTEGRITY_CLASSES`; Safety/Integrity fatal regardless
  of `required`.
- Config: `scripts/shared/mcp_config.py:100` `required: bool = True`, :326 normalized,
  :163-167 rejects `required=false` with `startup_mode=subprocess` (ADR-004 Exceptions).
- No machine-readable mandatoriness data exists under `scripts/` or `config/` (absence
  confirmed). Human-readable authority: `docs/23_agent/agent_08_04_configuration-mcp-
  approval-obs.md` :40-66 "Component Criticality Classification" table — all 10 servers
  (`shell`, `git`, `web_search`, `file_delete`, `file_write`, `file_read`, `github`,
  `cicd`, `rag_pipeline`, `mdq`) classified `required`.
- ADR-004 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`):
  :76/:77 mandatory/non-mandatory criteria; :79 undefined mandatoriness is an error;
  :80 item 13 division of responsibility — approved classification lives in the
  `agent_08_04` table, `config/agent.toml` `required` must match it, and startup
  validation verifies the effective classification; :85 Fail-Fast list already includes
  "Undeterminable component mandatoriness".
- Test blast radius (measured, resolves the issue's third unresolved question): 45
  `RuntimeToolRegistry(` constructions across 12 test files:
  `tests/shared/test_runtime_tool_registry.py` 19, `tests/shared/
  test_tool_routing_validation.py` 6, `tests/shared/test_tool_executor.py` 4,
  `tests/shared/test_tool_executor_routing.py` 3, `tests/agent/services/
  test_runtime_tool_routing_integration.py` 3, `tests/agent/commands/test_cmd_mcp.py` 2,
  `tests/shared/test_rag_tools_consistency.py` 2, `tests/shared/test_route_resolver.py` 2,
  `tests/agent/services/test_config_reload.py` 1, `tests/agent/test_tool_policy.py` 1,
  `tests/agent/test_tool_policy_comprehensive.py` 1, `tests/integration/
  test_production_security_regression.py` 1.
- Publication order already enforced (resolves the issue's first unresolved question):
  posture collection (`startup_validation.py:114`) precedes registry publication
  (`:118-120`) inside the same consolidated step, and `scripts/agent/startup.py:130-147`
  aborts on any fatal pipeline outcome before the session proceeds.

### Corrections to Issue Claims
1. Issue cites "about 20" test constructions; the measured count is 45 across 12 files
   (the issue itself flags this as a `Needs confirmation` to be measured).
2. Issue's `mcp_tool_discovery_registry.py` builder line anchors (:62, :98) verified as
   `_build_runtime_tools` :59-62 and `_dedupe_and_build` :95-98.

### Historical Context
- Builds on archived `mcpexec004` (`health_registry` mandatory: `scripts/shared/
  tool_executor.py:51` required parameter, :82 `TypeError` on `None`; `scripts/agent/
  factory.py:122,130` — re-verified, still current).

## Problem
1. `RuntimeToolRegistry.__init__` offers a fail-open `allowed_servers=None` that no
   production path uses today but a future caller can reach.
2. Mandatoriness is configuration-only (`required` per server) plus a prose table;
   nothing machine-readable records the architecture-approved classification, so a
   config edit can downgrade a mandatory component or leave a new server unclassified
   without any check — contrary to ADR-004 item 13's intent that startup verifies the
   effective classification.

## Reason for Change
The registry `None` default is the last optional gate on the executable-exposure path,
and the mandatoriness authority is the missing half of ADR-004's classification
contract. Risk is latent (configuration drift), not a demonstrated fail-open today.

## Implementation Intent
Make the allowlist a required constructor input; add a machine-readable
component-mandatoriness registry derived from the approved `agent_08_04` classification
(criteria themselves stay solely in ADR-004 — no competing copy); validate config
against it at startup with fatal unknown/conflicting classifications; generate
diagnostics and operator reference from it; reuse `_is_fatal_gate` and posture gates
rather than a parallel mechanism.

## Requirements
- `REQ-001`: `RuntimeToolRegistry.__init__` requires an explicit `allowed_servers:
  frozenset[str]`; `None` raises `TypeError`; empty set registers nothing (deny all).
- `REQ-002`: New `registry/component_mandatoriness.yaml` (PyYAML is already a project
  dependency) with one entry per MCP server: component ID, approved classification,
  failure category, safety role, safely-disableable functions, startup consequence,
  observability requirements, owner, authority ADR (issue Required Changes list).
- `REQ-003`: Loader in `scripts/shared` (leaf-safe: plain data, no Agent DTO imports)
  exposing a frozen classification map and typed errors (`UnknownComponentError`,
  `ClassificationConflictError`).
- `REQ-004`: Startup cross-validation: each configured server's `required` must agree
  with the registry entry; a configured server missing from the registry, or a registry
  entry with no classification, is fatal ("Undeterminable component mandatoriness" —
  ADR-004 :85 already lists it Fail-Fast).
- `REQ-005`: The registry is generated-from / drift-checked against the approved
  classification table in `agent_08_04`; `agent_08_04`'s table becomes an
  AUTO-GENERATED guard block via `tools/generate_reference_table.py` (ADR-015 pattern).
- `REQ-006`: Migration of all 45 test constructions without changing assertions' meaning
  (explicit allowlists computed from the tools under test; `frozenset()` where deny-all
  is the case).
- `REQ-007`: `shared` stays a leaf module (import-linter contract `agent-mcp-config-models`).
- `REQ-008`: Every fatal/disabled decision keeps an observable reason (existing
  `ServiceWarning`/pipeline outcome machinery carries it; do not add new channels).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on
2026-10-30: every row exists-or-is-new-with-evidence, is linked to a Plan requirement,
and is `Verified` against `HEAD c5a8285dd` — 45 `RuntimeToolRegistry(` constructions
measured across 12 test files and the sole production construction at
`scripts/agent/services/mcp_tool_discovery_registry.py:92` re-confirmed by direct scan;
`check_workitem_structure.py` reports no findings; cross-plan pairs reported by
`check_plan_target_overlaps.py` are recorded sequenced in Dependencies.)

| File Path | Change Type | Notes | Priority | Dependencies | Estimated Complexity |
|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | create | initial entries = current approved classification (all 10 required) | P1 | adrauth001 placement reconciliation | Low |
| scripts/shared/component_mandatoriness.py | create | loader, frozen map, typed errors | P1 | registry yaml | Medium |
| scripts/shared/runtime_tool_registry.py | refactor | required `allowed_servers`; drop `None` semantics | P1 | - | Low |
| scripts/agent/production_config_validator.py | refactor | required-vs-registry cross-check, fatal on unknown/conflict | P1 | loader | Medium |
| scripts/agent/startup_validation.py | refactor | wire the cross-check into the pipeline before discovery publication | P1 | production_config_validator | Medium |
| scripts/agent/services/mcp_health.py | refactor | error/remediation text names the registry as the classification source | P1 | - | Low |
| scripts/shared/mcp_config.py | refactor | `required` field docstring points at the registry authority | P2 | loader | Low |
| tools/check_component_mandatoriness.py | create | CI drift checker: registry ↔ agent_08_04 table ↔ config required values | P1 | registry yaml | Medium |
| tools/generate_reference_table.py | refactor | new mandatoriness guard-block generator for the MCP classification table | P2 | registry yaml | Medium |
| tests/shared/test_component_mandatoriness.py | create | loader tests, deny-all/unknown/conflict fixtures | P1 | loader | Medium |
| tests/shared/test_runtime_tool_registry.py | test | migrate 19 constructions; `None`-rejection regression | P1 | REQ-001 | Medium |
| tests/shared/test_tool_routing_validation.py | test | migrate 6 constructions | P1 | REQ-001 | Low |
| tests/shared/test_tool_executor.py | test | migrate 4 constructions | P1 | REQ-001 | Low |
| tests/shared/test_tool_executor_routing.py | test | migrate 3 constructions | P1 | REQ-001 | Low |
| tests/agent/services/test_runtime_tool_routing_integration.py | test | migrate 3 constructions | P1 | REQ-001 | Low |
| tests/agent/commands/test_cmd_mcp.py | test | migrate 2 constructions | P1 | REQ-001 | Low |
| tests/shared/test_rag_tools_consistency.py | test | migrate 2 constructions | P1 | REQ-001 | Low |
| tests/shared/test_route_resolver.py | test | migrate 2 constructions | P1 | REQ-001 | Low |
| tests/agent/services/test_config_reload.py | test | migrate 1 construction | P1 | REQ-001 | Low |
| tests/agent/test_tool_policy.py | test | migrate 1 construction | P1 | REQ-001 | Low |
| tests/agent/test_tool_policy_comprehensive.py | test | migrate 1 construction | P1 | REQ-001 | Low |
| tests/integration/test_production_security_regression.py | test | migrate 1 construction | P1 | REQ-001 | Low |
| tests/agent/test_production_config_validator.py | test | downgrade-rejected and unknown-fatal regressions | P1 | REQ-004 | Medium |
| tests/agent/test_startup_validation.py | test | publication-order regression (posture gate precedes registry publication) | P2 | - | Low |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | docs | state where the machine-readable registry lives; config cannot weaken it | P1 | adrauth001 (ADR-016 classification) | Low |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | docs | classification table becomes generated guard-block from the registry | P1 | generate_reference_table change | Medium |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | docs | `required` field semantics: validated against the registry | P1 | - | Low |
| config/documentation_canonical_sources.toml | config | register the registry as canonical source for mandatoriness claims | P1 | - | Low |
| tools/TOOL_DESCRIPTIONS.md | docs | register `check_component_mandatoriness.py` (routing.md Tools rule) | P1 | checker | Low |

Explicitly excluded from target files:
- `scripts/agent/factory.py`, `scripts/shared/tool_executor.py`,
  `scripts/shared/tool_transport_invoker.py` — already mandatory by `mcpexec004`.
- `scripts/agent/services/mcp_tool_discovery.py`, `mcp_tool_discovery_registry.py` —
  `allowed_servers`/`posture_gates` already required inputs (verified).
- `config/agent.toml` values — no value changes; all 10 servers stay `required = true`.
- `scripts/agent/startup.py` — ordering already correct; test-only confirmation.

## Reference Files
- scripts/agent/services/mcp_health.py — `PostureGate`, `allowed_server_keys`, `_is_fatal_gate`
- scripts/agent/services/mcp_tool_discovery_registry.py — the only production construction
- scripts/agent/startup.py — fatal pipeline abort path
- docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md — routing authority
- docs/10_adr/adr_01_index.md :99-147 — ADR Invariant Verification Matrix (update the ADR-004 rows for the new tests)
- tools/check_db_separation.py — pattern for a live-repo drift checker
- plans/20261029-214650_adrauth001_adr-authority-model.md — authority model coordination
- skills/DESIGN.md — Docs content policy; `shared` leaf contract

## Acceptance Criteria
- AC-1: `RuntimeToolRegistry(..., allowed_servers=None)` raises `TypeError`; an empty
  allowlist registers nothing; no production path interprets a missing allowlist as
  allow-all (grep-enforced: no `allowed_servers=None` remains in `scripts/` or `tests/`).
- AC-2: `registry/component_mandatoriness.yaml` exists, lists exactly the 10 approved
  servers with all issue-enumerated fields, and is validated at startup.
- AC-3: A config that sets `required = false` for a registry-`required` server aborts
  startup with a named fatal outcome; a configured server absent from the registry
  aborts startup (unknown classification).
- AC-4: The `agent_08_04` classification table is produced by the generator guard block
  and `tools/check_component_mandatoriness.py` fails on any registry/table/config drift.
- AC-5: A regression test confirms the runtime registry is never published before the
  posture gate completes (structural order asserted via the startup-validation flow).
- AC-6: All 45 migrated test constructions pass with unchanged assertion meaning;
  `mypy`, `ruff`, `bandit`, and `lint-imports` clean; production behavior unchanged for
  the current all-required configuration.

## Tests
### New
- `tests/shared/test_component_mandatoriness.py` — loader, unknown component,
  conflicting classification, deny-all fixtures.
- Downgrade-rejection and unknown-classification-fatal regressions in
  `tests/agent/test_production_config_validator.py` (fail-before/pass-after).
### Modified
- 12 test files (45 constructions) migrated to explicit allowlists; assertion meaning
  unchanged (issue Testing Expectations).
- `tests/agent/test_startup_validation.py` — publication-order regression.
### Regression
- Existing posture/fatal-gate tests (`tests/agent/test_mcp_health_posture.py`) unchanged.

## Documentation Impact
Yes (issue Documentation Impact). ADR-004 states where the registry lives and that
configuration cannot weaken it; `agent_08_04` table generated from the registry; MCP
operator reference (`docs/22_mcp/mcp_06_02_*`) updated. Intent/boundaries/failure
behavior only, per `skills/DESIGN.md` Docs content policy. `docs/00_index.md` task-scope
mapping applies at implementation time; `check_docs_consistency.py --domain mcp` must pass.

## Assumptions
- A-1: Initial registry content = the currently approved classification (all 10 servers
  required); it records, not re-decides (issue Out of Scope).
- A-2: `agent_08_04` table remains the human-readable approved classification until
  adrauth001's authority model (ADR-016) designates the authoritative store; the YAML
  registry and the table are drift-checked against each other so either can become
  derived without changing startup behavior.
- A-3: YAML format is acceptable (PyYAML `>=6.0` is already a project dependency).

## Unknowns
- U-1: Final home of the authoritative mandatoriness data once adrauth001 lands
  (`config/adr_authority.toml` vs `registry/` vs ADR front matter). Mitigation: loader
  reads one path constant; relocation is a one-file change. Sequencing constraint on the
  ADR-004 doc row.
- U-2: Whether adrcov001's contract manifests consume this registry file directly or a
  per-ADR manifest references it. Coordinate in the adrcov001 plan.

## Affected areas
- scripts/shared (2), scripts/agent (3), scripts/agent/services (1)
- tests: 14 files (12 migrated + 2 extended) + 1 new
- tools: 2 (1 new checker, 1 generator extension) + TOOL_DESCRIPTIONS
- registry/ (new directory), config/documentation_canonical_sources.toml
- docs/10_adr (2), docs/23_agent (1), docs/22_mcp (1)

## Design
### Current Architecture
`config required` → `PostureGate.required` → `_is_fatal_gate` (availability failures
only) and `allowed_server_keys` → registry. Approved classification exists only as a
prose table; nothing validates config against it.

### Target Architecture
Registry file (approved classification, machine-readable) → loader (shared, leaf) →
startup cross-validation against config (fatal on drift) → unchanged posture-gate and
registry-construction machinery (reused, not duplicated) → generated operator reference.
`RuntimeToolRegistry` no longer has a no-gate mode: absence of an allowlist is a
programming error, not a behavior.

### Key Components
1. `scripts/shared/component_mandatoriness.py`: `load_component_mandatoriness(path) ->
   FrozenDict[str, ComponentClassification]`; typed errors.
2. `production_config_validator`: per-server agreement check; unknown/conflict → fatal
   pipeline outcome (reuses existing pipeline FATAL semantics).
3. `tools/check_component_mandatoriness.py`: three-way drift checker (registry ↔
   generated table ↔ config), live-repo test + synthetic-repo negative tests following
   the `check_db_separation.py` pattern.

## Implementation steps
### Phase 1: Registry data + loader (independently testable)
- `registry/component_mandatoriness.yaml`, `scripts/shared/component_mandatoriness.py`,
  `tests/shared/test_component_mandatoriness.py`.
- Done when: loader round-trips the 10 approved entries; typed-error fixtures pass.
### Phase 2: Constructor hardening + test migration (mechanical, incremental)
- `RuntimeToolRegistry` required allowlist; migrate the 12 test files in batches per
  file, running the affected test file after each step (issue AI instruction).
- Done when: full `uv run pytest tests/shared tests/agent` green; grep shows no
  `allowed_servers=None`.
### Phase 3: Startup cross-validation
- Validator wiring + fatal fixtures + publication-order test.
- Done when: AC-3/AC-5 fixtures pass via `tests/agent/test_production_config_validator.py`
  and `tests/agent/test_startup_validation.py`.
### Phase 4: Generation + drift checker + docs
- `generate_reference_table.py` mandatoriness block; `check_component_mandatoriness.py`;
  docs rows; canonical-source registry entry; TOOL_DESCRIPTIONS row.
- Done when: `--check` drift test passes; docs checkers green.

## Validation plan
- Issue-specified: `uv run pytest tests/shared tests/agent`,
  `uv run pytest tests/integration/test_production_security_regression.py`,
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`,
  `uv run python tools/check_docs_consistency.py --domain mcp`.
- Standard gates: `uv run mypy scripts`, `uv run ruff check scripts tests tools`,
  `uv run bandit -r scripts`, `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_tool_descriptions_sync.py`,
  `check_canonical_source_registry.py`, `check_module_size.py` (two shared modules grow).
- CI-equivalent: no CI config deviation; mirror `rules/toolchain.md` sequence.

## Risks
| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| 45-construction migration silently changes test meaning | Medium | Medium | Per-file incremental migration; assertion-diff review per batch |
| Dual source (agent_08_04 table vs registry) drifts before adrauth001 settles authority | Medium | High | Three-way drift checker + canonical-source registry entry (A-2) |
| adrauth001 relocates contract data, invalidating the registry home | Medium | High | U-1: single loader path constant; coordinate before Phase 1 freeze lands in code |
| Constructor change breaks third-party/test-only registry uses not found by rg | Low | Low | Measured 45-construction inventory is rg-complete for `tests/` + `scripts/` |
| Deny-all semantics confused with no-MCP-tools production case | Low | Medium | Explicit `frozenset()` only in tests; production passes computed `allowed_server_keys` |

## Dependencies
- adrauth001 plan (placement/authority reconciliation; ADR-004 doc row sequencing).
- adrcov001 plan consumes this plan's registry (issue: "Blocks the component-mandatoriness
  manifest in adrcov001").
- toolexec001 plan: related (posture/tool-definition generation IDs), no target-file overlap.
- `check_plan_target_overlaps.py` findings at freeze time: recorded in Execution Status.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: registry data + loader | In Progress | — | — | Procedures written (docs 01, 02, 07, 10) |
| 2 | Phase 2: constructor hardening + 45-construction test migration | In Progress | — | — | Procedures written (docs 03, 11-22) |
| 3 | Phase 3: startup cross-validation | In Progress | — | — | Procedures written (docs 04, 05, 06, 23, 24) |
| 4 | Phase 4: generation + drift checker + docs | In Progress | — | — | Procedures written (docs 08, 09, 25-29); checker test row is a recorded target-table gap |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | adrauth001 authority/placement decision (U-1) pending at implementation time; wording designed amendment-safe | No | — |
| 4 | tools/check_component_mandatoriness.py synthetic-test file missing from the frozen target table — additional-target-file discovery to register before implementing row 8 | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-115752_01_registry_component_mandatoriness.yaml.md` | 1 | Procedure | Pending | — | — |
| `20261030-115752_02_scripts_shared_component_mandatoriness.py.md` | 1 | Procedure | Pending | — | — |
| `20261030-115752_03_scripts_shared_runtime_tool_registry.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_04_scripts_agent_production_config_validator.py.md` | 3 | Procedure | Pending | — | — |
| `20261030-115752_05_scripts_agent_startup_validation.py.md` | 3 | Procedure | Pending | — | — |
| `20261030-115752_06_scripts_agent_services_mcp_health.py.md` | 3 | Procedure | Pending | — | — |
| `20261030-115752_07_scripts_shared_mcp_config.py.md` | 1 | Procedure | Pending | — | — |
| `20261030-115752_08_tools_check_component_mandatoriness.py.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_09_tools_generate_reference_table.py.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_10_tests_shared_test_component_mandatoriness.py.md` | 1 | Procedure | Pending | — | — |
| `20261030-115752_11_tests_shared_test_runtime_tool_registry.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_12_tests_shared_test_tool_routing_validation.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_13_tests_shared_test_tool_executor.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_14_tests_shared_test_tool_executor_routing.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_15_tests_agent_services_test_runtime_tool_routing_integration.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_16_tests_agent_commands_test_cmd_mcp.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_17_tests_shared_test_rag_tools_consistency.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_18_tests_shared_test_route_resolver.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_19_tests_agent_services_test_config_reload.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_20_tests_agent_test_tool_policy.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_21_tests_agent_test_tool_policy_comprehensive.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_22_tests_integration_test_production_security_regression.py.md` | 2 | Procedure | Pending | — | — |
| `20261030-115752_23_tests_agent_test_production_config_validator.py.md` | 3 | Procedure | Pending | — | — |
| `20261030-115752_24_tests_agent_test_startup_validation.py.md` | 3 | Procedure | Pending | — | — |
| `20261030-115752_25_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_26_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_27_docs_22_mcp_mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_28_config_documentation_canonical_sources.toml.md` | 4 | Procedure | Pending | — | — |
| `20261030-115752_29_tools_TOOL_DESCRIPTIONS.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- Issue source: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`

## Requirement Traceability
- Issue Required Change "Require allowed_servers ... empty set denies all" → REQ-001, AC-1 → Phase 2.
- Issue Required Change "machine-readable component-mandatoriness registry (fields ...)" → REQ-002/003, AC-2 → Phase 1.
- Issue Required Change "validate config required against registry; unknown/conflict fatal" → REQ-004, AC-3 → Phase 3.
- Issue Required Change "generate diagnostics and operator reference from it" → REQ-005, AC-4 → Phase 4.
- Issue Required Change "measure blast radius; migrate in small steps" → REQ-006 → Phase 2.
- Issue AC "registry cannot be published without posture evaluation" → AC-5 → verified
  already structural; test-only.
- Issue Constraint "registry is derived; no competing copy of ADR-004 criteria" → REQ-005, A-2.
- Issue Constraint "shared stays a leaf" → REQ-007 → lint-imports gate.
- Issue Unresolved #1/#2/#3 → resolved in Background / A-2 / U-1.
