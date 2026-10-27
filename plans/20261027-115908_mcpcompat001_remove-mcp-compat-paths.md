# Remove the MCP Health re-export and the optional posture_gates default

## Goal
- Close the two MCP backward-compatibility paths this Issue names: delete the
  `shared.mcp_config` re-export of `McpServerHealthState` / `McpServerHealthRegistry` so
  `shared.mcp_health` is the only import path for the health types, and make
  `McpToolDiscoveryService` require a real Security Posture gate map so the
  `posture_gates=None` migration-window default cannot survive or be reintroduced.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete the `from shared.mcp_health import ... # noqa: F401` block in
    `scripts/shared/mcp_config.py` (line 19) and switch every remaining consumer to
    `from shared.mcp_health import ...`.
  - Make `posture_gates` a required argument of `McpToolDiscoveryService.__init__` and
    update every construction site (1 production, 6 test call sites verified).
  - Update the tests that construct discovery without a gate.
  - Correct `docs/22_mcp/mcp_03_03_transport-and-health.md` line 35, which states that
    `shared/mcp_config.py` re-exports the health class.
- **Out-of-Scope**:
  - Any change to the runtime semantics of the health registry, `StartupMode`
    enforcement (`_should_skip_startup_check`), or the tool-allowlist plumbing itself.
  - Any change to `collect_server_postures` or gate-row semantics
    (`scripts/agent/services/mcp_health.py`).
  - The `posture_gates={}` empty-map behavior: an empty gate map remains a valid,
    explicit value (registers nothing new; `allowed_server_keys({})` is empty and only
    affects servers with no gate row, i.e. disabled/startup_mode-none servers that
    already register no tools).
- **Dependencies**: No fix-order dependency on sibling issues. Shared-file overlap
  adjudications are recorded in `Assumptions` (mcpinv001/mcpinv003/mcpinv004 Plans touch
  `scripts/shared/tool_transport_invoker.py` and `scripts/agent/context.py`); whichever
  Plan is implemented later must rebase its edits onto this Plan's import changes.

## Background
Source: `memo-issue.md` item H-01 and the Medium M-03 docstring bullet. The Issue was
re-verified against current source on 2026-10-27. Two compatibility surfaces exist:

1. Re-export: `scripts/shared/mcp_config.py:19-22` re-publishes both health types with
   `# noqa: F401`. Verified remaining consumers: `scripts/agent/services/mcp_status.py:15-19`,
   `scripts/agent/startup_reporter.py:84` (deferred import), `scripts/agent/context.py:31`,
   `scripts/shared/tool_transport_invoker.py:15-21`, `tests/shared/test_tool_executor.py:15-19`,
   `tests/shared/test_tool_executor_routing.py:14-20`,
   `tests/shared/test_tool_transport_invoker.py:14-18` (registry via `mcp_config`, state
   already direct at line 20), and `tests/integration/test_agent_mcp_integration.py:18`
   (mixed import with legitimate `McpServerConfig`/`TransportType`).
2. Optional posture gate: `scripts/agent/services/mcp_tool_discovery.py:95` defaults
   `posture_gates` to `None`; the docstring (lines 99-101) names `None` "the
   migration-window value, and the only production caller passes real gates."

Corrections to the Issue text found during verification:

- The Issue's construction-site citation `tests/agent/test_mcp_health_posture.py:241-247,358-364`
  is stale. That file never constructs `McpToolDiscoveryService` (no `discover_all` or
  `posture_gates` reference). The verified construction sites are:
  `scripts/agent/startup_validation.py:115-117` (production, real gates from
  `collect_server_postures`), `tests/integration/test_production_security_regression.py:204,245`,
  `tests/agent/services/test_runtime_tool_routing_integration.py:313,347` (all four without
  gates), and `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` (gates at
  :121,132,176; no-gate at :142; empty map at :153).
- The Issue's doc citation `22_mcp/mcp_04_03_tool_discovery_service.md:63-71` no longer
  exists after the docs restructuring; the surviving doc statement about the re-export is
  `docs/22_mcp/mcp_03_03_transport-and-health.md:35`. No docs file mentions
  `posture_gates` at all (repo-wide grep).
- The health registry's runtime behavior, including half-open cooldown, is unchanged by
  this Plan.

## Problem
Importing health types through `shared.mcp_config` keeps a compatibility alias alive: a
future refactor of `shared.mcp_health` can silently break callers who never import the
canonical module. The optional `posture_gates` default keeps an unsafe discovery path —
gate-less registration of every reachable server's tools — reachable from any new call
site, even though the single production caller already supplies real gates.

