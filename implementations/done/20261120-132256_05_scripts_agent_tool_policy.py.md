## Goal

Make `check_preflight` mode-aware with semantics identical to `apply_policy`: in `discovered` mode allow every registered tool except those in `disabled_tools`; in `explicit_allowlist` mode allow only `allowed_tools` names and fail closed on an empty list (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `cfg.tool.tool_policy_mode` is already resolved to `discovered` or `explicit_allowlist` (validated by `config_validators.py`).
- Base visibility in `discovered` mode is the set of registered tools from `RuntimeToolRegistry`; the optional `registry` argument of `check_preflight` supplies it.
- `disabled_tools` is a hard denylist applied in both modes.

## Design decisions
- Replace the unconditional `if tool_name not in cfg.tool.allowed_tools` check (line 558) with a branch on `cfg.tool.tool_policy_mode`.
- `explicit_allowlist`: keep the membership check; an empty `allowed_tools` fails closed (unchanged behavior).
- `discovered`: allow the tool when it is a registered tool and not in `disabled_tools`; an empty `allowed_tools` is valid here.

## Alternatives considered
- Adding a separate deny-only path before the allowlist check: rejected because the plan requires the two modes to be mutually exclusive branches with identical end semantics to `apply_policy`.

## Implementation
### Target file
`scripts/agent/tool_policy.py`

### Procedure
In `check_preflight` (line 547), replace the unconditional `allowed_tools` membership denial at line 558 with a mode-aware branch.

### Method
Branch on `cfg.tool.tool_policy_mode`; keep the root-jail and repo checks unchanged below it.

### Details
- `explicit_allowlist` branch: raise `PolicyViolationError("denied_allowed_tools")` unless `tool_name in cfg.tool.allowed_tools` (empty list fails closed).
- `discovered` branch: raise unless `tool_name` is a registered tool (base visibility) and not in `cfg.tool.disabled_tools`.

## Compatibility considerations
In `explicit_allowlist` mode (the current effective runtime) behavior is unchanged; `discovered` mode now permits registered tools with an empty `allowed_tools`.

## Security considerations
Failing closed on an empty allowlist preserves the fail-closed invariant; the denylist still hard-denies in both modes.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py` confirms per-mode allow/deny.

## Completion criteria
`check_preflight` allows/denies exactly per AC-03 for both modes; the preflight contract tests pass.

## Out of Scope
Runtime application in `runtime_tool_registry.py` (identical semantics implemented there).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-183215 | 20261120-183215 | Replaced the unconditional `allowed_tools` denial in `check_preflight` with a mode-aware branch: explicit_allowlist keeps the existing `denied_allowed_tools` path; discovered allows registered tools not in `disabled_tools` (fail-closed when registry None). Uses `{t.name for t in registry.all_tools()}` (RuntimeToolRegistry has no `get_all_tool_names`). ruff+mypy clean. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-183215 | 20261120-183215 | Added TestCheckPreflight._reg_with helper + 4 discovered-mode cases (allow registered, deny unregistered, allow empty allowed_tools, deny disabled) to test_tool_policy.py; 3 matching cases to test_tool_policy_comprehensive.py. REQ-004 empty-allowlist-in-discovered covered. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-183215 | 20261120-183215 | ruff format+check clean on both files; mypy no new regressions (23 pre-existing SimpleNamespace/_extract_resource_scope errors unchanged vs HEAD); 401 tool_policy + 154 comprehensive + 199 caller (tool_runner/approval_preflight/gateway/preparation) tests pass. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Companion test files
- `tests/agent/test_tool_policy.py`
  - Procedure: add mode-aware `check_preflight` cases for both modes and the denylist; preserve existing coverage.
  - Validation: `uv run pytest tests/agent/test_tool_policy.py` passes.
- `tests/agent/test_tool_policy_comprehensive.py`
  - Procedure: extend `_cfg(n)`-driven coverage across both modes and the denylist.
  - Validation: `uv run pytest tests/agent/test_tool_policy_comprehensive.py` passes.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`
