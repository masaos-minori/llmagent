## Goal

Make `tool_policy.py` fail closed on empty safety lists: an empty `allowed_tools` denies every tool in `check_preflight`, and an empty `allowed_root` no longer skips the path checks in `check_allowed_root` and `_check_positional_args` (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

Edit `scripts/agent/tool_policy.py` and its companions `tests/agent/test_tool_policy.py` and `tests/agent/test_tool_policy_comprehensive.py`. The `/reload` side of REQ-002 is the `runtime_tool_registry.py` row.

## Assumptions

- Phase 4 of the Plan. Load-time rejection of an empty `allowed_root`/`allowed_tools` is in the validator and builder rows; this file is the runtime defense for paths that do not pass through them (`/reload` of the `approval` section uses `prepare_direct_section`, which copies fields without validation).
- Measured by experiment during Step 3a (changes reverted): deny-on-empty fails 44 tests in `test_tool_policy.py` and 6 in `test_tool_policy_comprehensive.py`, plus files that belong to other Plan rows (`test_tool_approval_preflight.py`, `test_tool_approval_paths.py`, `test_tool_approval_repos.py`, `test_tool_approval_risk.py`, `test_tool_runner.py`, `test_agent_repl_tool_exec.py`, `tests/integration/test_rag_turn_integration.py`). Their fixtures are updated by their own documents.
- Per the Plan (UNK-04), add the `/reload` test of an empty `allowed_tools` first (owned by the `tests/agent/services/test_config_reload.py` row) to confirm the live gap before changing behavior.
- `scripts/agent/wal_checkpoint_manager.py::_is_db_path_allowed` also returns True for an empty `allowed_root`; it is intentionally unchanged (Plan Assumptions).

## Design decisions

- Empty `allowed_tools` is an empty allowlist: `check_preflight` raises `PolicyViolationError("denied_allowed_tools", ...)` for every tool name; the audit decision string is unchanged so audit consumers keep working.
- Empty `allowed_root` denies a call that carries a path argument (`check_allowed_root` returns False) and classifies a path-bearing shell argv as `RiskLevel.HIGH`; a call with no path argument is not affected (nothing to confine).

## Alternatives considered

Denying every call when `allowed_root` is empty (even without path arguments) was rejected: it would make non-path tools unusable and is stricter than the jail's purpose. Treating an empty `allowed_root` as the filesystem root was rejected as an implicit allow-all.

## Implementation
### Target file
`scripts/agent/tool_policy.py`

### Procedure
1. In `check_preflight` (line 502) change the condition at line 513 to `if tool_name not in cfg.tool.allowed_tools:` and adjust the message to say the tool is not in `allowed_tools` (an empty list denies every tool).
2. In `check_allowed_root` (line 454) replace the early `return True` for an empty root (line 466) with: when the root is empty, return False if any path argument value exists (`_iter_path_arg_values` over `_resolve_path_keys(cfg, tool_name, registry)`), else True; keep the `_NotInspectablePathValueError` handling returning False. Update the docstring.
3. In `_check_positional_args` (line 259) replace `if cfg.approval.allowed_root:` (line 276) so an empty root returns `RiskLevel.HIGH` for a path candidate instead of skipping; keep the resolve/`is_relative_to` logic for a non-empty root.

### Method
- Edit by symbol and keep the function signatures unchanged (`check_allowed_root(cfg, tool_name, args, registry=None)`).
- Reuse `_iter_path_arg_values`; do not add a new helper unless the empty-root branch exceeds a few lines (if so, name it `_has_path_argument` (new) and add it before `check_allowed_root`).
- `rg -n "if cfg.tool.allowed_tools and|if not cfg.approval.allowed_root" scripts/agent/tool_policy.py` must return nothing afterwards.

### Details
- Both tests that assert the old behavior must be rewritten, not deleted: they become the REQ-002/REQ-003 acceptance tests (AC-02, AC-03).
- `check_preflight`'s ordering (allowed_tools first, then root jail) is unchanged.

### Companion test files
- `tests/agent/test_tool_policy.py`
  - Procedure: Give `_cfg` (line 44 and 53 defaults) a non-empty `allowed_tools` (a module constant `_POLICY_TEST_TOOLS` (new) covering every tool name the file passes) and a real `allowed_root` default such as `"/"`; rewrite `test_allowed_tools_none_does_not_block` (line 312) to assert denial for `allowed_tools=[]`; rewrite the empty-root cases (lines 229-232, 262-265, 302) to assert a path-bearing call is denied and a pathless call passes.
  - Validation: `uv run pytest tests/agent/test_tool_policy.py -v`
- `tests/agent/test_tool_policy_comprehensive.py`
  - Procedure: Replace the empty `allowed_root` default (line 54) with a real root and replace the empty-list allow-all cases with deny-all cases (REQ-002, REQ-003).
  - Validation: `uv run pytest tests/agent/test_tool_policy_comprehensive.py -v`

## Compatibility considerations

Behavior change for any config with an empty `allowed_tools` or `allowed_root`: such configs already fail at load (validator/builder rows) and now also fail closed at runtime after a reload. Shipped config is unaffected (non-empty both).

## Security considerations

Removes two "empty means allow all" paths (ADR-004 Decision Group 1). Fail-closed on a reloaded empty list; no new permissive branch.

## Rollback considerations

`git revert`; no persisted state.

## Validation plan

- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py -v`, then `uv run pytest tests/agent tests/shared tests/integration` to find fixture fallout (UNK-05); fixtures outside the Plan table are a Plan amendment.
- `uv run ruff format`/`ruff check` on the three files; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- An empty `allowed_tools` denies every tool in `check_preflight`; an empty `allowed_root` denies a path-bearing call and escalates a path-bearing shell argv to HIGH.
- Both companion tests assert the new behavior and their fixtures use non-empty defaults.

## Out of Scope

- `wal_checkpoint_manager.py` and `check_allowed_repo`.
- Fixture updates in other test files (own Plan rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Deny on empty `allowed_tools` in `check_preflight` | Pending | — | — | REQ-002 |
| 2 | Fail closed on empty `allowed_root` in `check_allowed_root` and `_check_positional_args` | Pending | — | — | REQ-003 |
| 3 | Update the two companion test files (non-empty fixture defaults; allow-all cases become deny-all) | Pending | — | — | REQ-002, REQ-003 |
| 4 | Run ruff, mypy, lint-imports and the agent/shared/integration test sweep | Pending | — | — | UNK-05 |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`
