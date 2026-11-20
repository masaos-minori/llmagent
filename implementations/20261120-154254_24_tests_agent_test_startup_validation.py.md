## Goal

Drop every `check_routing_drift` reference from `tests/agent/test_startup_validation.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 17 (`startup_validation.py` scope row); once gone, the dict-mock entries, kwargs, the `patch("agent.startup_validation.check_routing_drift", ...)`, and the `startup_validation.check_routing_drift` attribute access all break (collection `AttributeError` or assertion failure). Remove the references AND the tests that become void; retain the `check_routing_safety_tiers`-driven tests so the pipeline still exercises the surviving step.

> **⚠️ Reviewer decision required — scope note.** The Plan's Evidence for this row enumerates EIGHT references (dict-mocks at 72/120/460, kwargs at 142/157/202, patch at 241, attribute access at 266) and states "pipeline still exercises check_routing_safety_tiers". Implementing that literally leaves FIVE tests broken, because four of them assert a `routing_drift` outcome that `check_config()` can no longer produce (row 17 deletes the call site), and one patches a symbol that no longer exists. This procedure therefore removes those five tests in addition to the eight references. This is a consequence of the row's own goal (keep the suite green), not an independent behavior change, but it is larger than the enumerated Evidence. Approve the five removals below, or amend the Plan row to list them.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Three `check_routing_drift` entries live in per-call mock dicts that are patched generically (`for name, mock_obj in mocks.items(): stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))`). Dropping just the dict entry is safe; the surrounding dict and its `check_routing_safety_tiers` sibling stay:
  - `_run_check_services()` mocks dict: line 72 (`"check_routing_drift": MagicMock(return_value=[])`), sibling `"check_routing_safety_tiers"` at line 73.
  - `_run_check_config()` mocks dict: line 120, sibling at line 121.
  - `test_runtime_registry_published_after_posture_gate()` mocks dict: line 460, sibling at line 461.
- Four `TestCheckConfigStage` methods EXCLUSIVELY exercise `check_routing_drift` and MUST be removed (they would otherwise fail collection or assertions once the symbol is gone):
  - `test_routing_drift_is_fatal` (L135-148): drives `check_routing_drift=MagicMock(side_effect=RuntimeError(...))`; asserts a FATAL `routing_drift` outcome.
  - `test_drift_check_unexpected_exception_is_fatal` (L150-164): drives `check_routing_drift=MagicMock(side_effect=ValueError(...))`; asserts a FATAL `routing_drift` outcome.
  - `test_config_checks_report_together_without_short_circuit` (L193-209): drives `check_routing_drift=MagicMock(side_effect=RuntimeError("drift detected"))`; asserts `"routing_drift" in fatal_sources`.
  - `test_unregistered_routed_tool_is_fatal` (L258-271): passes `check_routing_drift=startup_validation.check_routing_drift` (real symbol, attribute access at L266); asserts a FATAL `routing_drift` outcome.
- `test_runtime_stage_no_longer_runs_config_checks` (L211-255) verifies that `check_services()` never calls `check_routing_drift` by patching it (L241) and asserting `recording.assert_not_called()`. Its premise is void once `check_routing_drift` is deleted (the patch target no longer resolves), so it is removed too. Its assertion (`no routing_drift outcome`) remains true but is now vacuous.
- Tests retained unchanged: `test_safety_tier_failure_is_fatal` (L167-178, `check_routing_safety_tiers`), `test_valid_config_passes_cleanly` (L180-191, no overrides), `test_tool_missing_from_safety_tiers_is_fatal` (L273-287, `check_routing_safety_tiers`), `TestToolDiscoveryFatalSkipsRagCheck`, `test_runtime_registry_published_after_posture_gate` (after the L460 entry drop), and `TestMcpAuthDisabledServers`.
- After removal, `import agent.startup_validation as startup_validation` (L19) is still used (e.g. `startup_validation.check_routing_safety_tiers` at L281), and `patch`/`MagicMock` remain referenced. No import collapse needed.

## Design decisions
- Delete the three `check_routing_drift` dict-mock entries, leaving each sibling `check_routing_safety_tiers` entry.
- Delete the five void `TestCheckConfigStage` methods wholesale (their `@pytest.mark.asyncio` decorator through their last assert), leaving the retained methods byte-for-byte.
- Do NOT touch any `check_routing_safety_tiers` reference, nor any non-`TestCheckConfigStage` code beyond the three dict entries.

## Alternatives considered
- Keeping the five tests behind a skip marker: rejected — the kwargs/patch/attribute references still resolve at decoration/collection time and raise before a skip can apply.
- Dropping only the eight enumerated references and leaving the tests: rejected — four would assert a non-existent `routing_drift` outcome (fail), one would `AttributeError` on the patch target. Violates the row's keep-the-suite-green goal.
- Rewriting the five tests against `check_routing_safety_tiers` or the live `validate_routing_against_live()` path: rejected — out of scope for a fallout cleanup; rewrites belong to a feature row.

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
Remove three `check_routing_drift` dict-mock entries and five void `TestCheckConfigStage` methods; retain all `check_routing_safety_tiers`-driven tests.

### Method
1. In `_run_check_services()` (L69-75), delete the line:
   ```python
   "check_routing_drift": MagicMock(return_value=[]),
   ```
   leaving `"check_routing_safety_tiers": MagicMock(return_value=[]),` as the drift-stage entry.
2. In `_run_check_config()` (L119-123), delete the same dict line (L120), leaving the `check_routing_safety_tiers` sibling.
3. In `test_runtime_registry_published_after_posture_gate()` (L457-466), delete the dict line (L460), leaving the `check_routing_safety_tiers` sibling (L461).
4. Delete these five methods from `TestCheckConfigStage` (decorator through last assert):
   - `test_routing_drift_is_fatal` (L135-148)
   - `test_drift_check_unexpected_exception_is_fatal` (L150-164)
   - `test_config_checks_report_together_without_short_circuit` (L193-209)
   - `test_runtime_stage_no_longer_runs_config_checks` (L211-255)
   - `test_unregistered_routed_tool_is_fatal` (L258-271)

### Details
- Confirm no `check_routing_drift` token remains anywhere in the file (no dict key, kwarg, patch target, attribute access, or comment).
- Confirm the three `check_routing_safety_tiers` dict entries (L73, L121, L461) and the two safety-tier test methods remain.
- Confirm `agent.startup_validation` import and `patch`/`MagicMock` imports are still referenced.
- Do not touch `TestToolDiscoveryFatalSkipsRagCheck`, `test_runtime_registry_published_after_posture_gate` body, `TestMcpAuthDisabledServers`, or any class outside `TestCheckConfigStage`.

## Compatibility considerations
Test-only change. Removes dead/void tests for a removed function and dead dict-mock entries; the surviving `check_routing_safety_tiers` tests are unchanged. No production compatibility impact.

## Security considerations
N/A: test-only. Removing tests for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8) and `check_routing_safety_tiers` stays covered.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/test_startup_validation.py` and assert the full suite collects and passes (no `AttributeError`, no missing-`routing_drift`-outcome failures).
- Confirm the five named tests are gone and `test_safety_tier_failure_is_fatal` / `test_tool_missing_from_safety_tiers_is_fatal` remain.
- Run ruff on the file to confirm no unused-import warnings.

## Completion criteria
`test_startup_validation.py` contains no `check_routing_drift` reference; the module collects cleanly; the `check_routing_safety_tiers`-driven tests pass.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py` row 16, `startup_validation.py` row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `test_startup_mcp_starter.py` config-drift test removals (row 19), and the cascade fixes to the other non-Plan startup test files (rows 25-27). The `tool_names` argument in `test_unregistered_routed_tool_is_fatal`'s server mock is also gone with that test; no standalone cleanup remains.

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
- **Related target files**: `tests/agent/test_startup_validation.py`
