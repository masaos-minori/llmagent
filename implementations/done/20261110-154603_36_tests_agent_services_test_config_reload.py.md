## Goal
Update the field-registry expectations of `tests/agent/services/test_config_reload.py` for the removed keys and add reload tests proving that an empty `allowed_tools` (and `allowed_root`) fails closed after `/reload` (`REQ-002`, `REQ-003`; Plan Phase 4 says the reload test comes first).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `/reload` re-applies the tool policy through `ConfigReloadService._sync_services` -> `RuntimeToolRegistry.apply_policy` (`scripts/agent/services/config_service_sync.py:76-81`); row 75 makes that method disable every tool for an empty list. `prepare_validated_section` does not call `ProductionConfigValidator` (Plan Background), so the reload path is where the runtime deny must hold (UNK-04).
- UNK-04 is resolved by writing the reload tests first (Step 1) and observing whether `apply_config_dict` already rejects an empty list; the assertions below are written for both outcomes and the implementer keeps the one that holds.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).

## Design decisions
- Test the observable fail-closed outcome (tool denied / `enabled_for_llm` False), not the internal branch, so the tests survive either defense layer.
- Use the existing real-`RuntimeToolRegistry` pattern (lines 575-615) instead of the `MagicMock` registry, because the mock cannot show the visibility result.

## Alternatives considered
Asserting only that `apply_policy` is called with `allowed_tools=[]` (the current `test_apply_policy_called_with_current_tier_map_and_allowed_tools`, line 544): rejected because it passes whether or not the empty list denies.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`

### Procedure
- Registry expectations: in `test_tool_section_fields_are_classified_correctly` remove `"tool_definitions_strict"` (line 869) and `"routing_drift_strict"` (line 875) from `expected`.
- In `test_mcp_section_fields_are_classified_correctly` (around lines 917-927) change `expected = {"security_profile"}` to `expected: set[str] = set()` (the `mcp` section keeps no field after row 04 removes the entry); do not delete the test.
- New test A (class `TestRuntimeToolPolicyReapplication`, after line 612): build the real registry as in lines 575-607 with tools `read_file` and `delete_file`, set `ctx.cfg.tool.allowed_tools = []`, call `svc._sync_services(...)`, assert both tools have `enabled_for_llm is False`.
- New test B (a `ConfigReloadService` test using the `svc_with_ctx` fixture): call `svc.apply_config_dict({"allowed_tools": []})`; if it raises `ConfigReloadValidationError`, assert that and that `ctx.cfg.tool.allowed_tools` is unchanged (pattern of lines 225-245); otherwise assert `check_preflight(ctx.cfg, "read_file", {})` raises `PolicyViolationError`.
- New test C (same shape for `allowed_root`): `svc.apply_config_dict({"allowed_root": ""})` either raises `ConfigReloadValidationError` with the config unchanged, or `check_allowed_root(ctx.cfg, "write_file", {"path": "/tmp/x"}, None)` returns False.

### Method
- Reuse the fixtures and imports already in the file (`svc_with_ctx`, `RuntimeToolRegistry`, `build_runtime_tool`/`build_fixture_runtime_tool` as used near line 590); import `PolicyViolationError` and `check_preflight`/`check_allowed_root` from `agent.tool_policy` inside the test (the file's existing local-import style).

### Details
- Test A is the one that must fail before row 75 and pass after; run it against the unmodified code first to confirm it fails (red before green).

## Compatibility considerations
Removing the two keys changes the registry-membership sets only; no persisted state.

## Security considerations
These tests assert fail-closed behavior; they must not weaken any existing denial assertion.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -v`
- Confirm test A fails when `scripts/shared/runtime_tool_registry.py` is at its pre-change state.

## Completion criteria
- The two strict keys and `security_profile` no longer appear in the file.
- Tests A, B and C exist and pass after rows 09, 75 and 15-16 are in place.
- The `mcp` section expectation is an empty set.

## Out of Scope
- Changing `ConfigReloadService` or `prepare_validated_section` (UNK-04: if neither layer denies, report `Plan Gap` rather than patching a non-target file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write reload tests A-C first and confirm red against the pre-change code | Done | 20261110-181000 | 20261110-183000 | Red phase observed before row 75 landed (empty list left `read_file` enabled / TypeError in the interim run); green after row 75. |
| 2 | Update registry-membership expectations (strict keys, `security_profile`) | Done | 20261110-181000 | 20261110-183000 | Removed `tool_definitions_strict` and `routing_drift_strict`; `mcp` expectation is now `expected: set[str] = set()`. Kept `system_prompt_tool` (row 04 keeps that entry, `config_field_registry.py:76`). |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload.py -v` after the code rows land | Done | 20261110-183000 | 20261110-183000 | 63 passed. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-183000 | 20261110-183000 | ruff check + ruff format clean; mypy error count unchanged vs HEAD baseline (68, pre-existing fixture-typing noise in this test file). |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | The procedure's line anchors were written against a pre-reorg copy of the test file; the current HEAD file (`tests/agent/services/test_config_reload.py`) has a 4-arg `_sync_services(new_cfg, llm, hist_mgr, runtime_tools)` and a `_make_svc` fixture pattern | Tests A-C re-anchored: test A added after `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` using the current real-`RuntimeToolRegistry(tools=..., allowed_servers=...)` pattern |
| VF-2 | `apply_policy` is invoked with `tier_map=` and `allowed_tools=` keywords via `ServiceSyncer` (`scripts/agent/services/config_service_sync.py:76-82`), matching row 75's `(allowed_tools, *, tier_map=None)` signature | No signature conflict; test A asserts the observable `enabled_for_llm is False` outcome |
| VF-3 | Import paths differ from the procedure text: `PolicyViolationError` lives in `agent.tool_exceptions`; `ConfigReloadValidationError` in `agent.services.exceptions` (no `config_service_validation` module exists) | Tests import the actual modules |
| VF-4 | Neither `allowed_tools` nor `allowed_root` has a value-level validator in `CONFIG_FIELD_REGISTRY` (`config_field_registry.py:79`, `:88`), so `apply_config_dict` does not raise: the "otherwise" branch of tests B/C holds (empty list applied, `check_preflight` raises, `check_allowed_root` returns False) | Kept the dual-outcome try/except shape; the applied branch is the live one |
| VF-5 | `svc_with_ctx`'s `ctx.cfg.approval` is a MagicMock; iterating its `approval_resource_keys` yields no path keys, so `check_allowed_root` would vacuously pass | Test C sets a real `approval_resource_keys` dict before the check |
| VF-6 | `system_prompt_tool` remains a live registry entry (row 04 keeps it); it is not part of the removed strict keys | Expected set keeps `system_prompt_tool` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Earlier in-session edits to this file were lost when a mid-session fast-forward pull moved `config_field_registry.py` to `scripts/agent/services/` and restored this test file to HEAD | Yes: re-verified all previously completed docs' tests pass in the new layout (619+338 passed), then re-implemented this doc against the current structure | 20261110-183000 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (empty `allowed_tools` denies, also after `/reload`), `REQ-003` (empty `allowed_root` fails closed), `REQ-001`/`REQ-007` (registry expectations)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/services/test_config_reload.py`
