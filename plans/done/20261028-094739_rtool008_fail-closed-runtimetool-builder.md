## Goal
- Make the production `RuntimeTool` builder fail closed on missing execution metadata, keep the permissive defaults only in a test-side builder that production modules cannot import, and correct the stale module documentation.

## Priority
Medium

## Scope
- **In-Scope**:
  - Require `is_write`, `requires_serial`, `resource_scope_kind` and `resource_scope_keys` in `build_runtime_tool()` and reject an explicit `None`.
  - Add a fixture builder under `tests/` that keeps today's permissive defaults by delegating to the strict builder.
  - Move the test call sites that rely on the defaults to the fixture builder.
  - Add a guard test that no module under `scripts/` imports the fixture builder.
  - Correct the `runtime_tool.py` module docstring and the one doc sentence about safe defaults.
- **Out-of-Scope**: legacy `resource_scope` handling and validator responsibility (mcpcompat003); the Schema 2.0 required field list; registry and routing changes; discovery validation behavior; requiring an explicit `agent_safety_tier` (UNK-02); an explicit "unknown" write state (UNK-01).
- **Dependencies**: `plans/done/20261027-121337_mcpcompat003_align-legacy-resource-scope.md` lists `scripts/shared/runtime_tool.py` only as a read-only reference ("defaults remain untouched") and modifies the validator and fetch layer; its implementation procedures (for example `implementations/20261028-065435_02_scripts_agent_services_mcp_tool_discovery_fetch.py.md`) are still `Pending` and touch none of this Plan's targets, so no ordering is needed. `plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md` also edits `tests/shared/test_runtime_tool_registry.py` (judged compatible in Assumptions).

## Background
`build_runtime_tool()` in `scripts/shared/runtime_tool.py` resolves a missing `is_write` to `False`, sets `requires_serial` to `True` when `is_write` was omitted, and defaults the safety tier to `WRITE_DANGEROUS`. Its single production caller, `_build_runtime_tools()` in `scripts/agent/services/mcp_tool_discovery_registry.py`, passes `is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`, `enabled_for_llm`, `capabilities` and the other discovered fields by keyword. Discovery rejects an entry that lacks the four Schema 2.0 fields before building (`_REQUIRED_SCHEMA_V2_FIELDS` in `mcp_tool_discovery_fetch.py`).

## Problem
Any future direct caller that omits `is_write` gets a tool recorded as read-only although its write behavior is unknown, and read/write classification drives approval, scheduling and policy. The module docstring still calls the registry future work with "no consumer yet", although the registry and discovery are active.

## Reason for Change
No production path hits the default today, so the risk is latent: a refactor of discovery validation could register an unclassified tool as read-only. The priority is Medium (safety default, no demonstrated misclassification).

## Implementation Intent
The production builder requires the metadata that discovery already validates and raises when it is missing. A clearly named test-side builder keeps the permissive defaults for fixtures and is not importable from production modules. Conservative defaults for fields that are not safety-classifying inputs or that are already fail-closed (safety tier, LLM visibility) stay.

