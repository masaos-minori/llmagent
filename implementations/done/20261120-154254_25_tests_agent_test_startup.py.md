## Goal

Drop every `check_routing_drift` reference from `tests/agent/test_startup.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 17 (`startup_validation.py` scope row); once gone, the dict-mock entry, the two kwargs, and any patch target referencing it break. Remove the dict-mock entry and the two `routing_drift (static)` tests that exercise it; retain the `routing_safety_tiers` tests so the pipeline still exercises the surviving step.

> **⚠️ Reviewer decision required — scope note.** The Plan's Evidence for this row enumerates THREE references (dict mock at 179, kwargs at 415 and 431) and implies only reference drops. Implementing that literally leaves `test_routing_drift_warning_on_messages` broken (it asserts a positive FATAL/WARNING `routing_drift` outcome that `check_config()` can no longer produce) and leaves `test_routing_drift_emits_no_outcome_when_clean` as a misleading vacuous check. This procedure removes both tests in addition to dropping the three references. This follows from the row's keep-the-suite-green goal, not an independent behavior change; approve the two removals or amend the Plan row.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- One `check_routing_drift` entry lives in the `_run_check_services()` per-call mock dict (L170-182), patched generically via `mocks.update(overrides)` then iterated. Dropping just the entry is safe; the sibling `"check_routing_safety_tiers"` at L180 stays.
- Two `TestCheckServicesSeverityClassification` methods under the `# ── routing_drift (static) ──` section header (L408) exercise `check_routing_drift`:
  - `test_routing_drift_warning_on_messages` (L410-422): drives `check_routing_drift=MagicMock(return_value=[...])`; asserts one `routing_drift` outcome with status WARNING. MUST remove — would fail (no `routing_drift` outcome produced once the symbol is gone).
  - `test_routing_drift_emits_no_outcome_when_clean` (L424-435): drives `check_routing_drift=MagicMock(return_value=[])`; asserts zero `routing_drift` outcomes. Would pass vacuously after removal, but its docstring describes `check_routing_drift` behavior that no longer exists; remove for clarity.
- Retained unchanged: `test_routing_safety_tiers_gap_is_fatal` (L439-452) and `test_routing_safety_tiers_emits_no_outcome_when_clean` (L454-463, `check_routing_safety_tiers`), plus `test_routing_drift_live_ok_when_clean` (L467+, which drives the LIVE path, not the removed static function).
- After removal, `patch`/`MagicMock` remain referenced; no import collapse needed.

## Design decisions
- Delete the `check_routing_drift` dict-mock entry (L179), leaving the `check_routing_safety_tiers` sibling (L180).
- Delete the two void `routing_drift (static)` methods (L410-422, L424-435).
- Remove the now-orphaned `# ── routing_drift (static) ──` section divider (L408), since no `routing_drift` test remains before the `routing_safety_tiers` section; leaving it above the safety-tier tests would be misleading. (Reviewer: if a future row re-adds static `routing_drift` tests, restore this divider.)

## Alternatives considered
- Keeping `test_routing_drift_emits_no_outcome_when_clean` by dropping only its kwarg: rejected — it becomes a misleading vacuous check whose docstring describes a removed function.
- Dropping only the three enumerated references and leaving both tests: rejected — `test_routing_drift_warning_on_messages` asserts a positive `routing_drift` outcome that no longer exists (fails).

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
Remove one `check_routing_drift` dict-mock entry and two void `routing_drift (static)` methods; drop the orphaned section divider.

### Method
1. In `_run_check_services()` (L170-182), delete:
   ```python
   "check_routing_drift": MagicMock(return_value=[]),
   ```
   leaving `"check_routing_safety_tiers": MagicMock(return_value=[]),`.
2. Delete `test_routing_drift_warning_on_messages` (L410-422) and `test_routing_drift_emits_no_outcome_when_clean` (L424-435), including the `# ── routing_drift (static) ──` divider (L408) directly above them.
3. Confirm no `check_routing_drift` token remains anywhere in the file.

### Details
- Confirm the `check_routing_safety_tiers` dict entry (L180) and both safety-tier test methods remain.
- Confirm `test_routing_drift_live_ok_when_clean` (the live-path test) is untouched — it does not use the removed static function.
- Do not touch `TestStartupOrchestratorSetupPrompt`, `TestStartupMemoryFailures`, `TestBuildAgentConfigErrorPath`, or other classes.

## Compatibility considerations
Test-only change. Removes dead/void tests for a removed function and a dead dict-mock entry; the `routing_safety_tiers` and live-path tests are unchanged. No production compatibility impact.

## Security considerations
N/A: test-only. Removing tests for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8) and `check_routing_safety_tiers` stays covered.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/test_startup.py` and assert the full suite collects and passes (no `AttributeError`, no missing-`routing_drift`-outcome failures).
- Confirm the two named tests are gone and both `routing_safety_tiers` tests remain.
- Run ruff on the file to confirm no unused-import warnings.

## Completion criteria
`test_startup.py` contains no `check_routing_drift` reference; the module collects cleanly; the `routing_safety_tiers` and live-path tests pass.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py` row 16, `startup_validation.py` row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), and the cascade fixes to the other non-Plan startup test files (rows 26-27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Removed the `check_routing_drift` dict-mock entry from `_run_check_services()` (leaving the `check_routing_safety_tiers` sibling) and the two void `routing_drift (static)` methods (`test_routing_drift_warning_on_messages`, `test_routing_drift_emits_no_outcome_when_clean`) together with the orphaned `# ── routing_drift (static) ──` section divider. Used a line-range deletion for the divider+methods block because the divider's box-drawing run prevented reliable literal matching. No `check_routing_drift` token remains; `routing_safety_tiers` tests and the live-path `test_routing_drift_live_ok_when_clean` untouched. The L142 comment listing pipeline sources (including the `routing_drift` source name) is retained — it names the pipeline source, not the removed function. |
| 2 | Add or update tests per Validation plan | N/A | — | — | Removes existing/void tests; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff format/check clean; target suite `tests/agent/test_startup.py` collects and passes (37 passed). Full-suite regression diff DEFERRED to the `_16`–`_27` coupled-unit final check. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only. |

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
- **Related target files**: `tests/agent/test_startup.py`
