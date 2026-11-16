## Goal

Let `check_service_health` and `check_readiness` accept pre-collected posture gates through an optional keyword `gates`, so a caller that already probed does not cause a second probe (`REQ-001`: one probe per startup; `REQ-003`: classification and raising behavior unchanged, a call without `gates` still probes by itself; `REQ-005`: tests for the optional argument).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two functions in `scripts/agent/services/mcp_health.py` and the companion test file `tests/agent/test_mcp_health_posture.py`.
- Out of scope: posture classification, failure classes, remediation text and messages, `HealthCheckResult`'s shape, `collect_server_postures` itself, and the pipeline change (document `02`).

## Assumptions

- Source plan `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` was verified against the code in this cycle: `check_service_health` calls `collect_server_postures(ctx)` after the llm and embed probes, `check_readiness` is its only caller, and `check_readiness` is called only by `StartupValidationPipeline.check_services` (re-read with `rg`). No Plan correction was needed beyond formatting the `Related Tests` cells.
- `collect_server_postures` never raises (its docstring: a probe failure becomes an Availability gate), so passing its result in changes nothing about error flow.
- Plan overlap judgment: no other Frozen Plan targets this file or this test file.
- Test file `tests/agent/test_mcp_health_posture.py` is a companion: it is a Plan row under `tests/`, only the `mcp_health.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Add `gates: dict[str, PostureGate] | None = None` as a keyword-only parameter to both functions; `check_readiness` passes it through unchanged. When it is `None`, `check_service_health` calls `collect_server_postures(ctx)` exactly as today.
- An empty dict is a valid pre-collected result (no usable server) and MUST NOT trigger a probe: test `gates is None`, not truthiness.

## Alternatives considered

- Adding the gates to `HealthCheckResult` or returning a pair from `check_readiness`: rejected in the Plan (layering of `agent.shared.health_models` and a changed return type for every patched call).

## Implementation
### Target file
`scripts/agent/services/mcp_health.py`

### Procedure
1. Add the keyword-only parameter `gates` to `check_service_health` and to `check_readiness`.
2. In `check_service_health`, replace the unconditional `gates = await collect_server_postures(ctx)` with `if gates is None: gates = await collect_server_postures(ctx)`; leave the loop that builds warnings and errors untouched.
3. In `check_readiness`, call `check_service_health(ctx, gates=gates)`.
4. Update both docstrings: state that `gates` must come from the same startup run, and that omitting it makes the function probe by itself.

### Method
- Keep the order of work in `check_service_health` (llm probe, embed probe, then classification of the gates), so the message order and the classification do not change.
- No new import: `PostureGate` is defined in this module.

### Details
- `check_service_health` is radon C (11); one added `if` must not push it to D.
- The `RuntimeError` raised by `check_readiness` on a required-service or fatal-posture failure, and its message and remediation text, are unchanged.

### Companion test files
- `tests/agent/test_mcp_health_posture.py`
  - Procedure: write these first and confirm they fail before the change: (a) `check_service_health(ctx, gates=gates)` makes no call to `collect_server_postures` (patch it with a counting fake) and returns the same warnings and errors as a probed run for the same gates; (b) `check_readiness(ctx, gates=gates)` does the same and raises the same `RuntimeError` text for a Safety or Integrity gate failure; (c) an empty `gates` dict does not probe; (d) without `gates` each function probes exactly once. Reuse the file's existing ctx and gate builders.
  - Validation: `uv run pytest tests/agent/test_mcp_health_posture.py -q`.

## Compatibility considerations

- The new parameter is optional and keyword-only; every existing caller and the test files that patch `check_readiness` with `AsyncMock` keep working.
- Return types and raised exceptions are unchanged.

## Security considerations

- The posture gate is a security control. Passing gates in lets the gate readiness classified be the gate discovery uses (ADR-003 Decision Detail 16). The function never accepts `None` to mean "no gates"; an omitted argument means "probe by yourself", so the control cannot be skipped by omission.

## Rollback considerations

- Revert the commit; document `02` depends on this signature and must be reverted with it.

## Validation plan

- `uv run pytest tests/agent/test_mcp_health_posture.py tests/agent/test_repl_health.py tests/agent/test_failure_handling_policy_cross_cutting.py -q`; the new cases fail on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`.

## Completion criteria

- `check_service_health` makes no probe of its own when given `gates`, and probes once when not given (`REQ-001`, AC-1).
- For the same gates, warnings, errors, remediation text and the `RuntimeError` of `check_readiness` are identical to a probed run (`REQ-003`, AC-3).
- The new tests exist and fail on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- Pipeline changes, the stale comment, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the optional-argument tests first and confirm they fail (companion `tests/agent/test_mcp_health_posture.py`) | Done | 20261116 | 20261116 | 4 cases in `TestOptionalGatesArgument`; 3 discriminated the missing `gates` kwarg on pre-change code. |
| 2 | Add the optional keyword `gates` to `check_service_health` and `check_readiness` | Done | 20261116 | 20261116 | Keyword-only param, `if gates is None` guard, `check_readiness` passthrough, both docstrings updated. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261116 | 20261116 | 107 targeted tests pass; ruff format/check, mypy, lint-imports, module size, reference table all clean. |

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
- **Requirement ID**: `REQ-001` (one probe per startup), `REQ-003` (classification unchanged), `REQ-005` (tests)
- **Source issue**: issues/20261115-214905_startrev005_posture-probed-twice-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220913_startrev005_posture-probed-twice-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095309
- **Related target files**: `scripts/agent/services/mcp_health.py`, `tests/agent/test_mcp_health_posture.py`
