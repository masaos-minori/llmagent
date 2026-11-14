## Goal

Construct the single shared `DiagnosticStore` in the Orchestrator with the validated `DiagnosticsConfig` snapshot injected (`REQ-001`, `REQ-008`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ctx` is the `AgentContext` held as `self._ctx`; `ctx.cfg` is the built `AgentConfig` (`context.py:389`), and `ctx.cfg.diagnostics` is a validated `DiagnosticsConfig` (`config_dataclasses.py:390`).
- `ctx.diagnostics` (context.py:399) is the shared-store handle other producers read; the Orchestrator owns the instance and assigns it here.
- `DiagnosticStore.__init__` gains a required `diagnostics_cfg` parameter (its own row); `session_id` keeps its `None` default.

## Design decisions
- **Keyword injection `DiagnosticStore(diagnostics_cfg=ctx.cfg.diagnostics)`.** Keeps `session_id` at its existing default (the store receives `session_id` per `save()` call, not at construction).

## Alternatives considered
- **Pass `ctx.session_id` too.** Rejected: the current code constructs with no session ID; changing it is unrelated to this Plan and out of scope.

## Implementation
### Target file
`scripts/agent/orchestrator.py`
### Procedure
- Inject the config at the existing construction site.
### Method
- Line 89:
  ```python
  -        self._diagnostic_store = DiagnosticStore()
  +        self._diagnostic_store = DiagnosticStore(diagnostics_cfg=ctx.cfg.diagnostics)
  ```
  Line 90 (`ctx.diagnostics = self._diagnostic_store`) is unchanged; it still publishes the single shared instance for other producers.
### Details
- Because `cfg.diagnostics` comes from `build_agent_config()`, a malformed `[diagnostics]` table raises during config build (`config_section_builders.py` row) before the store is ever constructed, so this site always receives a validated snapshot.

### Companion test files
N/A: producer-wiring coverage is a targeted wiring test described in the Validation plan (no dedicated test-file row in the Plan).

## Compatibility considerations
`DiagnosticStore()` now requires `diagnostics_cfg`. Any other in-script constructor of `DiagnosticStore` (e.g. `repl.py`, `session.py`) must inject the config too (their own rows).

## Security considerations
Ensures the store operates on the same validated config that failed closed at build time, so no store runs with an unvalidated/weak diagnostics config.

## Rollback considerations
Revert the commit (`N/A: revert the commit`).

## Validation plan
- Integration: the Orchestrator exposes one `DiagnosticStore` instance via `ctx.diagnostics`; it carries the injected config.
- Command: targeted wiring test asserting `ctx.diagnostics is <the constructed store>` and that its config equals `ctx.cfg.diagnostics`.

## Completion criteria
- `orchestrator.py` constructs `DiagnosticStore` with `diagnostics_cfg=ctx.cfg.diagnostics`.
- `ctx.diagnostics` references that single instance.

## Out of Scope
- Wiring in `repl.py` and `session.py` (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-008`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `scripts/agent/orchestrator.py`
