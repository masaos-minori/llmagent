# Configuration-only routing validation runs after the MCP subprocesses are spawned

## Priority
Medium

## Summary
`StartupOrchestrator.run` spawns every MCP subprocess server and waits for each to become healthy before `check_services` runs. Inside `check_services`, the routing-drift and safety-tier checks read only the agent configuration and the static tool registry, yet they run after all of that work. A configuration error that is detectable immediately therefore aborts startup only after every server was started, polled, and then rolled back. Move configuration-only validation ahead of the side-effecting startup steps.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path.
- The run order in `StartupOrchestrator.run` is: component initialization, server start, MCP health verification, `check_services`, prompt setup. A failure after server start triggers `_rollback_servers`.
- `check_routing_drift` compares each server's configured `tool_names` against the static tool registry, using `ctx.cfg.mcp.mcp_servers` only. `check_routing_safety_tiers` checks the declared safety tiers from `ctx.cfg.approval` against the registered tools. Neither reads the result of server startup or discovery.
- In strict mode (the production profile requires `routing_drift_strict`), drift is a FATAL outcome; a safety-tier failure is always FATAL.
- Archived work on the startup validation pipeline (for example `plans/done/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`) changed what the pipeline checks, not where in the startup sequence config-only checks run.

## Problem
For a configuration with a drifted routing entry or a missing safety tier, the actual sequence is: spawn each subprocess and poll its `/health` until ready (up to the per-server startup timeout, one server after another), run the post-start health verification, run readiness and discovery, and only then report the configuration FATAL and roll the servers back. The same failure could be reported before any process exists.

Evidence is from reading the code: the two functions' inputs are `ctx.cfg` and the static registry, and the call order is explicit in `StartupOrchestrator.run` and `StartupValidationPipeline.check_services`. The ordering was not exercised by running the agent.

## Reason for Change
- Time: a config mistake costs the full sequential startup time of every server before it is reported.
- Side effects: processes are launched and torn down for a run that could never succeed, and the interrupted-startup window during which a subprocess can be left behind (see `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`) is opened for nothing.
- Fail-fast principle: validation that needs no running service should precede steps with external effects.

## Implementation Intent
Introduce a configuration-validation stage that runs before `start_servers` and contains only checks that need no spawned process (routing drift, safety tiers, and any other config-only check found during the work). Keep the checks that need running servers (readiness, tool discovery, RAG consistency) where they are. Preserve the fail-closed semantics (unconditional FATAL for safety/integrity failures, ADR-004 Decision 14) and the existing aggregated outcome reporting.

## Target Files or Areas
- `scripts/agent/startup.py` (`StartupOrchestrator.run`, `_check_services`)
- `scripts/agent/startup_validation.py` (`StartupValidationPipeline.check_services`)
- `scripts/agent/services/routing_drift.py` (`check_routing_drift`, `check_routing_safety_tiers`, read only)
- `tests/agent/test_startup.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_rollback.py`

## Required Changes
- Split the config-only checks out of `check_services` into a stage that `run` executes before `start_servers`.
- Report that stage's outcomes through the existing reporter, with the same sources and severities.
- Keep the runtime-dependent checks in their current stage and order.
- Add tests: a config with a drifted routing entry (strict mode) aborts before `start_servers` is called; a safety-tier failure aborts before any subprocess start; a valid config runs both stages and the overall outcome is unchanged.

## Constraints
- Every FATAL that exists today must still be FATAL, regardless of environment or profile.
- Do not change the check logic itself or the outcome message formats.
- The reporter must still display warnings and fatals from both stages.
- Do not add configuration values or timings to design documents.

## Acceptance Criteria
- A configuration that fails a config-only FATAL check never reaches `start_servers`.
- A valid configuration produces the same set of outcomes as today, in a defined order.
- Non-fatal warnings from the config-only checks are still shown.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests with mocked starter and validation components asserting call order and that `start_servers` is not invoked on a config failure.
- Run `tests/agent/test_startup.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_reporter.py`, `ruff`, and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
Yes: the agent startup sequence documentation must describe the new order (config-only validation before server start). State the intent (fail before external effects) and the boundary between config-only and runtime-dependent checks. Check `docs/23_agent/` startup chapters first; do not copy concrete timeouts or values. Run the docs checkers named in `routing.md` for any `docs/` change.

## Out of Scope
- Changing which checks exist or their severity.
- The post-start health verification and readiness logic.
- Parallelizing server startup.

## Dependencies
- Related to `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`: this issue shrinks the window in which a startup interruption can orphan a subprocess, but does not fix the orphan itself. Independent fix order.

## Unresolved Questions
- Whether the current ordering is intentional (for example an ADR decision that all validation is reported together after services are up): `Needs confirmation` against the startup ADRs before changing it.
- Whether any other check in `check_services` is also config-only and should move (the `mcp_auth` check reads configuration only): to be decided during implementation, together with the separate `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md` change to that check. The mandatoriness cross-check added to `check_services` (`_check_component_mandatoriness`, registry versus each server's configured `required`; fatal on a conflict or unknown server) is another config-only check that also runs after server start, so it belongs in the same decision; it must still run before MCP tool discovery.

## AI Implementation Instruction
Move only config-only checks and keep every check's logic and severity unchanged. Do not reorder runtime-dependent steps and do not touch the lifecycle or subprocess code. Confirm the ordering question in Unresolved Questions against the ADRs first and stop to report if an ADR requires the current order.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135634
- **Related target files**: scripts/agent/startup.py, scripts/agent/startup_validation.py, scripts/agent/services/routing_drift.py, tests/agent/test_startup.py, tests/agent/test_startup_validation.py, tests/agent/test_startup_rollback.py