## Reason for Change
The migration window the docstring names is over: every production path passes gates
(`scripts/agent/startup_validation.py:114-116`), and half the test callers already import
health types directly from `shared.mcp_health` (`cmd_mcp.py`, `factory.py`,
`test_mcp_health.py`, `test_cmd_mcp.py`, `test_agent_factory.py`,
`test_tool_executor_order.py`, partially `test_tool_transport_invoker.py`). Closing both
paths now makes the canonical import surface and the gate requirement enforced by the
signatures themselves.

## Implementation Intent
Mechanical import-path migration plus a signature tightening:
delete the re-export block, retarget the eight remaining consumer imports, make
`posture_gates` a required keyword with no default in `McpToolDiscoveryService.__init__`,
remove the `None` branch in `discover_all` so the allowlist is always derived from the
supplied gate map, and update the gate-less test constructions to pass explicit gate maps
matching the servers each test configures (or `{}` where the test asserts a server
contributes no tool). `mcp_tool_discovery_registry.py` keeps its `allowed_servers=None`
parameter: `None` there still means "allow any source" and remains the internal value for
servers without a gate row (disabled / `startup_mode=none`), so the plumbing contract is
unchanged.

## Requirements
- `REQ-001`: `shared.mcp_health` is the only import path for `McpServerHealthState` and
  `McpServerHealthRegistry`; `scripts/shared/mcp_config.py` contains no re-export of them.
- `REQ-002`: All production and test consumers import the health types from
  `shared.mcp_health` (or, for mixed imports, split the health names out of the
  `shared.mcp_config` import statement).
- `REQ-003`: `McpToolDiscoveryService.__init__` requires `posture_gates` (no `None`
  default); the docstring no longer describes a migration window.
- `REQ-004`: `discover_all` always computes `allowed_servers` from the supplied gate map;
  no code path leaves it `None` because a gate was omitted.
- `REQ-005`: Every test that previously constructed `McpToolDiscoveryService(ctx)` passes
  an explicit gate map that preserves the behavior the test asserts.
- `REQ-006`: `docs/22_mcp/mcp_03_03_transport-and-health.md` no longer claims
  `shared/mcp_config.py` re-exports the health class.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/mcp_config.py | Delete the `from shared.mcp_health import ... # noqa: F401` block | REQ-001 | REQ-001 / AC-01 | lines 19-22 (verified) | tests/shared/test_mcp_health.py | Verified |
| scripts/agent/services/mcp_status.py | Split health-type import to `shared.mcp_health` | REQ-002 | REQ-002 / AC-02 | lines 15-19 (verified) | tests/agent/services (existing suite) | Verified |
| scripts/agent/startup_reporter.py | Retarget deferred import at line 84 | REQ-002 | REQ-002 / AC-02 | line 84 (verified) | tests/agent (startup-reporter tests) | Verified |
| scripts/agent/context.py | Retarget `McpServerHealthRegistry` import | REQ-002 | REQ-002 / AC-02 | line 31 (verified) | tests/agent/test_agent_factory.py | Verified |
| scripts/shared/tool_transport_invoker.py | Split health-type imports to `shared.mcp_health` | REQ-002 | REQ-002 / AC-02 | lines 15-21 (verified) | tests/shared/test_tool_transport_invoker.py | Verified |
| tests/shared/test_tool_executor.py | Retarget health-type imports | REQ-002 | REQ-002 / AC-05 | lines 15-19 (verified) | itself | Verified |
| tests/shared/test_tool_executor_routing.py | Retarget health-type imports | REQ-002 | REQ-002 / AC-05 | lines 14-20 (verified) | itself | Verified |
| tests/shared/test_tool_transport_invoker.py | Move `McpServerHealthRegistry` import to `shared.mcp_health` | REQ-002 | REQ-002 / AC-05 | lines 14-20 (verified) | itself | Verified |
| tests/integration/test_agent_mcp_integration.py | Split health names out of the mixed `mcp_config` import | REQ-002 | REQ-002 / AC-05 | line 18 (verified) | itself | Verified |
| scripts/agent/services/mcp_tool_discovery.py | Make `posture_gates` required; remove the `None` branch; update docstring | REQ-003, REQ-004 | REQ-003, REQ-004 / AC-03, AC-04 | lines 45-49, 95-113 (verified) | tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Verified |
| scripts/agent/startup_validation.py | Verify-only check that the production call still matches the new required signature (no edit expected) | REQ-003 | REQ-003 / AC-03 | lines 114-117 (verified) | tests/integration/test_production_security_regression.py | Verified |
| tests/agent/services/test_mcp_tool_discovery_posture_gate.py | Replace the no-gate construction with explicit gate maps; drop the `None`-case test | REQ-003, REQ-005 | REQ-005 / AC-05 | lines 121,132,142,153,176 (verified) | itself | Verified |
| tests/integration/test_production_security_regression.py | Add explicit gate maps to the two constructions | REQ-003, REQ-005 | REQ-005 / AC-05 | lines 204,245 (verified) | itself | Verified |
| tests/agent/services/test_runtime_tool_routing_integration.py | Add explicit gate maps to the two constructions | REQ-003, REQ-005 | REQ-005 / AC-05 | lines 313,347 (verified) | itself | Verified |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Remove the "mcp_config only re-exports" sentence | REQ-006 | REQ-006 / AC-06 | line 35 (verified) | N/A | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/services/mcp_health.py | Canonical health module; `collect_server_postures`, `PostureGate`, `allowed_server_keys` semantics for building test gate maps | REQ-003, REQ-005 |
| scripts/agent/services/mcp_tool_discovery_registry.py | Confirms `allowed_servers=None` internal contract is unchanged (row filter + registry construction) | REQ-004 |
| scripts/agent/services/mcp_tool_discovery_fetch.py | Confirms fetching is HTTP-transport-only and gate-independent | REQ-004 |
| scripts/shared/runtime_tool_registry.py | `allowed_servers` enforcement semantics inside the registry | REQ-004 |
| scripts/shared/http_transport.py | Module-level `get_effective_health_timeout` stays in `mcp_config`; mcp_status's mixed import must keep it there | REQ-002 |
| tests/agent/test_mcp_health_posture.py | Gate-construction helpers to reuse in test gate maps | REQ-005 |
| docs/00_index.md | Task-scope mapping for the doc update in REQ-006 | REQ-006 |

