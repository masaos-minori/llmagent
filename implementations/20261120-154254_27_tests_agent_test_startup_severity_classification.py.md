## Goal

Drop every `check_routing_drift` reference from `tests/agent/test_startup_severity_classification.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 17 (`startup_validation.py` scope row); once gone, the dict-mock entry and the four kwargs referencing it break (collection `AttributeError` or assertion failure). Remove the dict-mock entry and the four `routing_drift (static)` tests that exercise it; retain the `routing_safety_tiers` tests so the pipeline still exercises the surviving step.

> **⚠️ Reviewer decision required — scope note.** The Plan's Evidence for this row enumerates FOUR references (dict mock at 61, kwargs at 297/313/325/336) and implies only reference drops. Implementing that literally leaves FOUR tests broken: three assert positive FATAL/WARNING `routing_drift` outcomes that `check_config()` can no longer produce, and one is a misleading vacuous check. This procedure removes all four tests in addition to dropping the four references. This follows from the row's keep-the-suite-green goal, not an independent behavior change; approve the four removals or amend the Plan row.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- One `check_routing_drift` entry lives in the `_make_startup_ctx`/`_run_check_config` mock dict (L61), sibling `"check_routing_safety_tiers"` at L62.
- Four `TestCheckServicesSeverityClassification` methods under the `# ── routing_drift (static) ──` section header (L290) exercise `check_routing_drift`:
  - `test_routing_drift_warning_on_messages` (L292-304): drives `check_routing_drift=MagicMock(return_value=[...])`; asserts one WARNING `routing_drift` outcome. MUST remove.
  - `test_routing_drift_emits_no_outcome_when_clean` (L306-317): drives `check_routing_drift=MagicMock(return_value=[])`; asserts zero `routing_drift` outcomes. Would pass vacuously after removal, but its docstring describes a removed function; remove for clarity.
  - `test_routing_drift_unexpected_failure_is_fatal` (L319-329): drives `check_routing_drift=MagicMock(side_effect=ValueError("boom"))`; asserts a FATAL `routing_drift` outcome. MUST remove.
  - `test_routing_drift_runtime_error_is_fatal` (L331-340): drives `check_routing_drift=MagicMock(side_effect=RuntimeError("drift detected"))`; asserts a FATAL `routing_drift` outcome. MUST remove.
- Retained unchanged: `test_routing_safety_tiers_gap_is_fatal` (L344-357), `test_routing_safety_tiers_emits_no_outcome_when_clean` (L359-368), `test_routing_safety_tiers_unexpected_failure_is_fatal` (L370+), all `check_routing_safety_tiers`.
- After removal, `patch`/`MagicMock` remain referenced; no import collapse needed.

## Design decisions
- Delete the `check_routing_drift` dict-mock entry (L61), leaving the `check_routing_safety_tiers` sibling (L62).
- Delete the four void `routing_drift (static)` methods (L292-304, L306-317, L319-329, L331-340), including the `# ── routing_drift (static) ──` divider (L290) directly above them.
- Leave all `routing_safety_tiers` methods and the `# ── routing_safety_tiers ──` section intact.

## Alternatives considered
- Keeping `test_routing_drift_emits_no_outcome_when_clean` by dropping only its kwarg: rejected — it becomes a misleading vacuous check whose docstring describes a removed function.
- Dropping only the four enumerated references and leaving the tests: rejected — three assert positive `routing_drift` outcomes that no longer exist (fail).

## Implementation
### Target file
`tests/agent/test_startup_severity_classification.py`

### Procedure
Remove one `check_routing_drift` dict-mock entry and four void `routing_drift (static)` methods; drop the orphaned section divider.

### Method
1. Delete the `check_routing_drift` dict-mock entry (L61):
   ```python
   "check_routing_drift": MagicMock(return_value=[]),
   ```
   leaving `"check_routing_safety_tiers": MagicMock(return_value=[]),`.
2. Delete these four methods (decorator through last assert):
   - `test_routing_drift_warning_on_messages` (L292-304)
   - `test_routing_drift_emits_no_outcome_when_clean` (L306-317)
   - `test_routing_drift_unexpected_failure_is_fatal` (L319-329)
   - `test_routing_drift_runtime_error_is_fatal` (L331-340)
   together with the `# ── routing_drift (static) ──` divider (L290) above them.
3. Confirm no `check_routing_drift` token remains anywhere in the file.

### Details
- Confirm the `check_routing_safety_tiers` dict entry (L62) and all safety-tier test methods remain.
- Do not touch any class outside `TestCheckServicesSeverityClassification`, nor the `routing_safety_tiers` section.

## Compatibility considerations
Test-only change. Removes dead/void tests for a removed function and a dead dict-mock entry; the `routing_safety_tiers` tests are unchanged. No production compatibility impact.

## Security considerations
N/A: test-only. Removing tests for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8) and `check_routing_safety_tiers` stays covered.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/test_startup_severity_classification.py` and assert the full suite collects and passes (no `AttributeError`, no missing-`routing_drift`-outcome failures).
- Confirm the four named tests are gone and all `routing_safety_tiers` tests remain.
- Run ruff on the file to confirm no unused-import warnings.

## Completion criteria
`test_startup_severity_classification.py` contains no `check_routing_drift` reference; the module collects cleanly; the `routing_safety_tiers` tests pass.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py` row 16, `startup_validation.py` row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `test_startup_mcp_starter.py` config-drift test removals (row 19), and the cascade fixes to the other non-Plan startup test files (rows 23-26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Remove after row 17 lands. Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Removes existing/void tests; no new tests required. |
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
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
