## Goal
- Probe each MCP server's security posture once per startup and give tool discovery the same observation that readiness classified, so that the gate a server earns at readiness is the gate its tools run under, as ADR-003 and the `allowed_server_keys` contract already state.

## Priority
Medium

## Scope
- **In-Scope**: an optional pre-collected `gates` argument on `check_service_health` and `check_readiness`; `StartupValidationPipeline.check_services` collecting the gates once and passing them to both readiness and discovery; correcting the stale comment above the discovery step; tests for single probing and gate identity; one documentation sentence.
- **Out-of-Scope**: posture classification, failure classes, fatal and non-fatal rules and messages; runtime re-probing (restarts, per-call health checks); the tool discovery logic; `HealthCheckResult`'s shape (it stays unchanged).
- **Dependencies**: related, not blocking: `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md` and `issues/20261115-214906_startrev006_rag-check-timeout-executor.md` both edit `StartupValidationPipeline.check_services`, a different part of the method each; implement this Plan first because it is the smallest and changes the head of the method.

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214905_startrev005_posture-probed-twice-startup.md`).
- `check_readiness` calls `check_service_health`, which calls `collect_server_postures(ctx)` at its end to build the gates it classifies. `StartupValidationPipeline.check_services` then calls `collect_server_postures(ctx)` again before `McpToolDiscoveryService(ctx, posture_gates=...)` (Explicit in code, read in Step 3).
- The `allowed_server_keys` docstring states that no consumer re-probes `/health` and that the gate a server earned at readiness is the gate its tools run under. ADR-003 Decision Detail 16 (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`) states the exclusion is computed once at startup from the posture each server publishes and is not re-evaluated until the process restarts. Both contradict the two-probe code (Step 2).
- The comment above the second probe says the discovery step runs after a posture error makes `check_readiness` raise. That is false: `check_services` records the raised error as a fatal and returns before discovery whenever `pipeline.has_fatal`, so discovery never runs on that path.
- `collect_server_postures` probes servers one after another, so each probe round is a sequential round trip per usable HTTP server; two rounds double the startup cost.
- The Issue named `tests/agent/services` for the readiness tests. Correction found in Step 3: the readiness and posture tests are `tests/agent/test_mcp_health_posture.py` (`check_readiness`, `check_service_health`, `collect_server_postures`) and the pipeline tests are `tests/agent/shared/test_startup_validation_pipeline.py`; seven test files patch `check_readiness`, and only `tests/agent/test_startup_validation.py` also patches `collect_server_postures`.

## Problem
Two independent probes can disagree. A server that is green at readiness and not green at the second probe loses its tools with no readiness fatal naming it; a server that was a non-fatal warning at readiness and green the second time gains tools under a gate readiness never approved. The cost is doubled, and the stale comment describes a path that does not exist.

## Reason for Change
The posture gate is a security control; its decision and its use should come from one observation, and two documents already say they do. The window is small and the failure mode is mostly loss of tools, so the change is Medium, not High.

## Implementation Intent
Collect the gates once, at the start of the readiness stage of `check_services`, inside the same exception boundary that already turns a readiness failure into a pipeline fatal. Pass them to `check_readiness`, which passes them to `check_service_health`; each takes an optional keyword `gates` and probes by itself only when it is not given, so any other caller and every existing test keep working. Discovery then receives the same gates object. A readiness failure still returns before discovery, as today. Remove the stale comment and state the one-observation rule in its place. Classification, messages and `HealthCheckResult` are not touched.

