## Goal
- Make `shared.mcp_health` the only import path for `McpServerHealthState` and `McpServerHealthRegistry`, make `McpToolDiscoveryService` require real Security Posture gates, and add checker rules so that neither backward-compatibility path can return unnoticed, without changing the runtime behavior of the production startup path.

## Priority
Medium

## Scope
- **In-Scope**:
  - Move the eight importers of the Health types (four in `scripts/`, four in `tests/`) from `shared.mcp_config` to `shared.mcp_health`, then delete the re-export and its `# noqa: F401`.
  - Make `posture_gates` a required argument of `McpToolDiscoveryService`, remove the `None` branch of `discover_all()`, and rewrite the docstrings without migration-window wording.
  - Update the 65 gate-less constructor call sites in four test files through a shared test helper, replace the one test that asserts the `None` behavior, and keep the empty-gate test.
  - Add AST-based checker rules to `tools/check_compat_shims.py` (with tests and a catalog update) for the old Health import and for a gate-less `McpToolDiscoveryService(` call.
  - Remove the "only re-exports" sentence from the MCP transport-and-health document.
- **Out-of-Scope**:
  - Changing posture classification or `allowed_server_keys()` semantics.
  - Rewriting unrelated discovery tests.
  - The Tool Schema 2.0 validator and the legacy `resource_scope` policy (the `mcpcompat003` issue).
  - Removing the `eventbus.db` facade (the `ebcompat002` issue).
  - The `None` default of `RuntimeToolRegistry` and of the registry-building helper of the discovery package (recorded as UNK-02).
- **Dependencies**: Sequencing only, no hard ordering. The sibling issues `issues/20261027-104252_ebcompat002_decide-eventbus-db-facade.md` and `issues/20261027-104324_mcpcompat003_align-legacy-resource-scope.md` also edit `tools/check_compat_shims.py` and its tests, so the checker phase of this Plan lands before theirs and the three checker edits are never made in parallel. The open issues `issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md` and `issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md` edit different parts of `scripts/shared/tool_transport_invoker.py` (pre-call gates and semaphores); this Plan only changes its import block, so the edits are compatible but must be rebased in turn.

## Background
- `scripts/shared/mcp_config.py` imports both Health types from `shared.mcp_health` with `# noqa: F401` only to re-publish them. A syntax-level scan of `scripts/`, `tests/` and `tools/` found exactly eight importers through `shared.mcp_config`: `scripts/agent/context.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/startup_reporter.py` (deferred import), `scripts/shared/tool_transport_invoker.py`, `tests/integration/test_agent_mcp_integration.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py` and `tests/shared/test_tool_transport_invoker.py`. No module-attribute access and no patch target uses the old path.
- `McpToolDiscoveryService.__init__` declares `posture_gates: Mapping[str, PostureGate] | None = None`. When `None`, `discover_all()` passes `allowed_servers=None` and no posture allowlist applies. The docstrings call `None` "the migration-window value" and say tools are registered "as before". The only production caller, `scripts/agent/startup_validation.py`, collects real gates with `collect_server_postures()` and passes them.
- A syntax-level scan counted 65 gate-less constructor calls: 60 in `tests/agent/services/test_mcp_tool_discovery.py`, 2 in `tests/integration/test_production_security_regression.py`, 2 in `tests/agent/services/test_runtime_tool_routing_integration.py` and 1 in `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` (`test_no_gate_supplied_registers_every_reachable_tool`, which asserts the `None` behavior). `test_an_empty_gate_registers_no_mcp_tool` already asserts an empty registry for an empty gate mapping.
- `check_compat_patterns` in the checker matches single stripped lines, so it cannot detect a multi-line `from shared.mcp_config import (...)` or a multi-line constructor call; both rules therefore need syntax-tree detection. The checker's removed-name stage scans `docs/` only.
- The only document sentence that claims the re-export is in the MCP transport-and-health document; the system-overview and configuration-inventory documents already name `shared/mcp_health.py` correctly.
- `RuntimeToolRegistry` and the registry-building helper of the discovery package keep the same "`None` means no gate was supplied" default; the issue does not cover them.

## Problem
- The re-export keeps a second public path for the Health types, so the canonical module is not enforced and `mcp_status.py` depends on the old path.
- A caller that forgets `posture_gates` silently gets a discovery registry with no Security Posture gating, and 65 test call sites exercise that ungated path instead of the production path.

