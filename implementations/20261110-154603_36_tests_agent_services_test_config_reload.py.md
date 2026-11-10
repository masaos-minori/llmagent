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
| 1 | Write reload tests A-C first and confirm red against the pre-change code | Pending | — | — | |
| 2 | Update registry-membership expectations (strict keys, `security_profile`) | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload.py -v` after the code rows land | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (empty `allowed_tools` denies, also after `/reload`), `REQ-003` (empty `allowed_root` fails closed), `REQ-001`/`REQ-007` (registry expectations)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/services/test_config_reload.py`