## Acceptance Criteria
- `AC-01` (REQ-001): `grep "mcp_health" scripts/shared/mcp_config.py` returns nothing;
  ruff reports no `F401` suppression in that file.
- `AC-02` (REQ-002): no file under `scripts/` or `tests/` imports
  `McpServerHealthState` or `McpServerHealthRegistry` from `shared.mcp_config`.
- `AC-03` (REQ-003): `McpToolDiscoveryService(ctx)` without `posture_gates` raises
  `TypeError`; full-suite collection passes with zero such call sites.
- `AC-04` (REQ-004): `discover_all` contains no `self._posture_gates is None` branch;
  production startup behavior for a gated server is unchanged (server whose posture was
  rejected still contributes no tool).
- `AC-05` (REQ-005): all existing test assertions still pass after gate maps are supplied;
  the posture-gate regression tests (`gates` / `{}` cases) keep their meaning.
- `AC-06` (REQ-006): the re-export sentence is gone from
  `docs/22_mcp/mcp_03_03_transport-and-health.md`.

## Tests
- `REQ-001`/`REQ-002`: existing suites `tests/shared/test_mcp_health.py`,
  `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`,
  `tests/shared/test_tool_transport_invoker.py`, `tests/agent/` — import migration must be
  behavior-neutral; run the full suite.
- `REQ-003`: add one test asserting `McpToolDiscoveryService(ctx)` (no gate argument)
  raises `TypeError` (in `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`).
- `REQ-005`: the four gate-less constructions become explicit:
  `test_production_security_regression.py:204,245` and
  `test_runtime_tool_routing_integration.py:313,347` pass a gate map built from their
  configured servers (reuse the `_gate()`-style helper from
  `tests/agent/test_mcp_health_posture.py`); the `:142` no-gate case in
  `test_mcp_tool_discovery_posture_gate.py` is replaced by the `TypeError` test, and the
  `{}` case at `:153` is kept.

## Documentation Impact
`docs/22_mcp/mcp_03_03_transport-and-health.md` must be updated (REQ-006): remove the
re-export claim. Named via `docs/00_index.md` task scope for MCP transport/health. No
other doc requires updating; docs do not currently document `posture_gates` (verified by
repo-wide grep).

## Assumptions
- No out-of-repo caller imports the health types through `shared.mcp_config` (the Issue
  states plugin references are absent; nothing in this repo contradicts it).
- An empty gate map `{}` remains a legal explicit value distinct from the removed `None`.
- `allowed_servers=None` inside `mcp_tool_discovery_registry.py` /
  `RuntimeToolRegistry` stays: it is the internal allow-any filter for servers with no
  gate row, not the removed public default.