## Requirements
- `REQ-001`: A startup run probes each usable MCP server's posture exactly once.
- `REQ-002`: Tool discovery receives the gates computed for readiness (the same objects), not a second probe's result.
- `REQ-003`: Readiness classification, remediation text, log messages and the raising behavior of `check_readiness` are unchanged, and a call without `gates` still probes by itself.
- `REQ-004`: The stale comment above the discovery step is replaced by an accurate statement.
- `REQ-005`: Tests count probes per startup, assert gate identity from readiness to discovery, and cover the new optional argument.
- `REQ-006`: The startup health document states that posture is observed once per startup and that discovery uses that observation.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/services/mcp_health.py | Accept pre-collected gates | Add an optional keyword `gates` to `check_service_health` and `check_readiness`; use it instead of calling `collect_server_postures` when given | REQ-001, REQ-003; AC-1, AC-3 | `check_service_health` at line 285 calls `collect_server_postures(ctx)` at line 324; `check_readiness` at line 338 calls `check_service_health(ctx)` at line 346; radon C (11) for `check_service_health` (checked in Step 3 and Step 5) | `tests/agent/test_mcp_health_posture.py` | Verified |
| scripts/agent/startup_validation.py | Probe once and share the result | In `check_services`, collect the gates once inside the readiness try block, pass them to `check_readiness`, reuse them for `McpToolDiscoveryService(..., posture_gates=...)`, delete the second `collect_server_postures` call and replace the stale comment | REQ-001, REQ-002, REQ-004; AC-1, AC-2, AC-4 | `check_services` at line 161: readiness at line 172, early return at lines 183-184, second `collect_server_postures` at line 195, stale comment at lines 187-193; radon C (17) (checked in Step 3 and Step 5) | `tests/agent/shared/test_startup_validation_pipeline.py` | Verified |
| tests/agent/shared/test_startup_validation_pipeline.py | Pipeline-level tests | Add tests with a counting fake for `collect_server_postures`: exactly one call per `check_services` run; discovery is constructed with the same gate objects that `check_readiness` received; a readiness failure returns before discovery and without a second probe | REQ-001, REQ-002, REQ-005; AC-1, AC-2, AC-5 | The file patches `f"{MODULE}.check_readiness"` and `McpToolDiscoveryService` in its tests (lines 116, 157, 270, 305, 345, 390, 427) and never patches `collect_server_postures` (checked in Step 3) | tests/agent/shared/test_startup_validation_pipeline.py | Verified |
| tests/agent/test_mcp_health_posture.py | Optional-argument tests | Add tests: `check_service_health(ctx, gates=...)` and `check_readiness(ctx, gates=...)` do not probe and classify the given gates identically to a probed run; without `gates` they probe once | REQ-003, REQ-005; AC-3, AC-5 | The file imports `check_readiness`, `check_service_health` and `collect_server_postures` and tests their classification (lines 4-27) (checked in Step 3) | tests/agent/test_mcp_health_posture.py | Verified |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | State the one-observation rule | In the `readiness` description (line 75), add that each MCP server's posture is observed once per startup and that tool discovery uses that observation | REQ-006; AC-6 | Line 75 says `readiness` covers required-service availability and every MCP server's Security Posture gate and does not say how often posture is observed (checked in Step 3) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/services/mcp_tool_discovery.py | Consumes `posture_gates` through `allowed_server_keys`; confirms discovery needs only the mapping | REQ-002 |
| scripts/agent/shared/health_models.py | `HealthCheckResult` stays unchanged; its frozen shape explains why the gates travel as an argument | REQ-003 |
| docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md | Decision Detail 16 states posture is computed once at startup; the change makes the code match it | REQ-001, REQ-006 |
| tests/agent/test_startup_validation.py | The one other test file that patches `collect_server_postures`; it must keep passing | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): A `check_services` run calls `collect_server_postures` exactly once, and `check_service_health` makes no probe of its own when given `gates`.
- AC-2 (REQ-002): `McpToolDiscoveryService` is constructed with the same gate objects that `check_readiness` received.
- AC-3 (REQ-003): For the same gates, the readiness warnings, errors, remediation text and the `RuntimeError` on a required-service or fatal-posture failure are identical to a probed run; a call without `gates` probes by itself and behaves as before.
- AC-4 (REQ-004): The stale comment is gone and the comment now states the one-observation rule.
- AC-5 (REQ-005): `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_mcp_health_posture.py tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_repl_health.py` passes with the new cases, and the single-probe test fails against the pre-change code.
- AC-6 (REQ-006): The startup health document states the once-per-startup observation; `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` pass.
- AC-7 (REQ-001, REQ-002, REQ-003): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: a counting fake for `collect_server_postures` patched in the pipeline module; one `check_services` run increments it once.
- REQ-002: a patched `McpToolDiscoveryService` records `posture_gates`; assert identity with the object passed to the patched `check_readiness`.
- REQ-003: classification tests in `test_mcp_health_posture.py` run once with probed gates and once with the same gates passed in; results are equal; the no-`gates` call still probes once.
- REQ-004, REQ-006: documentation checks listed under AC-4 and AC-6.
- REQ-005: write the single-probe test first and confirm it fails on the current code.

