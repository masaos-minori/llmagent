## Goal

Make `RuntimeToolRegistry.apply_policy` deny every tool for an empty `allowed_tools`, so `/reload` cannot re-enable all tools through an empty list (REQ-002 "including after `/reload`").

## Scope
**Release unit**: N/A: not part of a release unit

Edit `scripts/shared/runtime_tool_registry.py` and its companion `tests/shared/test_runtime_tool_registry.py`. This row was added to the Plan by amendment (fallout of REQ-002) during Step 3a verification.

## Assumptions

- Phase 4 of the Plan. The reload path calls `apply_policy(tier_map=..., allowed_tools=ctx.cfg.tool.allowed_tools)` (`scripts/agent/services/config_service_sync.py`), and `apply_policy` treats an empty sequence as allow-all (`allowed_alone = not allowed_tools or name in allowed_tools`), which is the live gap behind REQ-002.
- The only production caller is `config_service_sync.py`; it passes `allowed_tools` explicitly, so making the parameter required changes no call site. Tests that omit it are updated in the companion file.
- At startup `enabled_for_llm` is not derived from `allowed_tools`; only the reload path does. Startup enforcement is `tool_policy.check_preflight` (the `tool_policy.py` row).

## Design decisions

- `allowed_tools` becomes a required argument and `allowed_alone = name in allowed_tools`: an empty sequence hides every tool from the LLM, matching `check_preflight`.
- A required parameter, not a default of `()`, so no caller can get allow-all by omission.

## Alternatives considered

Keeping the `()` default with deny semantics was rejected: it would silently hide every tool for callers that only wanted to set tiers (the tests at lines 210 and 219 do so); making the argument explicit exposes that choice.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
1. Change the signature of `apply_policy` (line 206) to `allowed_tools: Sequence[str]` with no default.
2. Change `allowed_alone` (line 223) to `name in allowed_tools`.
3. Rewrite the docstring (lines 212-218): an empty sequence means no tool is allowed; remove the sentence that mirrors the old "empty means all" convention.

### Method
- Keep the `logger.warning` branch for hidden tools (`not resolved_llm_visibility_base and allowed_alone`) unchanged.
- `rg -n "not allowed_tools" scripts/shared/runtime_tool_registry.py` must return nothing afterwards; confirm the only production caller with `rg -n "apply_policy" scripts`.

### Details
- The module docstring (line 12) mentions `apply_policy()` taking duck-typed primitives; it stays accurate.

### Companion test files
- `tests/shared/test_runtime_tool_registry.py`
  - Procedure: Rewrite `test_apply_policy_empty_allowed_tools_keeps_all_enabled` (line 161) as an empty-denies-all test (rename to `test_apply_policy_empty_allowed_tools_disables_all` (new)); pass an explicit `allowed_tools` in the two tier-only calls (lines 210 and 219) and in any other call that omitted it.
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py tests/agent/services/test_config_reload.py -v`

## Compatibility considerations

Signature change: calls without `allowed_tools` raise `TypeError`; the only production caller already passes it. Runtime effect: a reload with an empty `allowed_tools` now hides all tools instead of exposing all.

## Security considerations

Closes the reload-path allow-all gap for `allowed_tools` (ADR-004 Decision Group 1); fail closed.

## Rollback considerations

`git revert`; no persisted state.

## Validation plan

- `uv run pytest tests/shared/test_runtime_tool_registry.py tests/agent/services/test_config_reload.py tests/shared/test_tool_routing_validation.py -v`.
- `uv run ruff format`/`ruff check` on both files; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- `apply_policy` requires `allowed_tools` and disables every tool for an empty sequence; the companion test asserts it.

## Out of Scope

- `config_service_sync.py` (unchanged) and the `tool_policy.py` runtime check (own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make `allowed_tools` required and deny on empty in `apply_policy` | Pending | — | — | REQ-002 |
| 2 | Update the companion test file (deny-all case, explicit arguments) | Pending | — | — | REQ-002 |
| 3 | Run ruff, mypy, lint-imports and the registry and reload tests | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_runtime_tool_registry.py`
