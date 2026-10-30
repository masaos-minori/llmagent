# Implementation Procedure: `scripts/agent/startup_validation.py`

## Goal

Wire the mandatoriness cross-check into the startup pipeline before MCP tool discovery publication, so a registry conflict or unknown classification aborts startup as a named fatal (REQ-004 wiring; plan Phase 3 "wire the cross-check into the pipeline before discovery publication").

## Scope

- `scripts/agent/startup_validation.py`: one new pipeline stage inside `StartupValidationService.check_services` (:71), positioned before the posture/discovery block (:114-120).
- No change to the posture-gate or discovery machinery (plan Target Architecture: reuse, not duplicate).

## Assumptions

- Rows 2 and 4 are landed (loader + `validate_against_registry` (new)).
- MCP server configs are reachable from `AgentContext` the same way `collect_server_postures` reads them (`scripts/agent/services/mcp_health.py:217-233` iterates config entries via `ctx`), so the stage builds `{server_key: cfg.required}` from `ctx`.

## Design decisions

- New private stage function `_check_component_mandatoriness(ctx, pipeline)` (new): loads the registry via `load_component_mandatoriness()` once, calls `ProductionConfigValidator().validate_against_registry(...)`, and for each returned message calls `pipeline.add_fatal("component_mandatoriness", message, remediation)` (existing `StartupValidationResult.add_fatal`, `scripts/agent/shared/health_models.py:95`) — reuses the pipeline's FATAL semantics (plan Design §Key Components 2), no new channels (REQ-008).
- A missing or unparsable registry file is also a fatal under the same source label: "Undeterminable component mandatoriness" (ADR-004 :85 Fail-Fast list already names it). Catch `ComponentMandatorinessError` (new)/`FileNotFoundError`/`OSError` from the loader and report one fatal.
- Position: before `collect_server_postures` (:114) — mandatoriness classifies the components the posture gates then consume; the check reads no network state, so it costs nothing at the front.

## Alternatives considered

- Wire into `scripts/agent/startup.py` instead — rejected: startup.py :130-147 only renders `pipeline.has_fatal`; stages belong in the pipeline assembler (module docstring: "This module assembles the pipeline; it validates no configuration of another module" — the validator owns the check, this file only wires).
- Wire into `config_builders.py` reload path — rejected for this row (see row 4 Alternatives; reload-time enforcement is an open Needs Confirmation, out of plan scope).

## Implementation

### Target file

`scripts/agent/startup_validation.py`

### Procedure

1. Add module-level imports: `component_mandatoriness` (new) loader functions (row 2, (new) symbols `load_component_mandatoriness` (new)) and `ProductionConfigValidator` (existing class at `scripts/agent/production_config_validator.py:208`).
2. Add `_check_component_mandatoriness` (new) per Design: build the `{server_key: required}` mapping from ctx config, run `validate_against_registry` (new), `add_fatal("component_mandatoriness", ...)` per error with remediation text naming `registry/component_mandatoriness.yaml`.
3. Call it inside `check_services` (:71) after the existing readiness/required-services block and before `posture_gates = await collect_server_postures(ctx)` (:114). If `pipeline.has_fatal` after the stage, return early the same way the neighboring stages do (the existing flow already short-circuits on fatals before publication).

### Method

Follow the adjacent stage pattern: readiness (:85-103) and discovery (:126-132) each call `pipeline.add_fatal(source, message)`; this stage is synchronous and adds no awaits.

### Details

- Source label `component_mandatoriness` (new) becomes the named fatal outcome plan AC-3 requires ("aborts startup with a named fatal outcome").
- The publication-order property (AC-5) is untouched and confirmed by row 24's regression test: posture collection (:114) still precedes `ctx.services_required.runtime_tools = discovery.registry` (:118-120).
- Cross-plan overlap (reported by `check_plan_target_overlaps.py`): ragcorpus001 also targets this file. Landing order recorded in the plan Dependencies; this stage must remain before the discovery block regardless of which lands first — re-verify placement after the other plan's change merges.

## Compatibility considerations

- Production behavior unchanged for the all-required configuration: the stage finds zero errors today (10 configured servers match 10 registry entries).
- Startup latency: one YAML file read; negligible.

## Security considerations

- Fail-closed: registry load failure is fatal, never skipped (REQ-008: the fatal message carries the reason).

## Rollback considerations

- Remove the stage call + function; single commit revert. Rows 1-4 may stay (unused code is inert).

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py` (row 24 adds the publication-order regression) and `uv run pytest tests/agent/test_production_config_validator.py` (row 23).
- Plan-specified: `uv run pytest tests/shared tests/agent`; gates per `rules/toolchain.md` incl. `uv run mypy scripts`, `ruff`, `bandit`, `lint-imports`.

## Completion criteria

- With a synthetic conflicting config the pipeline reports a `component_mandatoriness` (new) fatal and startup aborts before `runtime_tools` is published (plan AC-3); with the real config the pipeline outcome is unchanged (plan AC-6).

## Out of Scope

- The check logic itself (row 4), loader (row 2), tests (rows 23-24), `scripts/agent/startup.py` (plan Excluded: ordering already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the pipeline stage and its call site per Procedure | Pending | — | — | Needs rows 2+4 |
| 2 | Regression test arrives from row 24 | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | N/A: docs live in rows 25-27 | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Rows 2 (loader) and 4 (validator method) must land first (plan phase order) | No | — |
| 1 | ragcorpus001 targets the same file; verify non-contradicting placement (check_plan_target_overlaps finding) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (startup cross-validation wiring, fatal on unknown/conflict)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/agent/startup_validation.py`