## Documentation Impact
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` must be updated (REQ-006) with one sentence on the once-per-startup observation and its use by discovery. Policy only: no counts, timeouts or file lists (`skills/DESIGN.md` Docs content policy). `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` describes the pre-bind gate and needs no change.

## Assumptions
- Collecting the gates before the LLM and embed probes is behavior-neutral: `check_service_health` builds its errors list in the order llm, embed, then postures from the gates it is given, so the classification and message order do not change; falsifiable by the identical-classification test.
- Tests that patch `check_readiness` without `collect_server_postures` stay valid: those tests already reach the real `collect_server_postures` in the discovery step today (only one of seven files patches it), so moving the call earlier adds no new kind of probe. Any test file found to need a patch is fallout under `rules/workflow-lifecycle.md` Plan Amendment Approval Classes.
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports no finding that names this Plan; none of its five target files is a target of another Frozen Plan at the time of freezing. The sibling issues 004 and 006 are not yet Plans; they are covered by UNK-01.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Order against `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md` and `issues/20261115-214906_startrev006_rag-check-timeout-executor.md`, which also edit `StartupValidationPipeline.check_services` (open sibling issues, related, not blocking) | Merge order of three edits to one method | Implement this Plan first; the two later Plans record the overlap at their own freeze: `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md`, `issues/20261115-214906_startrev006_rag-check-timeout-executor.md` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/services/mcp_health.py | Modify | Medium: `check_readiness` is the startup readiness gate; the new keyword is optional and its default keeps current behavior | 3 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_validation.py | Modify | Medium: every agent startup passes through `check_services`; the change reorders one probe and removes another | 10 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/shared/test_startup_validation_pipeline.py | Modify | Low: tests only | 3 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_mcp_health_posture.py | Modify | Low: tests only | 4 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Modify | Low: one sentence of one design document | 17 | High: one author | not applicable (rsynced): `docs/` is not deployed |

## Design
- **Design decision (how the gates travel)**: options weighed. (1) Add the gates to `HealthCheckResult`: rejected, `PostureGate` lives in `agent.services.mcp_health` while `HealthCheckResult` is in `agent.shared.health_models`, and the lower package must not import the higher one; typing the field loosely would lose the type. (2) Make `check_readiness` return a pair: rejected, it changes the return type for every patched call in seven test files. (3) Collect once in the pipeline and pass the gates down through an optional keyword: chosen. Compatibility impact: none for callers that do not pass `gates`; the pipeline's two probes become one.
- **Failure path**: the collection sits inside the readiness `try`, so an exception still becomes the `readiness` fatal and still returns before discovery; the early return on a fatal is unchanged. If the gates were ever unavailable at the discovery step, discovery must fail closed (no allowed servers), never fall back to an unprobed default.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `startup_validation.py` already imports `check_readiness` and `collect_server_postures` from `agent.services.mcp_health`; no new import (checked in Step 5).
- **Dependency graph**: `check_service_health` is called only by `check_readiness`; `check_readiness` is called only by `StartupValidationPipeline.check_services`; `collect_server_postures` has two callers today, both removed or merged into one by this change (checked in Step 3).
- **Historical analysis**: `startup_validation.py` 10 commits, `mcp_health.py` 3 commits and `agent_10_01` 17 commits in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: the change touches no port, database or service, and only reduces HTTP probes; no deploy-time lock to check (checked in Step 5).
- **Validation quality baseline**: radon: `check_service_health` C (11) and `check_services` C (17) today; the change moves one call and removes one, so no increase is expected; vulture and bandit: no finding in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Readiness accepts gates**
   - [ ] Write the optional-argument tests first and confirm they fail before the change (REQ-003, REQ-005; tests/agent/test_mcp_health_posture.py)
   - [ ] Add the optional `gates` keyword to `check_service_health` and `check_readiness` (REQ-001, REQ-003; scripts/agent/services/mcp_health.py)
2. **Phase 2: Pipeline probes once**
   - [ ] Write the single-probe and gate-identity tests first and confirm the single-probe test fails on the current code (REQ-001, REQ-002, REQ-005; tests/agent/shared/test_startup_validation_pipeline.py)
   - [ ] Collect the gates once in the readiness `try`, pass them to readiness and discovery, delete the second probe and replace the stale comment (REQ-001, REQ-002, REQ-004; scripts/agent/startup_validation.py)
3. **Phase 3: Documentation**
   - [ ] Add the once-per-startup observation to the readiness description (REQ-006; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
4. **Phase 4: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002, REQ-003; scripts/agent/services/mcp_health.py, scripts/agent/startup_validation.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/mcp_health.py | Unit | `uv run pytest tests/agent/test_mcp_health_posture.py -q` | New optional-argument cases pass; existing posture tests pass |
| scripts/agent/startup_validation.py | Unit | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_validation.py -q` | One probe per run; gate identity holds; existing pipeline tests pass |
| Startup callers of the readiness stage | Unit | `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py tests/agent/test_startup_memory_failures.py tests/agent/test_repl_health.py tests/agent/test_failure_handling_policy_cross_cutting.py -q` | All pass with no new real probe |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | No module over its limit; no drift |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Documentation | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_content_policy.py` | No findings |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: A test that patches `check_readiness` to raise now also runs the real `collect_server_postures` earlier (likelihood low) → **Mitigation**: those tests already reach it in the discovery step; the validation plan runs all seven files; any file needing a patch is fallout reported at implementation time.
- **Risk**: Moving the probe before the LLM and embed health checks changes timing, not results (likelihood low) → **Mitigation**: the identical-classification test; the errors list order is built from the gates, not from the probe order.
- **Risk**: A future caller passes stale gates to `check_readiness` (likelihood low) → **Mitigation**: the docstrings say the gates must come from the same startup run; the default stays "probe by itself".
- **Risk**: Three Plans edit `StartupValidationPipeline.check_services` (likelihood medium) → **Mitigation**: implement this Plan first; each later Plan records the overlap at its own freeze.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Readiness accepts gates (scripts/agent/services/mcp_health.py, tests/agent/test_mcp_health_posture.py) | In Progress | — | — |  |
| 2 | Pipeline probes once (scripts/agent/startup_validation.py, tests/agent/shared/test_startup_validation_pipeline.py) | In Progress | — | — |  |
| 3 | Documentation (docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md) | In Progress | — | — |  |
| 4 | Deployment and verification (scripts/agent/services/mcp_health.py, scripts/agent/startup_validation.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-095309_01_scripts_agent_services_mcp_health.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-095309_02_scripts_agent_startup_validation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-095309_05_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214905_startrev005_posture-probed-twice-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-220913
- **Related target files**: scripts/agent/services/mcp_health.py, scripts/agent/startup_validation.py, tests/agent/shared/test_startup_validation_pipeline.py, tests/agent/test_mcp_health_posture.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1), (2); `check_service_health` line 324 and `check_services` line 195 | scripts/agent/services/mcp_health.py | Phase 1 | AC-1 | optional-argument tests | Confirmed by repository evidence |
| REQ-003 | Issue Constraints (classification, messages and raising unchanged) | scripts/agent/services/mcp_health.py | Phase 1 | AC-3 | identical-classification tests | Explicit in issue |
| REQ-001 | Issue Required Changes (1), (2) | scripts/agent/startup_validation.py | Phase 2 | AC-1 | single-probe test | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (1); Acceptance Criteria (2) | scripts/agent/startup_validation.py | Phase 2 | AC-2 | gate-identity test | Explicit in issue |
| REQ-004 | Issue Required Changes (3); stale comment at lines 187-193 and early return at lines 183-184 | scripts/agent/startup_validation.py | Phase 2 | AC-4 | comment read-back; gates run | Confirmed by repository evidence |
| REQ-001 | Issue Acceptance Criteria (1); Testing Expectations | tests/agent/shared/test_startup_validation_pipeline.py | Phase 2 | AC-1, AC-5 | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -q` | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria (2) | tests/agent/shared/test_startup_validation_pipeline.py | Phase 2 | AC-2, AC-5 | gate-identity test | Explicit in issue |
| REQ-005 | Issue Required Changes (4); Testing Expectations | tests/agent/shared/test_startup_validation_pipeline.py | Phase 2 | AC-5 | single-probe test fails on pre-change code | Explicit in issue |
| REQ-003 | Issue Acceptance Criteria (3); Testing Expectations (the Issue named another test path: corrected) | tests/agent/test_mcp_health_posture.py | Phase 1 | AC-3, AC-5 | `uv run pytest tests/agent/test_mcp_health_posture.py -q` | Derived from confirmed evidence |
| REQ-005 | Issue Testing Expectations | tests/agent/test_mcp_health_posture.py | Phase 1 | AC-5 | new tests fail on pre-change code | Explicit in issue |
| REQ-006 | Issue Documentation Impact; ADR-003 Decision Detail 16; line 75 of the startup health document | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Phase 3 | AC-6 | `check_docs_quality`, `check_docs_content_policy` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-095309 -->