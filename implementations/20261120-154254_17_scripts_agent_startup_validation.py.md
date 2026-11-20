## Goal

Remove the `check_routing_drift()` startup-pipeline call site and its import from `scripts/agent/startup_validation.py` (`REQ-004`, scope approved). The config-based routing-drift step is obsolete once `validate_routing_against_config()` (row 8) and `check_routing_drift()` (row 16) are gone; live-vs-registry drift detection remains via `mcp_tool_discovery.py:165`. Keep the "Routing safety tiers" (`check_routing_safety_tiers`) step.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The call site is the `try/except` block at `startup_validation.py:173-179` (prefixed by the "# 5. Routing drift (static)" comment at lines 169-172), calling `check_routing_drift(ctx, strict=True)` and recording `routing_drift` warnings/FATAL on the pipeline.
- The import is `from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers` at line 31; `check_routing_safety_tiers` (still used by the "5b. Routing safety tiers" step) must remain imported.
- **CASCADE (new evidence, not in original Plan scope):** `check_routing_drift` is referenced by test files that are **not** in this Plan's `Implementation Target Files`:
  - `tests/agent/shared/test_startup_validation_pipeline.py` — ~10 `patch("agent.startup_validation.check_routing_drift", ...)` sites (lines 127, 162, 209, 239, 268, 381, 412, 453, 499, 534). Once the line-31 import is removed, `agent.startup_validation.check_routing_drift` no longer exists, so those patches raise `AttributeError`.
  - `tests/agent/test_startup_validation.py` — dict mocks and `patch("agent.startup_validation.check_routing_drift")` (lines 72, 120, 142, 157, 202, 241, 266, 460).
  - `tests/agent/test_startup.py` (lines 179, 415, 431), `tests/agent/test_startup_memory_failures.py` (line 50), `tests/agent/test_startup_severity_classification.py` (lines 61, 297, 313, 325, 336).
  - These require modification and constitute **additional target file discovery** per `rules/workflow-lifecycle.md`; each needs a Plan amendment (scope row) before this row validates to completion.

## Design decisions
- Delete the "# 5. Routing drift (static)" comment block and its `try/except` (lines 169-179, i.e. the comment at 169-172 plus the `try`/`except` at 173-179), leaving the "5b. Routing safety tiers" step intact.
- Narrow the line-31 import to drop `check_routing_drift`, keeping `check_routing_safety_tiers`.

## Alternatives considered
- Keeping the call site behind a conditional: rejected because the function it calls is removed (row 16); a dead call site is worse than an absent one.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
Drop the routing-drift pipeline step and remove the now-unused import name.

### Method
- Delete the block from the `# 5. Routing drift (static)` comment through the `_record_drift_check_failure(pipeline, exc)` line (current lines 169-179, re-verify exact numbers).
- Change line 31 from `from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers` to `from agent.services.routing_drift import check_routing_safety_tiers`.

### Details
- Confirm `check_routing_safety_tiers` is still referenced (the "5b. Routing safety tiers" step) so the narrowed import resolves.
- Confirm no other `check_routing_drift` reference remains in `startup_validation.py`.
- Do NOT touch `check_routing_safety_tiers` wiring or `_record_drift_check_failure` (used elsewhere if at all — verify).

## Compatibility considerations
Backward incompatible by design (`REQ-004`): the startup pipeline no longer runs a config-based routing-drift step. Live-vs-registry drift detection persists via `mcp_tool_discovery.py:165`. Pipeline consumers asserting on a `routing_drift` stage must be updated (see CASCADE above).

## Security considerations
Fail-closed preserved: routing drift is still detected via the live-vs-registry path, fatal under strict mode (`REQ-006`). Removing the config step removes a weaker, config-source drift check.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the startup-validation suite. **Because `check_routing_drift` is removed, the following non-Plan test files must be updated (additional target file discovery → Plan amendment required):** `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_memory_failures.py`, `tests/agent/test_startup_severity_classification.py`. Also `tests/agent/test_startup_mcp_starter.py` (row 19). Consumer-scan for any other `check_routing_drift` reference.

## Completion criteria
`startup_validation.py` has no routing-drift pipeline step and no `check_routing_drift` import/reference; `check_routing_safety_tiers` still runs; the module imports cleanly.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py`, row 16), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `test_startup_mcp_starter.py` edit (row 19), and the additional-target-file test edits enumerated in the CASCADE note.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | CASCADE: ~5 non-Plan test files need amendments (see Cascade note). |
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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/startup_validation.py`