## Requirements
- `REQ-001`: `build_runtime_tool()` takes `is_write`, `requires_serial`, `resource_scope_kind` and `resource_scope_keys` as required keyword arguments; omitting one raises `TypeError` and passing `None` raises `ValueError`; the `requires_serial`-follows-`is_write` default and the `is_write=False` default are removed; field names and meanings of `RuntimeTool` are unchanged.
- `REQ-002`: A fixture builder `build_fixture_runtime_tool()` in `tests/shared/runtime_tool_factory.py` reproduces today's permissive behavior (`is_write=False`, `requires_serial=True` when `is_write` is omitted, empty scope) by delegating to the strict builder, so it cannot drift from the real constructor.
- `REQ-003`: The 103 test call sites that rely on at least one removed default move to the fixture builder; the five test files whose calls already pass every required field are not changed.
- `REQ-004`: A guard test fails if any module under `scripts/` imports `tests.shared.runtime_tool_factory` or the fixture builder name.
- `REQ-005`: Tests show the production builder rejects each missing or `None` required field and that discovery still builds tools from validated entries (existing discovery tests stay green unchanged).
- `REQ-006`: The `runtime_tool.py` module docstring and the safe-defaults sentence in the shared types doc describe the current behavior: the registry consumes `RuntimeTool`, the four fields are required, and the remaining defaults are conservative.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/runtime_tool.py` | Production builder | Require the four metadata arguments, reject `None`, drop the permissive defaults, correct the module docstring | REQ-001, REQ-006 / AC-1, AC-5 | `is_write: bool \| None = None` resolved with `_or_default(is_write, False)`; `requires_serial` resolved with `_or_default(requires_serial, is_write is None)`; module docstring says "a future `RuntimeToolRegistry`" and "no consumer yet" (checked in Step 3) | `tests/shared/test_runtime_tool.py` | Verified |
| `tests/shared/runtime_tool_factory.py` | Fixture builder (new file) | New file: permissive test builder delegating to the strict builder | REQ-002 / AC-2 | New file; the containing directory `tests/shared/` exists and holds shared test helpers' tests (checked in Step 3) | `tests/shared/test_runtime_tool.py` | Verified |
| `tests/shared/test_runtime_tool.py` | Builder tests | Add strict-builder rejection tests and the import guard test; move default-reliant calls to the fixture builder | REQ-003, REQ-004, REQ-005 / AC-1, AC-3, AC-4 | 20 `build_runtime_tool` calls, 19 of which omit a required field (checked in Step 3) | itself | Verified |
| `tests/shared/test_runtime_tool_registry.py` | Registry tests | Move default-reliant calls to the fixture builder | REQ-003 / AC-3 | 51 calls, 50 of which omit a required field (checked in Step 3) | itself | Verified |
| `tests/shared/test_tool_routing_validation.py` | Routing validation tests | Move default-reliant calls to the fixture builder | REQ-003 / AC-3 | 30 calls, 29 of which omit a required field (checked in Step 3) | itself | Verified |
| `tests/agent/services/test_config_reload.py` | Config reload tests | Move default-reliant calls to the fixture builder | REQ-003 / AC-3 | 2 calls, both omit a required field (checked in Step 3) | itself | Verified |
| `tests/integration/test_production_security_regression.py` | Security regression test | Move default-reliant calls to the fixture builder | REQ-003 / AC-3 | 2 calls, both omit a required field (checked in Step 3) | itself | Verified |
| `tests/shared/test_resource_scope.py` | Resource scope tests | Move the default-reliant call to the fixture builder | REQ-003 / AC-3 | 1 call that omits a required field (checked in Step 3) | itself | Verified |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Shared types doc | Replace the "applies safe defaults to unspecified annotation fields" sentence | REQ-006 / AC-5 | Section 7c states `build_runtime_tool()` applies safe defaults to unspecified annotation fields (checked in Step 3) | `tools/check_docs_consistency.py --domain shared` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/mcp_tool_discovery_registry.py` | The single production caller; passes the four fields by keyword, so no change is needed | REQ-001 |
| `scripts/agent/services/mcp_tool_discovery_fetch.py` | `_REQUIRED_SCHEMA_V2_FIELDS` proves discovery rejects an entry missing the four fields before building | REQ-001, REQ-005 |
| `scripts/agent/services/mcp_tool_discovery.py` | Documents building through `build_runtime_tool()`; no change needed | REQ-005 |
| `tests/agent/services/test_mcp_tool_discovery.py` | Regression for discovery building tools from validated entries; not edited | REQ-005 |
| `tests/shared/test_tool_executor.py` | Calls the builder with every required field; not edited | REQ-003 |
| `tests/shared/test_tool_executor_routing.py` | Calls the builder with every required field; not edited | REQ-003 |
| `tests/shared/test_route_resolver.py` | Calls the builder with every required field; not edited | REQ-003 |
| `tests/shared/test_rag_tools_consistency.py` | Calls the builder with every required field; not edited | REQ-003 |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Calls the builder with every required field; not edited | REQ-003 |
| `.importlinter` | Contracts cover `scripts/` packages only, so the guard is a test, not a contract | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): Calling `build_runtime_tool()` without one of the four fields raises `TypeError`, and passing `None` raises `ValueError`; discovery still builds tools from validated entries.
- AC-2 (REQ-002): The fixture builder returns a `RuntimeTool` equal to what the old permissive builder returned for the same arguments.
- AC-3 (REQ-003): All 103 default-reliant test calls use the fixture builder and the affected test files pass unchanged in assertions.
- AC-4 (REQ-004): The guard test passes and fails when a `scripts/` module imports the fixture builder.
- AC-5 (REQ-006): The module docstring and the shared types doc match the current architecture.