## Reason for Change
A latent fail-open default on a security gate and a duplicated import surface. No production misbehavior is evidenced because the single production caller passes gates, so the priority is Medium. Nothing makes the change time-sensitive; doing it before more callers adopt the old paths keeps the cost low.

## Implementation Intent
Move every caller to the canonical import, then delete the re-export. Make `posture_gates` required and delete the `None` branch, keeping the fail-closed meaning that an empty gate mapping registers no server. Update the tests first (pass gates explicitly while the parameter is still optional), then flip the signature, so each step leaves the suite green. Add two syntax-tree rules to the compatibility checker in separate functions so the complexity of its `main` function does not grow. Remove the migration-window wording and the stale document sentence.

## Requirements
- `REQ-001`: Change every import of `McpServerHealthState` and `McpServerHealthRegistry` from `shared.mcp_config` to `shared.mcp_health` in the eight importer files, and confirm by a repository-wide search that no importer remains.
- `REQ-002`: Remove the re-export and its `# noqa: F401` from `scripts/shared/mcp_config.py` so that it no longer references either type.
- `REQ-003`: Make `posture_gates` a required argument of `McpToolDiscoveryService`, remove the `None` branch of `discover_all()`, and rewrite the class and module docstrings without migration-window wording, keeping the production startup behavior unchanged.
- `REQ-004`: Pass real gates at all 65 gate-less test call sites through one shared test helper, replace the test that asserts the `None` behavior with a test that `McpToolDiscoveryService(ctx)` raises `TypeError`, and keep the empty-gate test.
- `REQ-005`: Add checker rules that report a `shared.mcp_config` import of either Health type and a `McpToolDiscoveryService(` call without `posture_gates`, with checker tests and an updated catalog entry, implemented so that the existing checker behavior is unchanged.
- `REQ-006`: Remove the claim that `shared/mcp_config.py` re-exports the Health class from the MCP transport-and-health document, describing only current boundaries.
- `REQ-007`: Leave the production startup behavior, the import-layer contracts, the type check, the full test suite and the documentation checkers unchanged or passing.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | MCP server configuration models | Remove the Health re-export and its `# noqa: F401` | REQ-002; AC-2 | Imports both types from `shared.mcp_health` with `# noqa: F401` solely to re-publish them (checked in Step 3) | `tests/shared/test_mcp_config.py` | Verified |
| `scripts/agent/services/mcp_status.py` | MCP status service | Import `McpServerHealthState` from `shared.mcp_health` | REQ-001; AC-1 | Syntax-level scan: imports `McpServerHealthState` from `shared.mcp_config` (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `scripts/agent/startup_reporter.py` | Startup reporting | Import `McpServerHealthState` (deferred import) from `shared.mcp_health` | REQ-001; AC-1 | Deferred import of `McpServerHealthState` from `shared.mcp_config` inside a function (checked in Step 3) | `tests/agent/test_startup_reporter.py` | Verified |
| `scripts/agent/context.py` | Agent context | Import `McpServerHealthRegistry` from `shared.mcp_health` | REQ-001; AC-1 | Imports `McpServerHealthRegistry` from `shared.mcp_config` at module level (checked in Step 3) | `tests/agent/test_context.py` | Verified |
| `scripts/shared/tool_transport_invoker.py` | MCP tool transport invoker | Import both Health types from `shared.mcp_health` | REQ-001; AC-1 | Multi-line import from `shared.mcp_config` of `McpServerConfig`, both Health types and `StartupMode` (checked in Step 3) | `tests/shared/test_tool_transport_invoker.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery.py` | MCP tool discovery | Make `posture_gates` required, remove the `None` branch, rewrite the docstrings | REQ-003; AC-3 | `posture_gates: Mapping[str, PostureGate] \| None = None`; `discover_all()` passes `allowed_servers=None` when it is `None`; docstrings say "migration-window value" (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Verified |
| `tests/shared/test_tool_executor.py` | Tool executor tests | Import both Health types from `shared.mcp_health` | REQ-001; AC-1 | Imports both types from `shared.mcp_config` (checked in Step 3) | `tests/shared/test_tool_executor.py` | Verified |
| `tests/shared/test_tool_executor_routing.py` | Tool executor routing tests | Import both Health types from `shared.mcp_health` | REQ-001; AC-1 | Multi-line import of both types from `shared.mcp_config` (checked in Step 3) | `tests/shared/test_tool_executor_routing.py` | Verified |
| `tests/shared/test_tool_transport_invoker.py` | Transport invoker tests | Import `McpServerHealthRegistry` from `shared.mcp_health` | REQ-001; AC-1 | Imports `McpServerHealthRegistry` from `shared.mcp_config`; the file already imports from `shared.mcp_health` (checked in Step 3) | `tests/shared/test_tool_transport_invoker.py` | Verified |
| `tests/integration/test_agent_mcp_integration.py` | Agent-MCP integration tests | Import `McpServerHealthRegistry` from `shared.mcp_health` | REQ-001; AC-1 | Imports `McpServerConfig`, `McpServerHealthRegistry` and `TransportType` from `shared.mcp_config` (checked in Step 3) | `tests/integration/test_agent_mcp_integration.py` | Verified |
| `tests/agent/services/_discovery_gates.py` | Shared test helper for discovery gates (New file) | Create a helper that builds a green `PostureGate` for every server key of a test context | REQ-004; AC-4 | New file; its directory `tests/agent/services/` exists and the path is free; the sibling pattern `tests/mcp_servers/_auth_headers.py` is imported as `tests.mcp_servers._auth_headers` (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `tests/agent/services/test_mcp_tool_discovery.py` | Discovery service tests | Pass gates at 60 gate-less constructor calls | REQ-004; AC-4 | Syntax-level scan: 60 calls, none with `posture_gates` (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Posture-gate tests | Replace `test_no_gate_supplied_registers_every_reachable_tool` with a `TypeError` test; keep the empty-gate test | REQ-004; AC-4, AC-5 | The test builds `McpToolDiscoveryService(ctx)` without gates and asserts every reachable tool is registered; `test_an_empty_gate_registers_no_mcp_tool` asserts an empty registry (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Verified |
| `tests/integration/test_production_security_regression.py` | Production security regression tests | Pass gates at 2 constructor calls | REQ-004; AC-4 | Syntax-level scan: 2 gate-less calls (checked in Step 3) | `tests/integration/test_production_security_regression.py` | Verified |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Runtime routing integration tests | Pass gates at 2 constructor calls | REQ-004; AC-4 | Syntax-level scan: 2 gate-less calls (checked in Step 3) | `tests/agent/services/test_runtime_tool_routing_integration.py` | Verified |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | MCP transport and health document | Remove the "only re-exports" sentence | REQ-006; AC-6 | Line under `## McpServerHealthRegistry (\`shared/mcp_health.py\`)` reads "The canonical module is `shared/mcp_health.py`; `shared/mcp_config.py` only re-exports the class." (checked in Step 3) | N/A: documentation-only; `tools/check_docs_consistency.py --domain mcp` | Verified |
| `tools/check_compat_shims.py` | Compatibility checker | Add the two syntax-tree rules in separate functions | REQ-005; AC-7 | `check_compat_patterns` matches single stripped lines; `main` has cyclomatic complexity 18; patterns and the removed-name stage cannot see multi-line imports or calls (checked in Step 3) | `tests/tools/test_check_compat_shims.py` | Verified |
| `tests/tools/test_check_compat_shims.py` | Checker tests | Add tests for both rules | REQ-005; AC-7 | Existing test module for the checker; listed in `tools/compat_exceptions.toml` as a fixture exception (checked in Step 3) | `tests/tools/test_check_compat_shims.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool catalog | Update the `check_compat_shims.py` entries | REQ-005; AC-7 | The catalog lists the tool in its summary and detail tables as detecting leftover compatibility stubs and shims (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

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
| `scripts/shared/mcp_health.py` | Canonical module of the Health types; imports only the standard library, so no import cycle arises | REQ-001, REQ-002 |
| `scripts/agent/startup_validation.py` | The only production caller; passes gates from `collect_server_postures()` | REQ-003 |
| `scripts/agent/services/mcp_health.py` | Defines `PostureGate` and `allowed_server_keys()` used by the helper and the discovery service | REQ-003, REQ-004 |
| `scripts/shared/runtime_tool_registry.py` | Keeps its own `None` default; read to keep the discovery change consistent (UNK-02) | REQ-003 |
| `scripts/agent/services/mcp_tool_discovery_registry.py` | Registry-building helper that receives the allowlist; unchanged | REQ-003 |
| `tests/mcp_servers/_auth_headers.py` | Precedent for an underscore-named shared test helper module | REQ-004 |
| `tools/compat_exceptions.toml` | Exception ledger that lists checker fixtures and the discovery test | REQ-005 |
| `.importlinter` | Import-layer contracts that must still pass after the import moves | REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg "from shared.mcp_config import" scripts tests` shows no import of `McpServerHealthState` or `McpServerHealthRegistry`, and a syntax-level scan finds no importer.
- AC-2 (REQ-002): `scripts/shared/mcp_config.py` no longer references either type and has no `# noqa: F401` for them.
- AC-3 (REQ-003): `McpToolDiscoveryService(ctx)` without `posture_gates` raises `TypeError`, `discover_all()` has no `None` branch, and no docstring contains migration-window wording.
- AC-4 (REQ-004): No `McpToolDiscoveryService(` call without `posture_gates` remains in `scripts/` or `tests/`, and the discovery and integration test files pass.
- AC-5 (REQ-004): A test confirms that `McpToolDiscoveryService(ctx)` raises `TypeError`, and `test_an_empty_gate_registers_no_mcp_tool` still asserts an empty registry.
- AC-6 (REQ-006): The document no longer claims that `shared/mcp_config.py` re-exports the Health class.
- AC-7 (REQ-005): `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports a reintroduced old import and a gate-less constructor call (shown by the checker tests) and passes on the repository.
- AC-8 (REQ-007): The type check, the import-layer check, the test suite, ruff, bandit and the documentation checkers under Tests pass, and the production startup behavior is unchanged.

## Tests
- `uv run pytest tests/shared tests/agent/services tests/integration/test_agent_mcp_integration.py tests/integration/test_production_security_regression.py tests/tools/test_check_compat_shims.py -v` (REQ-001, REQ-003, REQ-004, REQ-005).
- `uv run pytest` (full suite), `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run ruff format` and `uv run ruff check` on changed files, `uv run bandit` on changed scripts (REQ-007).
- `uv run mypy tools/check_compat_shims.py` (path passed explicitly) and `uv run bandit tools/check_compat_shims.py` (REQ-005).
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` (REQ-005).
- `uv run python tools/check_docs_consistency.py --domain mcp`, `check_docs_quality.py`, `check_docs_structure.py` on the changed document, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` (REQ-006).
- `uv run python tools/check_tool_descriptions_sync.py` (REQ-005), and a diff-cover run per `rules/toolchain.md` (REQ-007).

## Documentation Impact
Yes, small. The MCP transport-and-health document (located through `docs/00_index.md` "Document References by Task") loses the sentence that claims a re-export; REQ-006 drives it. Describe only current boundaries, add no history note, and copy no implementation detail (`skills/DESIGN.md` Docs content policy). `tools/TOOL_DESCRIPTIONS.md` is updated for the checker (REQ-005). All text is written in English.

## Assumptions
- A required `posture_gates` argument is a compatible change for the single production caller, which already passes gates; the production startup behavior does not change.
- Updating the tests first (explicit gates while the parameter is still optional) leaves the suite green at each step.
- The shared test helper lives in a new underscore-named module under `tests/agent/services/` (precedent `tests/mcp_servers/_auth_headers.py`); the two integration test files import it by its `tests.` path (UNK-01).
- The eight importers and the 65 call sites found by the syntax-level scan are the complete set inside `scripts/`, `tests/` and `tools/`; a repository text search found no other path that imports the Health types through `shared.mcp_config` in `docs/`, `deploy/` or `config/`.
- Step 8b overlap judgments: `tools/TOOL_DESCRIPTIONS.md` is also targeted by `plans/20261027-105004_govrev005_adr-matrix-checker-extension.md`; the designs are compatible (that Plan edits the `check_adr_invariant_matrix.py` rows, this Plan edits the `check_compat_shims.py` rows) and only need rebasing in turn. `scripts/agent/context.py` is also targeted by the Frozen Plans `plans/20261027-070403_turn001_atomic-turn-persistence.md` (adds snapshot and restore methods to `ConvState`) and `plans/20261027-072306_memory001_retry-memory-injection-failure.md` (edits field comments); both are compatible with this Plan's one-line import change although the overlap tool did not list them.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Can the two integration test files import the new helper module through `tests.agent.services._discovery_gates`, given that `tests/agent/` has no `__init__.py`? | Not exercised; only the precedent `tests.mcp_servers._auth_headers` was observed | Try the import in Phase 2; if it fails, give those two files a local one-line gate builder instead and keep the shared helper for the two services test files | False |
| UNK-02 | Should `RuntimeToolRegistry` and the registry-building helper of the discovery package also drop their "`None` means no gate was supplied" default? | No owner decision; outside the issue | Keep them unchanged here; propose a follow-up issue to the repository owner after this Plan is implemented | False |
| UNK-03 | Does a deployed or external consumer outside this repository import the Health types through `shared.mcp_config`? | Only the repository was searched | The repository owner confirms; deletion is reversible by restoring the re-export | False |
| UNK-04 | Implementation order against the sibling checker issues and the open `mcpinv001`/`mcpinv004` issues | The siblings are not yet planned | Implement this Plan's checker phase first; rebase `tool_transport_invoker.py` and the checker around the sibling edits; the implementation-procedure phase reads this Plan's Scope Dependencies | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | Modify | High | 3 | 4 authors (1y), share not measured | not applicable (rsynced) |
| `scripts/agent/services/mcp_status.py` | Modify | Low | 1 | 4 authors (1y), share not measured | not applicable (rsynced) |
| `scripts/agent/startup_reporter.py` | Modify | Low | 5 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `scripts/agent/context.py` | Modify | Medium | 8 | 4 authors (1y), share not measured | not applicable (rsynced) |
| `scripts/shared/tool_transport_invoker.py` | Modify | Medium | 4 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `scripts/agent/services/mcp_tool_discovery.py` | Modify | Medium | 10 | 3 authors (1y), share not measured | not applicable (rsynced) |
| `tests/shared/test_tool_executor.py` | Modify | Low | 2 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/shared/test_tool_executor_routing.py` | Modify | Low | 6 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/shared/test_tool_transport_invoker.py` | Modify | Low | 4 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/integration/test_agent_mcp_integration.py` | Modify | Low | 0 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/agent/services/_discovery_gates.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery.py` | Modify | Medium | 6 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Modify | Low | 1 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `tests/integration/test_production_security_regression.py` | Modify | Low | 1 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Modify | Low | 2 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Low | 9 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tools/check_compat_shims.py` | Modify | Medium | 14 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/tools/test_check_compat_shims.py` | Modify | Low | 6 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 66 | 2 authors (1y), share not measured | not applicable (rsynced) |

## Design
- Path B: nineteen target files and a changed constructor contract of a security-relevant service. Architecture: the import moves keep every file on the same layer (`agent` and `shared` already import `shared.mcp_health`), `shared/mcp_health.py` imports only the standard library so no cycle arises, and the six import-layer contracts were kept before the change. Dependency graphing: `shared.mcp_config` is imported by 64 files, so removing a name from it is the high-blast-radius part; the eight importers were found by a syntax-level scan, and `shared.mcp_health` has three existing production or test importers. Historical analysis: churn in 30 days is 14 for the checker, 10 for the discovery module and 8 for `context.py`; each source edit is a one-line import change except the discovery module. Operational dependency inspection: not applicable (no process, port or database change).
- Validation baseline: `radon cc` rates the checker's `main` C (18) and `check_removed_name_reintroduction` C (16), so the new rules go into separate functions and `main` only calls them; `scripts/agent/services/mcp_status.py` and `scripts/shared/tool_transport_invoker.py` already have C-rated methods that this Plan does not touch. `vulture scripts/ --min-confidence 80` reports 17 findings, none in the target files and all unrelated; `bandit` reports no issue on the targets; `lint-imports` reports six contracts kept; the MCP documentation consistency check and the compatibility checker pass. The diff-cover baseline was not run in planning because a full coverage run is too costly; the implementation phase runs it against the threshold of `rules/toolchain.md`.
- Decision (gate fixture, the issue's open question): one shared helper builds a green gate for every server key of the test context, used by the 65 call sites, rather than a permissive gate written per test. Alternative rejected: per-test gates, which repeat the same construction 65 times.
- Decision (checker detection): syntax-tree rules, because `check_compat_patterns` is line-based and misses multi-line imports and calls. The gate-less call is also caught at runtime by `TypeError`; the checker rule is kept as the issue requires, and the `TypeError` test guards the signature.
- Decision (order): tests first, then the signature flip, so every phase is independently revertable and leaves the suite green.
- Sibling `None` defaults of `RuntimeToolRegistry` and the discovery registry helper are left as is (UNK-02).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Move the Health imports and delete the re-export**
   - [ ] Re-run the repository-wide search for importers immediately before editing (REQ-001; read-only)
   - [ ] Change the imports in the four source files (REQ-001; `scripts/agent/services/mcp_status.py`, `scripts/agent/startup_reporter.py`, `scripts/agent/context.py`, `scripts/shared/tool_transport_invoker.py`)
   - [ ] Change the imports in the four test files (REQ-001; `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/integration/test_agent_mcp_integration.py`)
   - [ ] Delete the re-export and its `# noqa: F401` (REQ-002; `scripts/shared/mcp_config.py`)
   - [ ] Remove the "only re-exports" sentence (REQ-006; `docs/22_mcp/mcp_03_03_transport-and-health.md`)
2. **Phase 2: Require the posture gates**
   - [ ] Create the shared gate helper (REQ-004; `tests/agent/services/_discovery_gates.py`)
   - [ ] Pass gates at the 60, 2 and 2 gate-less calls and the integration calls (REQ-004; `tests/agent/services/test_mcp_tool_discovery.py`, `tests/integration/test_production_security_regression.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`)
   - [ ] Replace the `None`-behavior test with a `TypeError` test and keep the empty-gate test (REQ-004; `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`)
   - [ ] Make `posture_gates` required, remove the `None` branch and rewrite the docstrings (REQ-003; `scripts/agent/services/mcp_tool_discovery.py`)
3. **Phase 3: Add the checker rules**
   - [ ] Add the two syntax-tree rules in separate functions called from `main` (REQ-005; `tools/check_compat_shims.py`)
   - [ ] Add checker tests for both rules, including a multi-line import and a multi-line call (REQ-005; `tests/tools/test_check_compat_shims.py`)
   - [ ] Update the catalog entries (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the checks listed under Tests, confirm the production startup path is unchanged, and measure diff-cover (REQ-007; the Phase 1 to 3 files)
   - [ ] Deploy hand-off: because `scripts/` changes, hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision and has an approval gate (REQ-007; `scripts/agent/services/mcp_tool_discovery.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Phase 1 source and test files | Unit and integration tests after the import moves | `uv run pytest tests/shared tests/integration/test_agent_mcp_integration.py -v` | Pass; no importer through `shared.mcp_config` |
| `scripts/agent/services/mcp_tool_discovery.py` | Unit tests of the gate contract | `uv run pytest tests/agent/services -v` | Pass; `TypeError` for a gate-less call; empty gate registers nothing |
| Integration tests | Production-path regression | `uv run pytest tests/integration/test_production_security_regression.py -v` | Pass |
| `tools/check_compat_shims.py` | Unit tests of both rules and live run | `uv run pytest tests/tools/test_check_compat_shims.py -v`; `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` | Pass; rules report the offending samples |
| All changed scripts | Type, import-layer, lint, security | `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run ruff check`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new finding; six contracts kept |
| Changed document | Documentation checks | `check_docs_consistency.py --domain mcp`; `check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py --strict` | No finding |
| Whole change | Full suite and coverage | `uv run pytest`; diff-cover per `rules/toolchain.md` | Pass; at least 90 percent on changed lines |

## Risks
- **Risk**: Removing the re-export breaks a caller that the scan missed (`shared.mcp_config` is imported by 64 files) → **Mitigation**: Re-run the repository-wide search immediately before the deletion and stop if a caller outside the listed files appears; the deletion is one revertable step.
- **Risk**: The 65 test call sites need a gate that does not match each test's server set, changing what the tests assert → **Mitigation**: The helper builds a green gate for exactly the servers of each context, so every previously registered server stays allowed; run the discovery tests after each file.
- **Risk**: A required parameter breaks a caller outside the searched trees → **Mitigation**: The scan covered `scripts/`, `tests/` and `tools/`; `mypy` flags a missing required argument in `scripts/`, and the `TypeError` test guards the contract.
- **Risk**: The checker rules add complexity to a function already rated C (18) → **Mitigation**: Put each rule in its own function and keep `main` as a caller only.
- **Risk**: Concurrent edits to `tools/check_compat_shims.py` by the sibling issues conflict → **Mitigation**: Land the checker phases in sequence, this Plan first, and rebase before each.
- **Risk**: `scripts/shared/tool_transport_invoker.py`, `scripts/agent/context.py` and `tools/TOOL_DESCRIPTIONS.md` are edited by other work (4, 8 and 66 commits in 30 days) → **Mitigation**: Keep each edit to the import block or the catalog row and re-run the checks after any sync.
- **Risk**: The change is deployed without the user's approval → **Mitigation**: Phase 4 only hands off to the deploy skill after commit and push; the deploy skill's approval gate decides.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move the Health imports and delete the re-export | Pending | — | — | |
| 2 | Require the posture gates (helper, 65 call sites, signature flip) | Pending | — | — | |
| 3 | Add the checker rules, tests and catalog entries | Pending | — | — | |
| 4 | Deployment and verification | Pending | — | — | |

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
- **Generated at**: 20261027-110516
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/startup_reporter.py`, `scripts/agent/context.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/agent/services/mcp_tool_discovery.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/integration/test_agent_mcp_integration.py`, `tests/agent/services/_discovery_gates.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`, `tests/integration/test_production_security_regression.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `tools/check_compat_shims.py`, `tests/tools/test_check_compat_shims.py`, `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (move imports); Background (eight importers) | `scripts/agent/services/mcp_status.py` | Phase 1 | AC-1 | `uv run pytest tests/shared tests/agent/services -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `scripts/agent/startup_reporter.py` | Phase 1 | AC-1 | `uv run pytest tests/shared -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `scripts/agent/context.py` | Phase 1 | AC-1 | `uv run pytest tests/shared -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `scripts/shared/tool_transport_invoker.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_tool_transport_invoker.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `tests/shared/test_tool_executor.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_tool_executor.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `tests/shared/test_tool_executor_routing.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_tool_executor_routing.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `tests/shared/test_tool_transport_invoker.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_tool_transport_invoker.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes (move imports) | `tests/integration/test_agent_mcp_integration.py` | Phase 1 | AC-1 | `uv run pytest tests/integration/test_agent_mcp_integration.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes (remove the re-export) | `scripts/shared/mcp_config.py` | Phase 1 | AC-2 | `uv run pytest tests/shared/test_mcp_config.py -v`; `uv run mypy --no-namespace-packages scripts/` | Confirmed by repository evidence |
| REQ-003 | Required Changes (required `posture_gates`); Constraints | `scripts/agent/services/mcp_tool_discovery.py` | Phase 2 | AC-3 | `uv run pytest tests/agent/services -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (update tests; keep the empty-gate test) | `tests/agent/services/_discovery_gates.py` | Phase 2 | AC-4 | `uv run pytest tests/agent/services -v` | Derived from confirmed evidence |
| REQ-004 | Required Changes (60 call sites) | `tests/agent/services/test_mcp_tool_discovery.py` | Phase 2 | AC-4 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (`TypeError` test; keep empty-gate test) | `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Phase 2 | AC-5 | `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (call sites) | `tests/integration/test_production_security_regression.py` | Phase 2 | AC-4 | `uv run pytest tests/integration/test_production_security_regression.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes (call sites) | `tests/agent/services/test_runtime_tool_routing_integration.py` | Phase 2 | AC-4 | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes (checker rules) | `tools/check_compat_shims.py` | Phase 3 | AC-7 | `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` | Confirmed by repository evidence |
| REQ-005 | Required Changes (checker tests) | `tests/tools/test_check_compat_shims.py` | Phase 3 | AC-7 | `uv run pytest tests/tools/test_check_compat_shims.py -v` | Explicit in issue |
| REQ-005 | Testing Expectations (catalog sync) | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes (document sentence) | `docs/22_mcp/mcp_03_03_transport-and-health.md` | Phase 1 | AC-6 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-007 | Constraints; Acceptance Criteria; Testing Expectations | `scripts/agent/services/mcp_tool_discovery.py` | Phase 4 | AC-8 | Full suite; `lint-imports`; `mypy`; diff-cover | Explicit in issue |
