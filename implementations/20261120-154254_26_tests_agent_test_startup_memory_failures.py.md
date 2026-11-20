## Goal

Drop the `check_routing_drift` dict-mock entry from `tests/agent/test_startup_memory_failures.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 17 (`startup_validation.py` scope row); once gone, the entry's patch target no longer resolves and `_run_check_services()` raises `AttributeError` at collection. Remove the entry; retain the sibling `check_routing_safety_tiers` entry so the pipeline still exercises the surviving step.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- One `check_routing_drift` entry lives in the `_run_check_services()` per-call mock dict (L41-53), patched generically via `mocks.update(overrides)` then iterated: line 50, sibling `"check_routing_safety_tiers"` at line 51.
- After removal, `patch`/`MagicMock` remain referenced; no import collapse needed.
- Minor: the `_run_check_services` docstring (L35) says "clean-pass mocks for all 5 patched checks"; after this edit there are 4 patched checks. This is a stale count, not a breakage.

## Design decisions
- Delete the `check_routing_drift` dict-mock entry (L50), leaving the `check_routing_safety_tiers` sibling (L51).
- Optionally correct the docstring count "5" → "4" (L35) to avoid a stale claim. Listed as optional; do it only if desired — it is not required to keep the suite green.

## Alternatives considered
- Keeping the entry behind a skip marker: rejected — `patch()` resolves the target at collection time; a skipped patch of a deleted symbol still raises `AttributeError`.

## Implementation
### Target file
`tests/agent/test_startup_memory_failures.py`

### Procedure
Remove the one `check_routing_drift` dict-mock entry; retain `check_routing_safety_tiers`.

### Method
In `_run_check_services()` (L41-53), delete:
```python
"check_routing_drift": MagicMock(return_value=[]),
```
leaving `"check_routing_safety_tiers": MagicMock(return_value=[]),`.

Optionally (not required for a green suite), change the docstring at L35 from "all 5 patched checks" to "all 4 patched checks".

### Details
- Confirm no `check_routing_drift` token remains anywhere in the file.
- Confirm the `check_routing_safety_tiers` entry (L51) remains.
- Do not touch `TestStartupMemoryFailures` test bodies.

## Compatibility considerations
Test-only change. Removes a dead mock for a removed function; the pipeline still runs `check_routing_safety_tiers`. No production compatibility impact.

## Security considerations
N/A: test-only. Removing the mock for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8) and `check_routing_safety_tiers` stays covered.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/test_startup_memory_failures.py` and assert the full suite collects and passes (no `AttributeError`).
- Confirm the `check_routing_drift` entry is gone and `check_routing_safety_tiers` remains.
- Run ruff on the file to confirm no unused-import warnings.

## Completion criteria
`test_startup_memory_failures.py` contains no `check_routing_drift` reference; the module collects cleanly; the memory-failure tests pass.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py` row 16, `startup_validation.py` row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the `tool_registry.py` docstring edit (row 18), the `test_startup_mcp_starter.py` config-drift test removals (row 19), and the cascade fixes to the other non-Plan startup test files (rows 23-25, 27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Remove after row 17 lands. Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Removes existing mock; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Optional docstring count correction (see Method). |

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
- **Related target files**: `tests/agent/test_startup_memory_failures.py`
