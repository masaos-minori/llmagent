## Goal
- Report configuration-only startup failures before any MCP subprocess is spawned: add a config-only validation stage to `StartupOrchestrator.run()` that runs before `_start_servers`, keep the runtime-dependent checks where they are, and preserve every existing FATAL, severity, message, and reporting path.

## Priority
Medium

## Scope
- **In-Scope**:
  - Split `StartupValidationPipeline.check_services` into a config-only stage (`mcp_auth`, `component_mandatoriness`, `routing_drift`, `routing_safety_tiers`) and the runtime stage (`readiness`, `mcp_tool_discovery`, `rag_consistency`).
  - Run the config-only stage in `StartupOrchestrator.run()` after component initialization and before `_start_servers`, reporting through the existing reporter with the same sources, severities, and fatal-abort format.
  - Tests for the order, the abort-before-spawn behavior, and the unchanged outcome of a valid configuration; update the existing tests whose harnesses drive the moved checks.
  - Documentation of the new order and of the boundary between config-only and runtime-dependent checks.
- **Out-of-Scope**:
  - Changing which checks exist, their logic, severity, or message formats.
  - The post-start health verification and readiness logic; parallelizing server startup.
  - Orphan handling in the lifecycle code (tracked by the separate orphan issue and its Plan).
  - Disabled-server handling inside `mcp_auth` (done by the separate disabled-auth Plan, which is applied first).
- **Dependencies**: The `mcp_auth` filter for disabled servers (Plan below) is applied first because both Plans touch the same function and the same tests. Related to the subprocess-orphan issue (id mcporphan001): this Plan shrinks the interruption window but does not fix the orphan; independent fix order.
  - **Depends on**: `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md` | phase all | both change `check_services`, its `mcp_auth` tests, and the same documentation bullet; apply the filter first, then move the check.

## Background
`StartupOrchestrator.run()` currently runs component initialization, `_start_servers`, `_verify_mcp_health`, `_check_services`, `_setup_prompt`, and rolls the servers back on a failure after the start. `check_routing_drift` reads `ctx.cfg.mcp.mcp_servers` and the static tool registry; `check_routing_safety_tiers` reads `ctx.cfg.approval` and the static registry; neither reads a server's runtime state. In strict mode a drift is FATAL; a safety-tier failure is always FATAL (checked in Step 2).

## Problem
A drifted routing entry or a missing safety tier aborts startup only after every subprocess server was spawned, polled for health one after another, verified, probed by readiness and discovery, and then rolled back. The same failure is detectable before any process exists (checked in Step 2; the order is explicit in `run()` and `check_services`).

Verification corrections to the Issue:
1. The Issue's second unresolved question is answered by the code: all four of `mcp_auth` (reads `ctx.cfg`), `_check_component_mandatoriness` (reads `ctx.cfg` and a registry file), `check_routing_drift`, and `check_routing_safety_tiers` need no running server. The mandatoriness check documents that it must run before tool discovery; running it earlier satisfies that.
2. `check_services` is not the straight line the Issue and the documentation describe: after the mandatoriness step it returns early when any FATAL exists, so today a readiness or `mcp_auth` FATAL skips discovery, drift, safety tiers, and RAG. The documentation claim that every check always runs and that all checks complete before the abort is therefore wrong, and the new stage report is the first place where all four config-only checks report together.
3. The Issue's ordering question has no counter-evidence: a search of `docs/10_adr/` for the startup-order terms finds no ADR requiring validation to be reported together after the services are up; ADR-004 lists `StartupOrchestrator.run()` only in its scope (checked in Step 2; ADR-004 Decision 14 is preserved because no severity changes).
4. Test blast radius is larger than the Issue's three test files: the `_run_check_services` harness is duplicated in `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup_validation.py`, and `tests/agent/test_startup_memory_failures.py`, and the `run()`-level tests in `tests/agent/test_startup_rollback.py` use a `MagicMock` context that would execute the new stage for real.

## Reason for Change
- Time: a config mistake costs the full sequential startup of every server before it is reported.
- Side effects: processes are launched and torn down for a run that cannot succeed, and the interruption window in which a subprocess can be left behind is opened for nothing.
- Fail-fast: validation that needs no running service precedes steps with external effects.

