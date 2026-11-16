## Goal

Make `StartupValidationPipeline.check_services` probe each MCP server's posture once and give tool discovery the very gates readiness classified, replacing the stale comment above the discovery step (`REQ-001`: one probe; `REQ-002`: discovery gets the same gate objects; `REQ-004`: accurate comment; `REQ-005`: pipeline tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `check_services` in `scripts/agent/startup_validation.py` and the companion test file `tests/agent/shared/test_startup_validation_pipeline.py`.
- Out of scope: the RAG consistency step (Plan `startrev006`), shutdown handling (Plan `startrev004`), tool discovery logic, runtime re-probing, and `HealthCheckResult`.

## Assumptions

- Execute after document `01` of this Plan: `check_readiness` must already accept the `gates` keyword.
- Plan overlap judgment: Plans `startrev006` and `startrev004` also edit `check_services` and `tests/agent/test_startup_validation.py`/`scripts/agent/startup_validation.py`, each in a different part of the method; this Plan changes the head of the method and goes first. Compatible with a sequencing dependency.
- Test files that patch `check_readiness` use `AsyncMock`, which accepts the new keyword (re-checked with `rg` in `tests/agent`); only `tests/agent/test_startup_validation.py` also patches `collect_server_postures`.
- `collect_server_postures` never raises, so placing it inside the readiness `try` only keeps the existing exception boundary.
- Test file `tests/agent/shared/test_startup_validation_pipeline.py` is a companion: it is a Plan row under `tests/`, only the `startup_validation.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Collect the gates once, immediately before `check_readiness(ctx, gates=gates)`, inside the existing readiness `try`, so a failure still becomes the `readiness` fatal and still returns before discovery.
- Discovery uses the same object: `McpToolDiscoveryService(ctx, posture_gates=gates)`. The second `collect_server_postures` call is deleted, and discovery never falls back to an unprobed default.

## Alternatives considered

- Storing the gates on `HealthCheckResult` or changing the return type of `check_readiness`: rejected in the Plan (package layering, and a changed return type for patched calls in several test files).

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. In `check_services`, inside the readiness `try`, add `gates = await collect_server_postures(ctx)` before the readiness call and call `check_readiness(ctx, gates=gates)`.
2. Remove the second `posture_gates = await collect_server_postures(ctx)` in the discovery `try` and construct `McpToolDiscoveryService(ctx, posture_gates=gates)`.
3. Replace the stale comment above the discovery step (it claims discovery runs after a posture error makes `check_readiness` raise) with a statement of the one-observation rule: the gates are collected once, readiness classifies them, and discovery runs only after a readiness pass and uses the same observation.

### Method
- Keep the early return on `pipeline.has_fatal` exactly as it is; it guarantees `gates` is bound whenever discovery runs.
- Keep the import line from `agent.services.mcp_health` as is (both names are still used).

### Details
- `check_services` is radon C (17); moving and removing one call must not raise the grade.
- Do not change the messages, severities or the order of the pipeline outcomes.

### Companion test files
- `tests/agent/shared/test_startup_validation_pipeline.py`
  - Procedure: write these first; the single-probe test must fail on the current code: (a) with `collect_server_postures` patched to a counting fake at `agent.startup_validation.collect_server_postures`, one `check_services` run calls it exactly once; (b) the patched `McpToolDiscoveryService` is constructed with `posture_gates` that `is` the object the patched `check_readiness` received as `gates`; (c) a readiness failure (patched `check_readiness` raising) returns before discovery, with one probe and no discovery construction. Follow the file's existing `MODULE` patch pattern.
  - Validation: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_validation.py -q`.

## Compatibility considerations

- Startup behavior is unchanged except that the posture probe runs once, before the llm and embed probes, instead of twice; classification and message order come from the gates, not from probe timing.
- Tests that patch `check_readiness` keep working; any test file that turns out to need a `collect_server_postures` patch is fallout to report at implementation time (`rules/workflow-lifecycle.md` Plan Amendment Approval Classes).

## Security considerations

- Closes a window where the gate that earned readiness could differ from the gate discovery applied. Discovery must fail closed: if the gates were ever unavailable, no server is allowed; it must never use an unprobed default.

## Rollback considerations

- Revert the commit together with document `01` if the signature change is reverted; the pipeline alone can be reverted to the two-probe shape without touching `mcp_health.py`.

## Validation plan

- `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py tests/agent/test_startup_memory_failures.py tests/agent/test_repl_health.py -q`.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- A `check_services` run calls `collect_server_postures` exactly once (`REQ-001`, AC-1) and discovery is constructed with the same gate objects readiness received (`REQ-002`, AC-2).
- The stale comment is gone and the new comment states the one-observation rule (`REQ-004`, AC-4).
- The new tests exist and the single-probe test fails on the pre-change code (`REQ-005`, AC-5); AC-7 checks pass.

## Out of Scope

- RAG step and shutdown changes (other Plans), runtime re-probing, documentation (document `05`), and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the single-probe and gate-identity tests first and confirm the single-probe test fails (companion `tests/agent/shared/test_startup_validation_pipeline.py`) | Pending | — | — | |
| 2 | Collect the gates once in the readiness `try`, pass them to readiness and discovery, delete the second probe and replace the stale comment | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (one probe), `REQ-002` (same gates to discovery), `REQ-004` (accurate comment), `REQ-005` (pipeline tests)
- **Source issue**: issues/20261115-214905_startrev005_posture-probed-twice-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220913_startrev005_posture-probed-twice-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095309
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/shared/test_startup_validation_pipeline.py`
