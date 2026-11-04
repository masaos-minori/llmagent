## Goal
- Split `StartupValidationPipeline.check_services` into a new synchronous config-only stage `check_config` (new) holding the `mcp_auth`, `component_mandatoriness`, `routing_drift`, and `routing_safety_tiers` checks, and a runtime stage that keeps `readiness`, `mcp_tool_discovery`, and `rag_consistency` with the guard that skips discovery after a FATAL (`REQ-001`: the config-only stage contains exactly those four checks; `REQ-003`: runtime stage order and guard kept; `REQ-004`: logic, sources, severities, and messages unchanged and no short-circuit among the four).

## Scope
**Release unit**: config-stage-split

- `scripts/agent/startup_validation.py` only: one new method, the removal of the moved blocks from `check_services`, and the guard placement. The check logic, outcome sources, severities, and messages are moved, not changed.

## Assumptions
- Execution order: this procedure runs after the procedures of the disabled-auth Plan (the Plan's `Depends on`). The `mcp_auth` block is moved exactly as it stands at execution time, with or without the `is_disabled` filter; no step below depends on the comprehension's text, and no Before block quotes it.
- All four moved checks need no running server: `mcp_auth` reads `ctx.cfg`; `_check_component_mandatoriness` reads `ctx.cfg` and the registry file; `check_routing_drift` and `check_routing_safety_tiers` read `ctx.cfg` and static registries (checked in Step 3a).
- Today `check_services` runs `mcp_auth`, readiness, `_check_component_mandatoriness` followed by `if pipeline.has_fatal: return pipeline`, discovery, drift, safety tiers, RAG, in that order (checked in Step 3a). After the split the guard follows readiness instead, so a readiness FATAL still skips discovery and RAG; an `mcp_auth` or mandatoriness FATAL now aborts earlier, in the config stage.
- Each stage creates its own `StartupValidationResult`; the test harnesses capture a result by patching the class in `agent.startup_validation`, which works for each stage.
- The module is 11615 bytes, so one added method stays below the 20480-byte size gate.
- The sibling procedure for `scripts/agent/startup.py` (later `seq`) adds the call; the sibling test procedures re-point the tests that assert the moved checks.
- Step 2 start conditions held: the Plan is not gated (its dependency Plan is archived) and has no blocking Unknown; the overlap with the disabled-auth Plan is a recorded sequencing dependency.

## Design decisions
- `check_config` (new) is a synchronous `def` returning a `StartupValidationResult`: the four checks are synchronous, and no await is needed.
- Keep the original relative order inside `check_config` (new) (`mcp_auth`, mandatoriness, drift, safety tiers) and run all four without an early return, so the stage reports them together.
- Keep the original step comments (`# 1b.`, `# 3.`, `# 5.`, `# 5b.`) with the moved blocks and do not renumber the remaining steps, to keep the diff a pure move.

## Alternatives considered
- Moving only drift and safety tiers, leaving `mcp_auth` and mandatoriness in the runtime stage: rejected by the Plan's Decision 1 (they read the same configuration and abort after the same spawn work).

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Add `def check_config(self) -> StartupValidationResult:` (new) to `StartupValidationPipeline`, directly before `check_services`. Its body: `ctx = self._ctx`, `pipeline = StartupValidationResult()`, then the moved blocks in this order — the `# 1b. MCP authentication check` block, `_check_component_mandatoriness(ctx, pipeline)`, the `# 5. Routing drift (static)` block (the `drift_strict = True` assignment through the `except Exception` handler that calls `_record_drift_check_failure`), the `# 5b. Routing safety tiers` block — and `return pipeline`.
2. Remove those blocks from `check_services`. Keep the readiness step and the steps after it.
3. Immediately after the readiness step, keep the early return so a readiness FATAL still skips discovery and RAG.
4. Update the two docstrings.

### Method
Replace the old guard position.

Before:

```python
        _check_component_mandatoriness(ctx, pipeline)
        if pipeline.has_fatal:
            return pipeline
```

After (this line stands right after the readiness step's `except` block, in `check_services`; the `_check_component_mandatoriness` call is now in `check_config` (new)):

```python
        # A readiness FATAL skips tool discovery and the RAG check.
        if pipeline.has_fatal:
            return pipeline
```

Docstrings: `check_config` (new) gets `"""Run the configuration-only checks; none needs a running MCP server."""`; `check_services` becomes `"""Probe LLM/Embed health, validate MCP readiness and Security Posture, discover tools, and check RAG consistency."""`.

### Details
- `check_config` (new) takes no `await`; it does not create a `Logger`; the `Logger` local of `check_services` stays there for the RAG branch.
- Do not change the remediation texts, the `add_fatal`/`add_warning` source names (`mcp_auth`, `component_mandatoriness`, `routing_drift`, `routing_safety_tiers`), or the drift strictness fail-closed default.
- Do not edit `_check_component_mandatoriness`, `_record_drift_check_failure`, or `_classify_rag_failure`.

## Compatibility considerations
- `check_services` keeps its name, signature, and return type; `StartupOrchestrator._check_services` keeps its contract.
- For an invalid configuration the set and timing of outcomes change (the config checks report earlier and together, and drift and safety tiers are reported even when readiness would have failed); this is the requested behavior. For a valid configuration the outcome set is unchanged.

## Security considerations
Every FATAL that exists today stays FATAL regardless of environment or profile (ADR-004 Decision 14); no check logic, severity, or message changes, and the config-only checks now fail closed earlier.

## Rollback considerations
Revert the commit; the release unit (this split, the orchestrator call, and the re-pointed tests) is reverted together, because reverting only this file leaves the orchestrator calling a missing method.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on `scripts/agent/startup_validation.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_module_size.py`.
- `uv run radon cc scripts/agent/startup_validation.py -s` shows `check_services` below its current grade D (25).
- `uv run pytest tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_memory_failures.py -q` passes.
- Allowed red states until the sibling procedures land (release unit), recorded in the Failure Log: the tests of `tests/agent/test_startup_severity_classification.py` and `tests/agent/test_startup.py` that assert the moved checks through `_check_services`, and the `run()` tests of `tests/agent/test_startup_rollback.py` until the orchestrator call and its stub exist.

## Completion criteria
- `check_config` (new) holds exactly the four config-only checks, runs all of them without a short-circuit, and returns one result (`AC-1`).
- `check_services` keeps readiness, discovery, and RAG in order and still returns early after a readiness FATAL (`AC-3`).
- A valid configuration produces the same set of outcomes as before (`AC-4`), and no check logic or message text differs.

## Out of Scope
- The orchestrator wiring, the test re-pointing and new tests, and the documentation (separate procedures).
- Changing which checks exist, their severity, or their messages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the targeted tests of the Validation plan and record the allowed red states | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (config-only stage content), `REQ-003` (runtime stage order and guard), `REQ-004` (checks unchanged, no short-circuit)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `scripts/agent/startup_validation.py`