- Cross-plan overlap adjudications (via `tools/check_plan_target_overlaps.py` at
  implementation time): this Plan's import edits in `scripts/shared/tool_transport_invoker.py`
  and `scripts/agent/context.py` are Compatible with the mcpinv001/mcpinv003 Plans
  (health-registry usage in the invoker) and the mcpinv004 Plan (per-server concurrency);
  different lines/responsibilities. `scripts/agent/context.py` is also targeted by the
  turn001 and memory001 Plans (service wiring); this Plan changes only the health-registry
  import line — Compatible. Whichever Plan lands later must rebase onto this
  Plan's import lines. Recorded bidirectionally here; the counterpart Plans were frozen
  before this Issue batch existed and must be re-checked with the overlap tool before
  either side is implemented.
- Overlap adjudication (2026-10-27 overlap-tool run): `docs/22_mcp/mcp_03_03_transport-and-health.md`
  is also edited by the frozen mcpinv003 Plan, which updates the retry-message bullet — a
  different sentence from this Plan's re-export sentence. Compatible; rebase between edits.
- Overlap adjudication with the mcpcompat003 Plan (same batch): `tests/agent/services/test_runtime_tool_routing_integration.py`
  is edited by both (this Plan adds gate maps at lines 313/347; mcpcompat003 re-runs and
  adjusts the incomplete-declaration test) — different tests in the same file, Compatible.
  `scripts/agent/services/mcp_tool_discovery_registry.py` is a read-only Reference File
  here and untouched by mcpcompat003's edits — Compatible.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `test_runtime_tool_routing_integration.py`'s mock MCP servers should be gated `Accepted` or left absent (gate map `{}`) depends on which behavior each test asserts at lines 313/347 | Assertion bodies of those two tests were not read line-by-line during verification | Read both test bodies at implementation time; choose gate maps preserving each assertion | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/mcp_config.py | Delete re-export block | 8 consumer files (all in-repo) | 3 | low (single maintainer area) | No deploy.sh change; redeploy files + service restart |
| scripts/agent/services/mcp_tool_discovery.py | Required parameter + branch removal | 1 production caller, 6 test call sites | 10 | medium (active area) | No deploy.sh change; service restart |
| scripts/agent/context.py | Import line change | shared MCP wiring surface | 8 | medium | No deploy.sh change |
| scripts/shared/tool_transport_invoker.py | Import split | tool-execution hot path | 4 | medium | No deploy.sh change |
| scripts/agent/startup_reporter.py | Deferred import change | startup report path | 5 | low | No deploy.sh change |
| scripts/agent/services/mcp_status.py | Import split | MCP status command path | 1 | low | No deploy.sh change |
| scripts/agent/startup_validation.py | Verify only | production startup chain | 5 | medium | No deploy.sh change |
| scripts/agent/services/mcp_tool_discovery_registry.py | Reference only (no edit) | registry build | 1 | low | None |
| tests (4 files) | Import retarget | test suite | 0-6 | n/a | None |
| docs/22_mcp/mcp_03_03_transport-and-health.md | One-sentence correction | docs | 9 | medium | None |

## Design
- Import surface: `shared.mcp_health` becomes the single canonical source for the two
  health types; `shared.mcp_config` keeps only what it actually defines
  (`McpServerConfig`, `StartupMode`, `TransportType`, `get_effective_health_timeout`).
  This matches the layer contract already used by `cmd_mcp.py`, `factory.py`, and five
  test files.
- Gate requirement: the required-argument signature is the fail-closed mechanism — a new
  call site physically cannot discover without deciding a gate map. The internal
  `allowed_servers` plumbing keeps its current meaning so the registry contract, the
  duplicate-exclusion path, and the unavailable-server filter are untouched.
- Semantics preserved: with gates required, production `allowed_servers` is always the
  `allowed_server_keys()` frozenset of usable HTTP servers — identical to today, because
  `collect_server_postures` covers exactly the servers discovery can fetch
  (HTTP, non-disabled, and `startup_mode=none` servers register no tools anyway).

## Implementation steps
1. **Phase 1: Import migration (re-export removal)**
   - [ ] Delete the re-export block (REQ-001; scripts/shared/mcp_config.py)
   - [ ] Retarget the four production imports (REQ-002; scripts/agent/services/mcp_status.py, scripts/agent/startup_reporter.py, scripts/agent/context.py, scripts/shared/tool_transport_invoker.py)
   - [ ] Retarget the four test imports (REQ-002; tests/shared/test_tool_executor.py, tests/shared/test_tool_executor_routing.py, tests/shared/test_tool_transport_invoker.py, tests/integration/test_agent_mcp_integration.py)
