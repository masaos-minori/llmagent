## Goal
- Add a config-only validation step to `StartupOrchestrator`, run it in `run()` after component initialization and before `_start_servers`, and share one display-and-raise helper between the two stages, so a configuration failure aborts startup with the existing error before any MCP subprocess is spawned and without a rollback (`REQ-001`: the stage runs before `_start_servers`; `REQ-002`: the abort uses the existing format and displays the stage's warnings and fatals).

## Scope
**Release unit**: config-stage-split

- `scripts/agent/startup.py` only: `run()`, `_check_services`, and two new methods. The rollback, `_start_servers`, `_verify_mcp_health`, and `_setup_prompt` are not changed.

## Assumptions
- `StartupValidationPipeline.check_config` (new) is declared by the sibling procedure for `scripts/agent/startup_validation.py` (earlier `seq`); this procedure calls it.
- Today `_check_services` awaits `check_services()`, displays the outcomes, reports readiness, and on a FATAL builds the fatal text from the outcomes and raises `RuntimeError(f"Startup validation failed: {fatal_str}")` (checked in Step 3a); that behavior must stay identical for the runtime stage.
- `ComponentInitializer.initialize()` runs outside the `try` that owns the rollback, and the existing tests pin that an initialize failure triggers no rollback; the config stage follows the same rule because nothing is spawned yet.
- `StartupValidationResult` and `StartupCheckStatus` are already imported at module level in this file.
- `ReadinessReporter.report_readiness` counts only readiness, discovery, and RAG sources, so the config stage does not call it (checked in Step 3a).
- The module is 6507 bytes, well below the size gate.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; the overlap with the disabled-auth Plan is a recorded sequencing dependency.

## Design decisions
- `_check_config` (new) is a synchronous method: `check_config` is synchronous, so no await is needed.
- One helper, `_finish_validation_stage` (new), holds the display step, the optional readiness report, and the FATAL raise, so both stages report identically; `_check_services` keeps its public contract.
- Call the stage outside the `try`, between `initialize()` and `_start_servers`.

## Alternatives considered
- Calling the stage inside the `try` (so a config failure would trigger a no-op rollback): rejected by the Plan's Decision 2; nothing is spawned, and it would call `shutdown_all` needlessly.

## Implementation
### Target file
`scripts/agent/startup.py`

### Procedure
1. In `run()`, call `self._check_config()` (new) right after the `initialize()` call and before the `try`.
2. Replace `_check_services` with the three methods below.

### Method
`run()`.

Before:

```python
        ).initialize()
        try:
            await self._start_servers()
```

After:

```python
        ).initialize()
        self._check_config()
        try:
            await self._start_servers()
```

Replace the head of `_check_services` and give the FATAL block a new home.

Before:

```python
    async def _check_services(self) -> None:
        """Probe LLM/Embed health, validate MCP readiness and Security Posture, validate tool definitions."""
        pipeline = await self._validation_pipeline.check_services()
        self._display_pipeline_results(pipeline)
        self._report_readiness(pipeline)

        if pipeline.has_fatal:
```

After:

```python
    def _check_config(self) -> None:
        """Run the config-only validation stage before any MCP subprocess is spawned."""
        self._finish_validation_stage(
            self._validation_pipeline.check_config(), report_readiness=False
        )

    async def _check_services(self) -> None:
        """Probe LLM/Embed health, validate MCP readiness and Security Posture, validate tool definitions."""
        pipeline = await self._validation_pipeline.check_services()
        self._finish_validation_stage(pipeline, report_readiness=True)

    def _finish_validation_stage(
        self, pipeline: StartupValidationResult, *, report_readiness: bool
    ) -> None:
        """Display a stage's outcomes, optionally report readiness, and abort on a FATAL."""
        self._display_pipeline_results(pipeline)
        if report_readiness:
            self._report_readiness(pipeline)

        if pipeline.has_fatal:
```

### Details
- The body of the old `if pipeline.has_fatal:` block (building `fatal_parts`, logging, and raising `Startup validation failed: ...`) moves unchanged into `_finish_validation_stage` (new); do not alter the message format or the remediation lines.
- `_display_pipeline_results` and `_report_readiness` stay as they are.
- `StartupInterrupted`, `_rollback_servers`, and the `try`/`except` structure of `run()` are not touched.

## Compatibility considerations
- `_check_services` keeps its signature, return type, and every observable behavior; the stage reports through the same reporter and raises the same error type and format.
- A configuration FATAL now raises before `_start_servers`, and no `shutdown_all` call is made.

## Security considerations
N/A: no credential or input handling; fail-closed behavior is kept and happens earlier.

## Rollback considerations
Revert the commit; the release unit is reverted together, because reverting only this file leaves `check_config` unused and the moved checks out of `check_services`.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on `scripts/agent/startup.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `PYTHONPATH=scripts uv run lint-imports`.
- `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup_reporter.py tests/agent/shared/test_startup_validation_pipeline.py -q` passes once the rollback fixture stub of its sibling procedure exists; until then the `run()` tests of the rollback file are an allowed red state (release unit), recorded in the Failure Log.
- `uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
- `run()` calls the config stage after `initialize()` and before `_start_servers`, outside the rollback `try` (`AC-1`).
- A config FATAL raises `Startup validation failed: ...` before any subprocess start, with no rollback, and the stage's warnings and fatals are displayed (`AC-2`).
- `_check_services` behaves as before for the runtime stage.

## Out of Scope
- The pipeline split, the tests, and the documentation (separate procedures); the rollback logic and the other startup steps.

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
- **Requirement ID**: `REQ-001` (config stage before server start), `REQ-002` (abort format and display)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `scripts/agent/startup.py`