## Implementation Intent
Add a `check_config` stage to the validation pipeline and a matching orchestrator step, executed before the server start and outside the rollback window (nothing is spawned yet). The runtime stage keeps its current order and its guard that skips discovery after an earlier FATAL. A shared helper in the orchestrator displays a stage's outcomes and raises the existing `Startup validation failed` error, so both stages report identically.

## Requirements
- `REQ-001`: `StartupOrchestrator.run()` MUST execute a config-only validation stage after component initialization and before `_start_servers`; the stage MUST contain `mcp_auth`, `component_mandatoriness`, `routing_drift`, and `routing_safety_tiers`, and no check that needs a spawned process.
- `REQ-002`: A FATAL in the config-only stage MUST abort startup with the existing `RuntimeError("Startup validation failed: ...")` format before `_start_servers` is called; warnings and fatals of the stage MUST be displayed through the existing reporter; no rollback is required because nothing was started.
- `REQ-003`: The runtime stage MUST keep `readiness`, `mcp_tool_discovery`, and `rag_consistency` in their current order and MUST keep skipping discovery and RAG when an earlier runtime-stage FATAL exists; the mandatoriness gate MUST still run before tool discovery.
- `REQ-004`: Every FATAL that exists today MUST stay FATAL regardless of environment or profile; check logic, outcome sources, severities, and message formats MUST NOT change; the four config-only checks MUST all run and report together (no short-circuit among them).
- `REQ-005`: Tests MUST show that a strict routing drift aborts before `_start_servers`, a safety-tier failure aborts before any subprocess start, and a valid configuration runs both stages with an unchanged overall outcome; they MUST fail on the pre-change code and pass after it.
- `REQ-006`: Existing tests whose harness drives the moved checks MUST be re-pointed to the new stage, and the `run()`-level tests MUST stub the new stage so they keep isolating the step under test.
- `REQ-007`: Documentation MUST describe the new order (config-only validation before server start), the intent (fail before external effects), and the boundary between config-only and runtime-dependent checks, and MUST correct the statement that every check always runs.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Stage split | Add `StartupValidationPipeline.check_config` holding steps 1b, 3, 5, and 5b of `check_services`; remove them from `check_services`; keep the has-fatal guard before discovery (checked in Step 2) | REQ-001, REQ-003, REQ-004; AC-1, AC-3, AC-4 | `check_services` runs `mcp_auth`, readiness, `_check_component_mandatoriness` (then returns on any FATAL), discovery, drift, safety tiers, RAG in that order; the module is 11615 bytes, under the size gate (checked in Step 2) | `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py` | Verified |
| `scripts/agent/startup.py` | Orchestration | Add the config stage step and a shared display-and-raise helper; call the stage in `run()` after `ComponentInitializer.initialize()` and before the `try` that starts servers (checked in Step 2) | REQ-001, REQ-002; AC-1, AC-2 | `run()` starts servers inside `try`, rolls back on failure, and `_check_services` displays the pipeline then raises `Startup validation failed` on a FATAL (checked in Step 2) | `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup.py` | Verified |
| `tests/agent/test_startup_validation.py` | New stage tests, harness | Add `check_config` tests (drift strict, safety tier, valid config) with a harness that drives the real method; limit the existing harness to the runtime stage (checked in Step 2) | REQ-005, REQ-006; AC-2, AC-5 | The file drives the real `check_services()` body through `_run_check_services` and patches `check_routing_drift` and `check_routing_safety_tiers` (checked in Step 2) | `tests/agent/test_startup_validation.py` | Verified |
| `tests/agent/test_startup_rollback.py` | Order and rollback tests | Add run-order tests (config stage before `_start_servers`, abort without rollback); stub the new stage in the autouse fixture so existing `run()` tests keep their isolation (checked in Step 2) | REQ-005, REQ-006; AC-1, AC-2, AC-5 | Twelve `orch.run()` calls with `ctx = MagicMock()` and per-method stubs for `_start_servers`, `_check_services`, `_setup_prompt` only (checked in Step 2) | `tests/agent/test_startup_rollback.py` | Verified |
| `tests/agent/test_startup_severity_classification.py` | Re-point harness | Drive the moved checks (`mcp_auth`, drift, safety tiers, mandatoriness) through the new stage; keep the runtime-stage tests on `_check_services` (checked in Step 2) | REQ-006; AC-5 | The harness calls `startup._check_services()` and asserts drift, safety-tier, and `mcp_auth` outcomes (about 50 matching lines, rg, checked in Step 2) | `tests/agent/test_startup_severity_classification.py` | Verified |
| `tests/agent/test_startup.py` | Re-point duplicated harness | Same re-pointing for the duplicate severity block (checked in Step 2) | REQ-006; AC-5 | The file contains a duplicate `_run_check_services` harness and `mcp_auth` and drift tests (rg, checked in Step 2) | `tests/agent/test_startup.py` | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Startup order description | Describe config-only validation before server start, the intent, and the stage boundary; correct the "every check always runs" statement (checked in Step 2) | REQ-007; AC-6 | The design-intent section names two phases (start and health check) and the `mcp_auth` bullet claims no short-circuit (checked in Step 2) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/routing_drift.py` | Both checks read `ctx.cfg` and static registries only; strict drift raises `RuntimeError` | REQ-001, REQ-004 |
| `scripts/agent/startup_reporter.py` | `display_pipeline_results` shows warnings and fatals; `report_readiness` counts only readiness, discovery, and RAG sources, so it needs no change | REQ-002 |
| `scripts/agent/production_config_validator.py` | `validate_against_registry` reads configuration and a registry map only | REQ-001 |
| `scripts/agent/shared/health_models.py` | `StartupValidationResult` and `StartupCheckStatus` used by both stages | REQ-002 |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Drives `_check_services` through a mocked pipeline; stays valid because `_check_services` keeps its contract | REQ-006 |
| `tests/agent/test_startup_memory_failures.py` | Harness patches names that remain importable from `agent.startup_validation`; no change needed (checked in Step 3) | REQ-006 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Decision 14: safety failures stay unconditional; no ordering mandate found | REQ-004 |
| `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md` | Same function and tests; the filter lands first | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): a configuration that fails a config-only FATAL check never reaches `_start_servers`; the call order for a valid configuration is config stage, `_start_servers`, `_verify_mcp_health`, `_check_services`, `_setup_prompt`.
- AC-2 (REQ-002, REQ-005): a strict routing drift and a safety-tier failure each raise `Startup validation failed` before any subprocess start, with no `shutdown_all` call, and their warnings and fatals are displayed.
- AC-3 (REQ-003): the runtime stage still produces readiness, discovery, and RAG outcomes in the current order and still skips discovery after an earlier runtime FATAL.
- AC-4 (REQ-004): a valid configuration produces the same set of outcomes as before, in the defined order (config stage first); no check logic or message text differs.
- AC-5 (REQ-005, REQ-006): the new tests fail on the pre-change code and pass after it; the re-pointed and stubbed existing tests pass.
- AC-6 (REQ-007): the documentation matches the new order and the docs checkers report no findings, with no concrete timeouts or values copied.

## Tests
- `REQ-005`: in `tests/agent/test_startup_rollback.py`, a call-order test with mocked starter and validation components asserting the config stage precedes `_start_servers` and that a config FATAL leaves `_start_servers` uncalled and `shutdown_all` not awaited.
- `REQ-005`: in `tests/agent/test_startup_validation.py`, `check_config` tests for strict drift FATAL, safety-tier FATAL, non-strict drift WARNING shown, and a clean pass.
- `REQ-006`: re-point the severity harness in the two duplicate files; stub the new stage in the rollback fixture.
- Regression: `tests/agent/test_startup.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_reporter.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup_memory_failures.py`.

## Documentation Impact
Yes. REQ-007 drives an update of the startup and health document (located through `docs/00_index.md` "Document References by Task"): the order, the intent, and the boundary only; no concrete values.

## Assumptions
- All four moved checks are config-only: confirmed by reading their inputs (`ctx.cfg`, the static registry, the mandatoriness registry file) in Step 3.
- Running the stage after component initialization is sufficient; the Issue asks only for "before `start_servers`", and initialization is outside the rollback window today (checked in Step 3).
- The two-stage report is acceptable: the readiness summary counts only readiness, discovery, and RAG sources, so splitting outcomes across two pipeline objects changes no summary line (checked in Step 3).
- Step 8b overlap judgement (`tools/check_plan_target_overlaps.py`): `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md` shares `scripts/agent/startup_validation.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup_validation.py`, and the startup and health document. Judged a sequencing dependency, not a conflict: that Plan only adds the `is_disabled` filter to the `mcp_auth` comprehension and adjusts mocks, which this Plan then moves unchanged into `check_config`; it is recorded in Scope Dependencies as a `Depends on` line.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any ADR other than the ones searched requires validation outcomes to be reported together after services are up. | A search of `docs/10_adr/` for the order terms found none; the ADR index was not read line by line. | Implementer re-checks `docs/10_adr/adr_01_index.md` entries for startup validation; stop and report if an ADR requires the current order. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify | Medium: every agent startup passes through it | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/startup.py` | Modify | Medium: startup entry sequence | 9 | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_validation.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_rollback.py` | Modify | Medium: twelve `run()` callers | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_severity_classification.py` | Modify | Medium: about 50 matching lines | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup.py` | Modify | Medium: duplicated harness | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, which checks move. Alternatives: (a) only drift and safety tiers, as the Issue names; (b) all four config-only checks. Chosen: (b). `mcp_auth` and `component_mandatoriness` read the same configuration, abort after the same spawn work, and the mandatoriness gate already requires running before discovery. Cost: more test re-pointing (recorded under Risks). Compatibility: the sources, severities, and messages are unchanged.

Decision 2, where the stage runs. After `ComponentInitializer.initialize()` and outside the `try` that owns the rollback: nothing is spawned, so no rollback is needed and the existing rule that an initialize failure triggers no rollback is kept.

Decision 3, failure handling inside the stage. The four checks run and report together with no short-circuit among them; the abort happens once, after the stage, through the shared helper that displays outcomes and raises the existing error format. The runtime stage keeps its guard after readiness so discovery and RAG are skipped after an earlier runtime FATAL, exactly as today.

Compatibility impact: for an invalid configuration, the set and timing of reported outcomes changes (earlier, and drift and safety tiers are now reported even when readiness would have failed); this is the requested behavior and is documented. For a valid configuration the outcome set is unchanged apart from the order (config stage first).

No persisted schema, public API, or shared constant is changed; the `check_services` method keeps its name and return type, and `_check_services` keeps its contract.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the call-order and abort-before-spawn tests and the `check_config` tests, and record that they fail on the current code (REQ-005; `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_validation.py`).
2. **Phase 2: Pipeline split**
   - [ ] Add `check_config` and remove the moved steps from `check_services`, keeping the has-fatal guard before discovery (REQ-001, REQ-003, REQ-004; `scripts/agent/startup_validation.py`).
3. **Phase 3: Orchestrator wiring**
   - [ ] Add the config stage step and shared helper and call it before `_start_servers` (REQ-001, REQ-002; `scripts/agent/startup.py`).
4. **Phase 4: Existing tests**
   - [ ] Re-point the moved-check tests and stub the new stage in the rollback fixture (REQ-006; `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_validation.py`).
5. **Phase 5: Documentation**
   - [ ] Describe the new order, intent, and boundary and correct the no-short-circuit statement; run the docs checkers (REQ-007; `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`).
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` (REQ-001; `scripts/agent/startup.py`, `scripts/agent/startup_validation.py`).