2. **Phase 2: posture_gates required**
   - [ ] Make `posture_gates` required, remove the `None` branch, update the docstring and module header (REQ-003, REQ-004; scripts/agent/services/mcp_tool_discovery.py)
   - [ ] Confirm the production call site still matches (REQ-003; scripts/agent/startup_validation.py)
   - [ ] Update gate-less test constructions and add the `TypeError` test (REQ-005; tests/agent/services/test_mcp_tool_discovery_posture_gate.py, tests/integration/test_production_security_regression.py, tests/agent/services/test_runtime_tool_routing_integration.py)
3. **Phase 3: Verification & docs**
   - [ ] Full test suite + ruff/mypy clean (all REQs)
   - [ ] Remove the re-export sentence (REQ-006; docs/22_mcp/mcp_03_03_transport-and-health.md)
   - [ ] Deployment check: files synced to /opt/llm, agent service restart, `cmd_agent` startup log shows `mcp_tool_discovery` OK (no target-file change; operational check)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_config.py + consumers | Static grep + full unit suite | `rg "McpServerHealth" scripts/ tests/ -g '*.py'` filtered to `from shared.mcp_config`; `uv run pytest` | zero re-export consumers; suite green |
| scripts/agent/services/mcp_tool_discovery.py | Unit (posture-gate tests) + integration | `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py tests/integration/test_production_security_regression.py` | gate required; gated-server exclusion unchanged |
| scripts/agent/startup_validation.py | Integration | `uv run pytest tests/agent -k startup` + production startup log | discovery step still passes with real gates |
| whole repo | Lint/type | `uv run ruff check scripts tests` ; `uv run mypy scripts` | no F401 additions, no type errors |

## Risks
- **Risk**: making `posture_gates` required breaks an out-of-repo caller → **Mitigation**:
  Issue states no plugin references; the signature change is a deliberate fail-closed
  break — any external caller must pass an explicit gate map, which is the intended
  outcome.
- **Risk**: supplying gate maps in tests changes what a test exercises (e.g. a mock server
  silently excluded by an allowlist) → **Mitigation**: build gate maps from each test's own
  configured servers (helper pattern in `tests/agent/test_mcp_health_posture.py`);
  UNK-01 covers the two integration sites.
- **Risk**: this Plan edits `scripts/agent/context.py` and
  `scripts/shared/tool_transport_invoker.py`, both also targeted by the frozen
  mcpinv001/003/004 Plans → **Mitigation**: import-line changes only; overlap tool rerun
  before implementation; later Plan rebases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: import migration | Pending | — | — | |
| 2 | Phase 2: posture_gates required | Pending | — | — | |
| 3 | Phase 3: verification & docs | Pending | — | — | |

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
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-115908
- **Related target files**: scripts/shared/mcp_config.py, scripts/agent/services/mcp_status.py, scripts/agent/startup_reporter.py, scripts/agent/context.py, scripts/shared/tool_transport_invoker.py, tests/shared/test_tool_executor.py, tests/shared/test_tool_executor_routing.py, tests/shared/test_tool_transport_invoker.py, tests/integration/test_agent_mcp_integration.py, scripts/agent/services/mcp_tool_discovery.py, scripts/agent/startup_validation.py, tests/agent/services/test_mcp_tool_discovery_posture_gate.py, tests/integration/test_production_security_regression.py, tests/agent/services/test_runtime_tool_routing_integration.py, docs/22_mcp/mcp_03_03_transport-and-health.md

### Requirement Traceability
| Requirement | Source | Plan Section | Target File | Test / Validation | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261027-104222 (Summary, Background) | Requirements, Target Files row 1 | scripts/shared/mcp_config.py | rg check, AC-01 | Planned |
| REQ-002 | issues/20261027-104222 (Background) | Target Files rows 2-9 | consumer files listed | existing suites, AC-02 | Planned |
| REQ-003 | issues/20261027-104222 (Summary, M-03) | Target Files rows 10-14 | scripts/agent/services/mcp_tool_discovery.py + tests | TypeError test, AC-03 | Planned |
| REQ-004 | issues/20261027-104222 (Background, gate plumbing) | Design | scripts/agent/services/mcp_tool_discovery.py | posture-gate tests, AC-04 | Planned |
| REQ-005 | issues/20261027-104222 (Test Plan) | Tests | test construction sites | full suite, AC-05 | Planned |
| REQ-006 | issues/20261027-104222 (Doc Correction) | Documentation Impact | docs/22_mcp/mcp_03_03_transport-and-health.md | doc review, AC-06 | Planned |
