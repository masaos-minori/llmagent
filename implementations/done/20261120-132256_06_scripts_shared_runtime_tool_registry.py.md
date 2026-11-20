## Goal

Make `RuntimeToolRegistry.apply_policy` mode-aware and denylist-aware with semantics identical to `check_preflight`, and add `tool_policy_mode` and `disabled_tools` inputs (`REQ-005`).

## Scope
**Release unit**: `apply_policy` signature change — adding `tool_policy_mode`/`disabled_tools` inputs invalidates every caller (`config_service_sync.sync_all`) and its direct-call tests until updated in the same commit; they cannot be validated alone.

## Assumptions
- `tool_policy_mode` is `discovered` or `explicit_allowlist` (validated upstream by `config_validators.py`).
- `disabled_tools` is a hard denylist applied in both modes.
- Base visibility in `discovered` mode is the registry's per-tool base visibility (`agent_safety_tier` / `llm_visibility_base`).

## Design decisions
- Extend the `apply_policy` signature (line 206) with two keyword parameters `tool_policy_mode` and `disabled_tools`, placed after `allowed_tools` so existing positional callers keep working and the new caller passes them by name.
- Replace the empty-sequence fail-closed branch (lines 214-216) with a mode-aware computation: `discovered` keeps base visibility minus `disabled_tools`; `explicit_allowlist` intersects with `allowed_tools` and fails closed on an empty list.

## Alternatives considered
- Keeping `allowed_tools=[]` as a blanket fail-closed signal: rejected because the plan makes emptiness valid in `discovered` mode; the mode now disambiguates intent.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
Add the two new parameters to `apply_policy` (line 206) and rewrite its visibility computation to branch on `tool_policy_mode`.

### Method
Mirror `check_preflight`'s branch; keep the two-phase apply contract used by `/reload`.

### Details
- Signature: add `tool_policy_mode: str` and `disabled_tools: Sequence[str]` after `allowed_tools: Sequence[str]`.
- `discovered`: visibility = base visibility for each tool minus any tool in `disabled_tools`.
- `explicit_allowlist`: visibility = tools in `allowed_tools`; an empty `allowed_tools` fails closed.

## Compatibility considerations
The signature change breaks `config_service_sync.sync_all` (line 76) and its direct-call tests; all update together in one commit (the release unit above).

## Security considerations
Failing closed on an empty allowlist preserves the fail-closed invariant; the denylist still hard-denies in both modes.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_runtime_tool_registry.py tests/shared/test_tool_routing_validation.py` confirms mode + denylist enforcement and reload reapplied via `_sync_services`.

## Completion criteria
`apply_policy` exposes the same semantics as `check_preflight`; after `/reload` the resolved visibility equals the freshly-started visibility (AC-04).

## Out of Scope
Caller wiring in `config_service_sync.py` (same commit) and preflight in `tool_policy.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-184200 | 20261120-184200 | Extended `apply_policy` signature with `tool_policy_mode="explicit_allowlist"`/`disabled_tools=()` kwargs after `allowed_tools` (existing positional callers keep working). Added a mode branch: explicit_allowlist keeps existing intersect-with-allowed_tools fail-closed; discovered keeps each tool's base visibility minus `disabled_tools`. Updated production caller `config_service_sync.sync_all` to pass both by name. ruff+mypy clean. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-184200 | 20261120-184200 | Added 3 discovered-mode cases to `test_runtime_tool_registry.py::TestRuntimeToolRegistry` (allow registered w/ empty allowlist, deny disabled_tool, honor llm_visibility_base=False). Updated `test_config_reload.py` mock assertion for new kwargs and set `tool_policy_mode="explicit_allowlist"`/`disabled_tools=[]` in `TestRuntimeToolPolicyReapplication._make_svc` (the class assumed explicit_allowlist REQ-002 semantics; MagicMock ctx previously returned a Mock mode value -> treated as discovered). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-184200 | 20261120-184200 | ruff format+check clean on all 4 files; mypy no new regressions; 1605 tests pass across tests/shared/ + tests/agent/services/ (incl. the 2 previously-failing real-registry paths). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Companion test files
- `tests/shared/test_tool_routing_validation.py`
  - Procedure: update `apply_policy` calls for the new signature and add mode/denylist cases.
  - Validation: `uv run pytest tests/shared/test_tool_routing_validation.py` passes.
- `tests/shared/test_runtime_tool_registry.py`
  - Procedure: update `apply_policy(tier_map={}, ...)` calls for the new signature; add mode cases.
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py` passes.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`, `tests/shared/test_runtime_tool_registry.py`
