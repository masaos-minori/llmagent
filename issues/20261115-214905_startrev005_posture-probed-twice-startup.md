# Startup probes MCP security posture twice and discovery uses the second, unvalidated probe

## Priority
Medium

## Summary
`check_readiness` probes every MCP server's published security posture and decides fatal or non-fatal on that result. Immediately afterwards `StartupValidationPipeline.check_services` probes every server again with `collect_server_postures` and gives that second result to tool discovery. The gate a server earned at readiness is therefore not the gate its tools run under, which contradicts the contract stated for `allowed_server_keys`. Probe once and reuse the result.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Explicit in code): `check_readiness` calls `check_service_health`, which calls `collect_server_postures(ctx)` to build the gates it classifies.
- Evidence (Explicit in code): `check_services` then calls `collect_server_postures(ctx)` again before `McpToolDiscoveryService(ctx, posture_gates=...)`.
- Evidence (Explicit in code): the `allowed_server_keys` docstring states that no consumer re-probes `/health` and that the gate a server earned at readiness is the gate its tools run under.
- Evidence (Explicit in code): the comment above the second probe says the step runs after a posture error makes `check_readiness` raise. That is not true: `check_services` records the raised error as a fatal and returns before discovery whenever `pipeline.has_fatal`, so the discovery step never runs on that path.
- Related and already closed: `plans/done/20261110-225014_adrrev007_posture-fail-closed.md` (posture fail-closed behavior).

## Problem
Two independent probes can disagree. A server that is green at readiness and not green at the second probe loses its tools without any readiness fatal naming it; a server that was a non-fatal warning at readiness and green the second time gains tools under a gate readiness never approved. Each probe is also a sequential network round trip per server, so the cost is doubled. The stale comment describes a path that no longer exists.

## Reason for Change
The posture gate is a security control; its decision and its use should come from the same observation. The window is small, but the existing documented contract already says it is closed. Medium because the exposure is narrow and the failure mode is mostly loss of tools, not extra privilege.

## Implementation Intent
Probe once per startup, in the readiness stage, and hand the resulting gates to tool discovery. Keep `check_readiness` and its fatal rules unchanged. Remove or correct the stale comment. Keep the posture failure classes, fatal conditions and messages exactly as they are.

## Target Files or Areas
- scripts/agent/startup_validation.py (`StartupValidationPipeline.check_services`)
- scripts/agent/services/mcp_health.py (`check_service_health`, `check_readiness`, `collect_server_postures`)
- tests/agent/shared/test_startup_validation_pipeline.py
- tests/agent/services (readiness tests)

## Required Changes
- Return the gates from the readiness stage (or store them on its result) so `check_services` can pass them to discovery without a second probe.
- Delete the second `collect_server_postures` call in `check_services`.
- Correct the comment that describes discovery running after a readiness exception.
- Add a test that counts probe calls per startup (exactly one per server) and a test that discovery receives the same gate objects readiness classified.

## Constraints
- Fatal and non-fatal classification, remediation text and the log messages MUST NOT change.
- `check_readiness` MUST still raise on a required-service or fatal posture failure.
- No posture value, fingerprint or server-supplied message may reach logs or messages (existing rule).

## Acceptance Criteria
- A startup run probes each usable MCP server's posture exactly once.
- Tool discovery receives the gates computed by the readiness stage.
- The behavior for every existing readiness test is unchanged.
- `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` and the readiness tests under `tests/agent/services` pass with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit tests with a counting fake for the probe; one test on the pipeline level asserting a single probe and identical gate identity. Regression run of the startup validation tests.

## Documentation Impact
Update the MCP readiness and posture design text to state that posture is observed once per startup and that discovery uses that observation. Policy only, with no values.

## Out of Scope
- Changing posture classification, failure classes or fatal rules.
- Re-probing at runtime (restarts and per-call health checks).
- The tool discovery logic itself.

## Dependencies
N/A: none

## Unresolved Questions
- Does any caller rely on `check_readiness` returning only warnings and errors? (The return shape change is the main compatibility question; assumption: add the gates without removing existing fields.)

## AI Implementation Instruction
Keep changes minimal. Do not change classification or messages. Write the single-probe test first and confirm it fails on the current code.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214905
- **Related target files**: scripts/agent/startup_validation.py, scripts/agent/services/mcp_health.py, tests/agent/shared/test_startup_validation_pipeline.py
