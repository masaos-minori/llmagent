## Goal

Inject the validated `DiagnosticsConfig` snapshot into the `DiagnosticStore` that `AgentSession` constructs (`REQ-001`, `REQ-008`), so the session-scoped store never reads `agent.toml` per operation and never runs with an unvalidated config.

## Scope
**Release unit**: N/A: not part of a release unit (config injection; the `storage_format` write-and-read path is the Plan's only release unit)

## Assumptions
- `AgentContext.__init__` builds `self.cfg = build_agent_config()` (`context.py:389`) before constructing `AgentSession()` (`context.py:395`), so `cfg.diagnostics` is a validated `DiagnosticsConfig` reachable at the construction site.
- `DiagnosticStore.__init__` gains a required `diagnostics_cfg` parameter (its own row); `session_id` keeps its runtime role — passed to `save()` at call time, not supplied at construction (where it is still `None`, no session started).
- A malformed `[diagnostics]` table raises during `build_agent_config()` (`config_section_builders.py` row) before `AgentSession()` is constructed, so this site always receives a validated snapshot.

## Design decisions
- **Wiring path is an implementation-phase decision** (two feasible paths, per Plan Design):
  - (a) Thread `cfg.diagnostics` into `AgentSession.__init__` and construct `DiagnosticStore(diagnostics_cfg=<config>)` at the existing site (line 62). Keeps `session.py` self-contained.
  - (b) Consolidate onto the Orchestrator-owned shared instance (`ctx.diagnostics`) so `session.py` does not create a second store. Aligns with `REQ-008` (exactly one store instance).
- Path choice determines how many `AgentSession` test fixtures must update — recorded as a Risk in the Plan.

## Alternatives considered
- **Leave `DiagnosticStore(self.session_id)` unchanged.** Rejected: `__init__` now requires `diagnostics_cfg` (its own row); the no-config construction fails.

## Implementation
### Target file
`scripts/agent/session.py`
### Procedure
- Supply the validated `DiagnosticsConfig` to the store constructed at line 62.
### Method
- Line 62, resolved via path (a) variant (optional param + validated-config fallback):
  ```python
  -        self._diagnostic_store = DiagnosticStore(self.session_id)
  +        if diagnostics_cfg is None:
  +            diagnostics_cfg = build_agent_config().diagnostics
  +        self._diagnostic_store = DiagnosticStore(diagnostics_cfg=diagnostics_cfg)
  ```
  `session_id` stays `None` at construction and is passed to `save()` at call time (unchanged). `AgentContext.__init__` (context.py:395) is frozen and still calls `AgentSession()` with no args, so the `build_agent_config().diagnostics` fallback supplies the validated snapshot; a malformed `[diagnostics]` table fails closed during that build. Tests may inject `diagnostics_cfg=` directly.
### Details
- `AgentSession.__init__` currently takes only `strict_mode`; any new parameter must be threaded from `AgentContext.__init__` (`context.py:395`) or supplied by the chosen path.
- Both paths change `AgentSession`'s constructor. Audit `tests/agent/test_agent_session.py` and related fixtures; if any fixture outside the Plan's `Implementation Target Files` must change, that is an **additional target file discovery** — amend the Plan via `amend_plan.py` before committing that path (Plan Risk: 40+ `AgentSession()` call sites).

### Companion test files
N/A: no `tests/` row names a session-test file in the Plan.

## Compatibility considerations
`DiagnosticStore()` now requires `diagnostics_cfg`. Every in-script constructor must inject it (orchestrator.py, repl.py, session.py rows). Changing `AgentSession.__init__` breaks existing test fixtures — see Details.

## Security considerations
Ensures the session-scoped store operates on the same validated config that failed closed at build time; no store runs with an unvalidated diagnostics config.

## Rollback considerations
Revert the commit.

## Validation plan
- Integration: the session-scoped store carries the injected validated config; no per-op config read.
- Command: targeted wiring test plus `tests/agent/test_agent_session.py` (and any fixtures the chosen path updates).

## Completion criteria
- `session.py` constructs the store with a validated `DiagnosticsConfig` via the chosen path.
- No `_load_diagnostics_config()` per-op read remains.

## Out of Scope
- The `storage_format` write-and-read path (`scripts/agent/diagnostic_store.py`, `scripts/db/schema_sql.py`).
- Wiring in `orchestrator.py` and `repl.py` (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 20261114-204015 | 20261114-204015 | Path resolved: optional `diagnostics_cfg` param on `AgentSession.__init__` (path a variant). `context.py` is frozen, so config is threaded via a default param with a `build_agent_config().diagnostics` fallback. Fixed the buggy `DiagnosticStore(self.session_id)` (passed None as `diagnostics_cfg`). |
| 2 | Add or update tests per Validation plan | Done | 20261114-204015 | 20261114-204015 | `test_agent_session.py` 53 passed (fallback build verified); `test_turn_persistence.py` passes. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261114-204015 | 20261114-204015 | ruff + mypy + lint-imports + bandit + ast-grep clean. Full agent suite: 4255 passed, 0 new failures (pre-existing procedure-01 fallout in test_session_persister.py/test_regression_diagnostic_persist.py is procedures 14/15). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 20261114-204015 | 20261114-204015 | No doc change in scope. |

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
- **Related target files**: `scripts/agent/session.py`
