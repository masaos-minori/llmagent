## Goal

Drop all ten `patch("agent.startup_validation.check_routing_drift", ...)` sites from `tests/agent/shared/test_startup_validation_pipeline.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 17 (`startup_validation.py` scope row); once gone, `patch("agent.startup_validation.check_routing_drift")` raises `AttributeError` at collection and the whole pipeline test file fails to collect. Remove the ten patch entries; keep every adjacent `check_routing_safety_tiers` patch, which exercises the surviving step.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Current source has TEN `check_routing_drift` patch sites, all of the form `patch(f"{MODULE}.check_routing_drift", return_value=[])` with `MODULE = "agent.startup_validation"` (line 20):
  - NINE single-line entries, each on its own line: lines 127, 162, 209, 239, 268, 381, 412, 499, 534.
  - ONE multi-line entry at lines 452-455:
    ```python
    patch(
        f"{MODULE}.check_routing_drift",
        return_value=[],
    ),
    ```
- Every one of these sits immediately before a `patch(f"{MODULE}.check_routing_safety_tiers", return_value=[])` entry. The `check_routing_safety_tiers` patches are retained (the symbol survives; `test_check_routing_safety_tiers_context` at line 321 exercises it directly, and it appears 15 times total).
- After removal, `patch` is still imported and used (for `check_readiness`, `McpToolDiscoveryService`, `RagMaintenanceService`, etc.), so the `unittest.mock` import stays.
- No other `check_routing_drift` reference exists in this file (no import, no dict-mock, no attribute access).
- Ordering dependency: these patches must be removed AFTER row 17 lands (which deletes the `check_routing_drift` call site + import from `startup_validation.py`). If removed first, the real `check_routing_drift` would run under test; since row 17 removes the call site, the pipeline never invokes it again, so dropping the mock is behavior-preserving.

## Design decisions
- Delete each of the ten `check_routing_drift` patch entries (the nine single-line lines and the four-line multi-line block), leaving the surrounding `with (...)` context managers intact.
- Leave every `check_routing_safety_tiers` patch and all other patches byte-for-byte.

## Alternatives considered
- Keeping the patches behind a skip marker: rejected because `patch()` evaluates the target string at decoration/collection time; a skipped patch of a deleted symbol still raises `AttributeError`.
- Rewriting the pipeline to re-introduce a live drift step: out of scope; the config-based drift path is intentionally eliminated.

## Implementation
### Target file
`tests/agent/shared/test_startup_validation_pipeline.py`

### Procedure
Remove the ten `check_routing_drift` patch entries; retain all `check_routing_safety_tiers` patches.

### Method
1. Delete the nine single-line entries matching exactly:
   ```python
   patch(f"{MODULE}.check_routing_drift", return_value=[]),
   ```
   (use a global replace on that exact line, honoring indentation — they appear indented at both 8 and 12 spaces).
2. Delete the multi-line block at lines 452-455:
   ```python
   patch(
       f"{MODULE}.check_routing_drift",
       return_value=[],
   ),
   ```
3. Verify no `check_routing_drift` token remains anywhere in the file.

### Details
- Confirm the adjacent `check_routing_safety_tiers` patches remain untouched (they drive the surviving config-stage step).
- Confirm `patch` is still referenced elsewhere (it is) so the import resolves.
- Do not modify any test body, the `mock_ctx`/`startup_instance` fixtures, or the `Test*Scenario` classes beyond the ten deletions.

## Compatibility considerations
Test-only change. Removes dead mocks for a removed function; the pipeline still runs `check_routing_safety_tiers`. No production compatibility impact.

## Security considerations
N/A: test-only. Removing mocks for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/shared/test_startup_validation_pipeline.py` and assert the full suite collects and passes (no `AttributeError` at collection).
- Confirm the ten `check_routing_drift` patches are gone and `check_routing_safety_tiers` patches remain.
- Run ruff on the file to confirm no unused-import or unused-variable warnings.

## Completion criteria
`test_startup_validation_pipeline.py` contains no `check_routing_drift` reference; the module collects cleanly; the pipeline tests pass while still exercising `check_routing_safety_tiers`.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py` row 16, `startup_validation.py` row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `test_startup_mcp_starter.py` config-drift test removals (row 19), and the cascade fixes to the other non-Plan startup test files (rows 24-27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Remove after row 17 lands (ordering dependency). Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Removes existing mocks; no new tests required. |
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
- **Related target files**: `tests/agent/shared/test_startup_validation_pipeline.py`
