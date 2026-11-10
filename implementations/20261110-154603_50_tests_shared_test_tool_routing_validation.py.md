## Goal
Update the `apply_policy` tests in `tests/shared/test_tool_routing_validation.py` for the deny-on-empty semantics added by row 75 (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Row 75 changes `RuntimeToolRegistry.apply_policy` so an empty `allowed_tools` leaves every tool `enabled_for_llm=False`; two tests here assert the old allow-all result.
- Tests that call `apply_policy(tier_map=...)` without `allowed_tools` (lines 179, 189) assert only the tier, so they need no change; the implementer confirms by running the file.
- Phase 4.

## Design decisions
- Invert, do not delete: the empty-list contract is part of INV-005 and must stay tested.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/shared/test_tool_routing_validation.py`

### Procedure
- `test_apply_policy_empty_allowed_tools_keeps_all_enabled` (starting at line 164): rename to `test_apply_policy_empty_allowed_tools_disables_all` (new), update the docstring, and assert `reg.get("search_web").enabled_for_llm is False`.
- `test_atomic_single_swap_per_call` (around line 358): the call with `allowed_tools=[]` ends with `assert reg.get("shell_run").enabled_for_llm is True`; change the call to `allowed_tools=["shell_run"]` so the test still checks one swap per call and the enabled state.

### Method
- Keep `build_fixture_runtime_tool` and `_registry_with` usage as is.
- Other `apply_policy` calls pass non-empty lists and are unchanged.

### Details
- Row 49 (`tests/shared/test_runtime_tool_registry.py`) covers the same method for its own file; do not duplicate its cases here.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/shared/test_tool_routing_validation.py -v`

## Completion criteria
- No test asserts that an empty `allowed_tools` keeps tools enabled.
- The file passes against the new `apply_policy`.

## Out of Scope
- Changing `apply_policy` itself (row 75).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/shared/test_tool_routing_validation.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/shared/test_tool_routing_validation.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (empty `allowed_tools` denies, also after `/reload`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/shared/test_tool_routing_validation.py`