### Release units
**Unit**: config-stage-split | **Phases**: 2, 3, 4 | **Reason**: removing the moved checks from `check_services` without the orchestrator call drops them from startup, and the re-pointed tests cannot pass until the new stage exists.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py`, `scripts/agent/startup_validation.py` | Unit with mocked starter and validation | `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup_validation.py -v` | New tests fail before Phase 2-3, pass after |
| Re-pointed harnesses | Unit | `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py tests/agent/test_startup_reporter.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_memory_failures.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture / size | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Reference tables | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Startup document | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `StartupOrchestrator._check_services` at B (6) in `startup.py`, and `StartupValidationPipeline.check_services` at D (25) in `startup_validation.py`, which the split reduces; `vulture` and `bandit` show no finding in the target files; the diff-cover number is recorded at implementation time.

## Risks
- **Risk**: Test blast radius: the moved checks are asserted in four duplicated harness files (about 115 matching lines across the three largest files) and twelve `run()` callers → **Mitigation**: the blast radius is recorded here per `rules/toolchain.md`; Phase 4 is a separate revertable step, and a test file not listed above that fails is reported through `tools/amend_plan.py`.
- **Risk**: A `run()`-level test with a `MagicMock` context executes the new stage for real and passes or fails for the wrong reason → **Mitigation**: stub the stage in the rollback fixture and assert it is called once in the order test.
- **Risk**: Outcome ordering or set changes for an invalid configuration is read as a regression → **Mitigation**: stated in Design and documentation; AC-4 pins the valid-configuration case.
- **Risk**: Overlap with the disabled-auth Plan in the same function and tests → **Mitigation**: the `Depends on` line sequences it; this Plan is rebased on the filter.
- **Risk**: A future config-only check is added to the runtime stage → **Mitigation**: the documentation states the boundary rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing order and stage tests | Pending | — | — | |
| 2 | Phase 2: split the validation pipeline | Pending | — | — | |
| 3 | Phase 3: wire the config stage in the orchestrator | Pending | — | — | |
| 4 | Phase 4: re-point and stub existing tests | Pending | — | — | |
| 5 | Phase 5: documentation update | Pending | — | — | |
| 6 | Phase 6: deployment hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261031-135634_validorder001_config-validation-after-spawn.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-095930
- **Related target files**: scripts/agent/startup_validation.py, scripts/agent/startup.py, tests/agent/test_startup_validation.py, tests/agent/test_startup_rollback.py, tests/agent/test_startup_severity_classification.py, tests/agent/test_startup.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Implementation Intent | scripts/agent/startup_validation.py | 2 | AC-1 | `check_config` tests | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1 | scripts/agent/startup.py | 3 | AC-1 | Call-order test | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; Constraints bullet 3 | scripts/agent/startup.py | 3 | AC-2 | Abort-before-spawn tests | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | scripts/agent/startup_validation.py | 2 | AC-3 | Runtime-stage regression tests | Explicit in issue |
| REQ-004 | Constraints bullets 1-2; Implementation Intent | scripts/agent/startup_validation.py | 2 | AC-4 | Valid-configuration outcome test | Explicit in issue |
| REQ-005 | Required Changes bullet 4 | tests/agent/test_startup_rollback.py | 1 | AC-1, AC-2, AC-5 | Call-order and abort tests | Explicit in issue |
| REQ-005 | Required Changes bullet 4 | tests/agent/test_startup_validation.py | 1 | AC-2, AC-5 | `check_config` tests | Explicit in issue |
| REQ-006 | Derived: duplicated harness found in Step 2 | tests/agent/test_startup_severity_classification.py | 4 | AC-5 | `tests/agent/test_startup_severity_classification.py` | Confirmed by repository evidence |
| REQ-006 | Derived: duplicated harness found in Step 2 | tests/agent/test_startup.py | 4 | AC-5 | `tests/agent/test_startup.py` | Confirmed by repository evidence |
| REQ-006 | Derived: `run()` tests with a mock context | tests/agent/test_startup_rollback.py | 4 | AC-5 | Rollback fixture stub | Derived from confirmed evidence |
| REQ-006 | Derived: harness limited to the runtime stage | tests/agent/test_startup_validation.py | 4 | AC-5 | `tests/agent/test_startup_validation.py` | Derived from confirmed evidence |
| REQ-007 | Documentation Impact | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | 5 | AC-6 | `tools/check_docs_*` | Explicit in issue |
