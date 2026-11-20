## Goal

Add `/reload` contract tests for both `tool_policy_mode` values, empty/unknown mode, and tool visibility preserved after `/reload` (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_sync_services()` re-applies `RuntimeToolRegistry.apply_policy()` after a successful reload (existing behavior around line 626-640).
- The existing `REQ-002` reload test and the `_sync_services` refactor fixture are in this file.

## Design decisions
- Extend the existing reload test class with cases that set `tool_policy_mode` and `disabled_tools` on the reload payload and assert the post-reload visibility matches the freshly-started visibility for each mode.

## Alternatives considered
- A separate test module: rejected because the reload machinery lives in this file's fixture and the plan lists this file as the reload contract home.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`

### Procedure
Add reload contract tests that reload with `tool_policy_mode`/`disabled_tools` set and assert post-reload visibility equals the fresh start for each mode.

### Method
Reuse the existing reload fixture; set the new fields on the reload payload; compare `apply_policy` output before and after reload.

### Details
- Reload with `tool_policy_mode="discovered"` + empty `allowed_tools` + a `disabled_tools` entry; assert base visibility minus denylist is unchanged after reload.
- Reload with `tool_policy_mode="explicit_allowlist"` + a non-empty `allowed_tools`; assert the allowlist visibility is unchanged after reload.
- Reload with an unknown `tool_policy_mode`; assert the reload is rejected and the previous value survives.

## Compatibility considerations
Purely additive tests; existing reload tests are preserved.

## Security considerations
No security impact: these tests verify reload atomicity and mode parity, not enforcement logic.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/services/test_config_reload.py` confirms both modes reload atomically with identical visibility.

## Completion criteria
The reload contract tests pass for both modes, empty/unknown mode, and visibility preservation (AC-04, AC-05).

## Out of Scope
The reload transaction itself (`config_reload.py`) and `apply_policy` (`runtime_tool_registry.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-190500 | 20261120-190500 | Added 3 reload contract tests to `TestRuntimeToolPolicyReapplication` in `tests/agent/services/test_config_reload.py`: discovered-mode base visibility minus denylist, explicit_allowlist allowlist preservation, and unknown-mode rejection with previous mode surviving. `_bound_registry` binds a real `RuntimeToolRegistry` (typed return) so `apply_policy` results are asserted against live tool visibility. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-190500 | 20261120-190500 | Tests cover REQ-005 (mode-specific visibility preserved across `/reload`) and REQ-006 (unknown mode rejected atomically, previous mode survives). Empty `allowed_tools` valid in discovered mode; `disabled_tools` still a hard denylist. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-190500 | 20261120-190500 | ruff format/check clean; pytest 72 passed in test_config_reload.py (incl. new 3); 328 tests/agent/services + 76 shared runtime-tool tests pass; project mypy (configured files) success, no issues in 573 files. No regressions. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `tests/agent/services/test_config_reload.py`