## Tests
- Strict builder: each of the four required fields missing, each passed as `None` (REQ-001, REQ-005).
- Fixture builder: equality with the previous default behavior for omitted `is_write`, explicit `is_write=True`, and omitted scope (REQ-002).
- Guard: AST scan of `scripts/**/*.py` for imports of the fixture module (REQ-004).
- Regression: `tests/agent/services/test_mcp_tool_discovery.py` and the registry and routing tests (REQ-003, REQ-005).
- Run `uv run pytest tests/shared tests/agent/services tests/integration -q`, mypy, ruff, `PYTHONPATH=scripts uv run lint-imports`.

## Documentation Impact
Yes, small (REQ-006): the shared types doc under `docs/40_shared/` found through `docs/00_index.md` "Document References by Task". State current behavior only.

## Assumptions
- Requiring only the four fields that discovery already validates is sufficient for "no production path can register an unclassified tool as read-only"; the safety tier already defaults to the most conservative value (`WRITE_DANGEROUS`) and the production caller passes `enabled_for_llm` explicitly, so those two stay as they are (UNK-02).
- A fixture builder that delegates to the strict builder keeps the test semantics unchanged while the production builder cannot regain a permissive path.
- Placing the fixture builder under `tests/` keeps it out of production imports: `.importlinter` contracts do not cover `tests/`, so a guard test enforces it instead.
- Overlap judgment (compatible): `plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md` also targets `tests/shared/test_runtime_tool_registry.py`; it adds exclusion-reason tests and changes executor construction, while this Plan only changes which builder the existing calls use.
- Pre-existing helper layout: `tests/shared/` has no `__init__.py`, and `tests/` is a regular package; the new module is importable as `tests.shared.runtime_tool_factory` the way other test helpers are (the procedure confirms this before the move).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether "unknown" write state should be an explicit value instead of failing construction | Design decision recorded as `Needs confirmation` in the Issue | Plan default: fail construction and keep the permissive path only in the fixture builder; the owner may request an explicit unknown state in a follow-up Issue | False |
| UNK-02 | Whether the production builder should also require `agent_safety_tier` and `enabled_for_llm` | Discovery does not supply a safety tier today and the Issue forbids changing discovery validation | Keep the conservative defaults; file a follow-up Issue if the owner wants discovery to supply the tier | False |
| UNK-03 | Whether `tests.shared.runtime_tool_factory` imports cleanly across test directories (`tests/shared/` has no `__init__.py`) | Not exercised yet | Verify with one import from `tests/agent/services` and `tests/integration` before moving the call sites; if it fails, add the helper to `tests/conftest.py`'s import path or use a `tests/shared/__init__.py` row in an amended Plan | False |
| UNK-04 | Owner confirmation of the fixture-builder shape before the 103 call sites move (the Issue asks to propose it first when many tests depend on the defaults) | 103 of 115 test calls rely on a default, which meets the "many" condition | Review of this Plan is the proposal; the procedure's first step creates the fixture builder with no call-site changes so it can be reviewed alone | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/runtime_tool.py` | Modify | Medium | 0 | N/A | not applicable (rsynced) |
| `tests/shared/runtime_tool_factory.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_runtime_tool.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_runtime_tool_registry.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_routing_validation.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_config_reload.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_production_security_regression.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_resource_scope.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (more than 3 files; changes a shared public builder signature). `shared` is a leaf package and `runtime_tool.py` imports only the standard library, so no import changes; `lint-imports` kept all 6 contracts earlier in this batch and is re-run after the change. Callers: one production call site and 11 test files (115 calls) found by `rg` and an AST count; `radon cc` reports no function at B or above in the module.
- Decision 1, strictness: required keyword arguments (no defaults) for the four fields, so a missing field is a `TypeError` from Python itself and an explicit `None` is a `ValueError` from one check; this avoids a second "missing" sentinel.
- Decision 2, fixture builder: lives in `tests/shared/runtime_tool_factory.py` and calls `build_runtime_tool()` with the old defaults filled in; it takes the same keyword names, so migrating a call site is a one-name change plus an import.
- Decision 3, enforcement: a pytest AST guard rather than an import-linter contract, because the contracts cover `scripts/` only and a `tests` root package would pull the whole suite into the contract graph.
- Decision 4, discovery: unchanged. The production caller already passes the four fields by keyword, so the strict signature needs no edit there.
- Compatibility: `RuntimeTool` fields and meanings are unchanged; only the builder's call contract changes.

## Implementation steps
1. **Phase 1: Fixture builder first**
   - [ ] Create the fixture builder as a thin wrapper over the current builder and add its equivalence tests, with no call-site or production change (REQ-002; `tests/shared/runtime_tool_factory.py`, `tests/shared/test_runtime_tool.py`)
   - [ ] Confirm the helper imports from `tests/agent/services` and `tests/integration` (UNK-03; `tests/shared/runtime_tool_factory.py`)
2. **Phase 2: Move the call sites**
   - [ ] Move the default-reliant calls to the fixture builder (REQ-003; `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`, `tests/shared/test_runtime_tool.py`, `tests/agent/services/test_config_reload.py`, `tests/integration/test_production_security_regression.py`, `tests/shared/test_resource_scope.py`)
3. **Phase 3: Strict production builder**
   - [ ] Add the strict-builder rejection tests and the import guard test, confirm they fail on the permissive builder, then make the four fields required and update the docstring (REQ-001, REQ-004, REQ-005, REQ-006; `scripts/shared/runtime_tool.py`, `tests/shared/test_runtime_tool.py`)
4. **Phase 4: Documentation**
   - [ ] Align the safe-defaults sentence (REQ-006; `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because `scripts/shared/` changes; confirm agent startup discovery still reports `mcp_tool_discovery` OK (REQ-001; `scripts/shared/runtime_tool.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/runtime_tool.py` | Unit | `uv run pytest tests/shared/test_runtime_tool.py -q` | Strict rejection and guard tests pass; fail on the permissive builder |
| Migrated call sites | Regression | `uv run pytest tests/shared tests/agent/services tests/integration -q` | All pass with unchanged assertions |
| Discovery | Regression | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | Passes unchanged |
| Architecture | Import contracts | `PYTHONPATH=scripts uv run lint-imports` | All contracts kept |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/shared -c pyproject.toml` | Clean |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain shared` | No errors |

Baseline recorded in Step 5: `radon cc` reports no function at B or above in `runtime_tool.py`; `vulture scripts/ --min-confidence 80` earlier in this batch listed no finding in `scripts/shared/runtime_tool.py`; `bandit -r scripts/` reported no Medium or High finding.

## Risks
- **Risk**: A missed test call site fails after the strict signature lands → **Mitigation**: move the call sites before the production change and run the full affected suites between phases; the AST count lists the 103 sites.
- **Risk**: A future test imports the strict builder with omitted fields → **Mitigation**: the `TypeError` fails loudly at test collection or run time; the fixture builder is the documented path.
- **Risk**: The fixture builder is imported from production by mistake → **Mitigation**: the guard test scans `scripts/` for the import.
- **Risk**: The helper module is not importable across the test directories → **Mitigation**: UNK-03 check in Phase 1 before moving any call site.
- **Risk**: Two Plans edit `test_runtime_tool_registry.py` → **Mitigation**: the edits are independent; implement in sequence and rebase.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the fixture builder and confirm cross-directory import | Completed | — | 2026-10-28 | rows 02+03 landed; factory in tests/shared/runtime_tool_factory.py; guard test added |
| 2 | Move the 103 default-reliant test calls to the fixture builder | Completed | — | 2026-10-28 | 109 omissions across 7 files migrated (04:56, 05:29, 06:2, 07:2, 08:1, 03:19, factory); recount vs 103 baseline |
| 3 | Make the production builder strict, add rejection and guard tests | Completed | — | 2026-10-28 | row 01 landed: strict signature + ValueError checks; full suite 10404 passed; diff-cover 100% |
| 4 | Align the shared types doc | Completed | — | 2026-10-28 | row 09 landed; docs checkers clean |
| 5 | Deployment and verification hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-120306_01_scripts_shared_runtime_tool.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-120306_02_tests_shared_runtime_tool_factory.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-120306_03_tests_shared_test_runtime_tool.py.md | 1,3 | Procedure | Pending | — | — |
| implementations/20261028-120306_04_tests_shared_test_runtime_tool_registry.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120306_05_tests_shared_test_tool_routing_validation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120306_06_tests_agent_services_test_config_reload.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120306_07_tests_integration_test_production_security_regression.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120306_08_tests_shared_test_resource_scope.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-120306_09_docs_40_shared_shared_02_02_types_and_protocols-tool-and-execution-dto.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-094739
- **Related target files**: `scripts/shared/runtime_tool.py`, `tests/shared/runtime_tool_factory.py`, `tests/shared/test_runtime_tool.py`, `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`, `tests/agent/services/test_config_reload.py`, `tests/integration/test_production_security_regression.py`, `tests/shared/test_resource_scope.py`, `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 2; builder resolves a missing `is_write` to `False` | `scripts/shared/runtime_tool.py` | Step 3 | AC-1 | `tests/shared/test_runtime_tool.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 2 | `tests/shared/test_runtime_tool.py` | Step 3 | AC-1 | `uv run pytest tests/shared/test_runtime_tool.py -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; 103 of 115 test calls rely on a default | `tests/shared/runtime_tool_factory.py` | Step 1 | AC-2 | `tests/shared/test_runtime_tool.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/shared/test_runtime_tool_registry.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/shared/test_tool_routing_validation.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/shared/test_runtime_tool.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/agent/services/test_config_reload.py` | Step 2 | AC-3 | `uv run pytest tests/agent/services -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/integration/test_production_security_regression.py` | Step 2 | AC-3 | `uv run pytest tests/integration -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 and 3 | `tests/shared/test_resource_scope.py` | Step 2 | AC-3 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; Acceptance Criteria 2 (production modules do not import the fixture builder) | `tests/shared/test_runtime_tool.py` | Step 3 | AC-4 | `uv run pytest tests/shared/test_runtime_tool.py -q` | Explicit in issue |
| REQ-005 | Testing Expectations 1; discovery validates before building | `tests/shared/test_runtime_tool.py` | Step 3 | AC-1 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | Confirmed by repository evidence |
| REQ-006 | Required Changes 4; module docstring names a future registry | `scripts/shared/runtime_tool.py` | Step 3 | AC-5 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact | `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Step 4 | AC-5 | `tools/check_docs_consistency.py --domain shared` | Explicit in issue |