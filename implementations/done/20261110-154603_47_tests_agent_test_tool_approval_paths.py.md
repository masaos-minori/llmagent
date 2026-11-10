## Goal
Update `tests/agent/test_tool_approval_paths.py` so `_make_cfg` uses a non-empty root and the "disabled root" test asserts the new denial (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `PERMISSIVE_ALLOWED_ROOT` (new) is defined by the row 37 document (`tests/agent/_config_test_defaults.py`) as `"/"`, so every absolute test path stays inside the jail; row 37 lands first.
- `build_agent_config` rejects `allowed_root=""` (row 07), so the old `test_disabled_root_does_not_block` (line 133) cannot build its config; the runtime denial for an empty root (row 09, `check_allowed_root`) is exercised by assigning the attribute after the build, which is what a `/reload` would produce.

## Design decisions
- Replace the test instead of deleting it: the fail-closed behavior for an empty root is the new contract.
- `_make_cfg` follows the same fixture change as rows 46/80/81.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_tool_approval_paths.py`

### Procedure
- Import `PERMISSIVE_ALLOWED_ROOT` (new); drop `STRICT_PRODUCTION_OVERRIDES` from the imports (lines 18-24) and from `_make_cfg` (line 33); add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` before `**overrides`.
- Replace `test_disabled_root_does_not_block` (line 133 to the end of the file) with `test_empty_allowed_root_denies_path_arguments` (new): `cfg = _make_cfg(approval_protected_paths=[])`, then `cfg.approval.allowed_root = ""`; give `ctx.services_required.audit_logger` a `MagicMock`; call `check_approval(ctx, "write_file", {"path": outside})`; assert the result is False and `"denied_root_jail" in audit.info.call_args[0][0]` (same shape as the test at line 79).

### Method
- Keep the two root-bearing tests (lines 79-130) as they are: they pass their own root.
- Use `tmp_path / "outside.txt"` for `outside`, as the old test did, to avoid `approval_protected_paths` escalation.

### Details
- If `check_approval` denies through a different code than `denied_root_jail` for an empty root, align the assertion with row 09's procedure rather than weakening it.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_paths.py -v`

## Completion criteria
- No strict spread remains.
- The empty-root test asserts denial and passes.
- The file passes against the fail-closed code.

## Out of Scope
- Changing the other root-jail tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_tool_approval_paths.py` per Procedure/Method/Details | Done | 20261110-200000 | 20261110-200500 | Import swap (lines 19-24), `_make_cfg`: strict spread dropped, `"allowed_root": PERMISSIVE_ALLOWED_ROOT` added before `**overrides`; `test_disabled_root_does_not_block` replaced by `test_empty_allowed_root_denies_path_arguments` (post-build `cfg.approval.allowed_root = ""`, denial asserted via `denied_root_jail` in `audit.info`). Dry-run mock and `_approval_read` patch dropped: denial happens at preflight, before interactive approval. |
| 2 | Run `uv run pytest tests/agent/test_tool_approval_paths.py -v` and fix remaining fixtures in this file only | Done | 20261110-200500 | 20261110-200500 | 3 passed; no additional fixtures needed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-200500 | 20261110-200500 | ruff check + ruff format clean; no `STRICT_PRODUCTION_OVERRIDES` reference remains. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed: `STRICT_PRODUCTION_OVERRIDES` import at line 23, spread at line 33, `test_disabled_root_does_not_block` at line 132 asserting `result is True` | Applied as written |
| VF-2 | Doc's Details branch checked against code: `check_preflight` (tool_policy.py line 534) raises `PolicyViolationError("denied_root_jail", ...)` for a failed root jail, so no assertion alignment was needed | Kept `denied_root_jail` assertion |
| VF-3 | The replacement test no longer needs the `ToolCallResult` dry-run mock or the `_approval_read` patch used by the old test — preflight denial fires before dry-run/approval; both imports remain used by the two retained tests | Followed the doc's "same shape as the test at line 79" |

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
- **Requirement ID**: `REQ-002`, `REQ-003` (empty `allowed_root` fails closed); `REQ-001` (strict spread removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_tool_approval_paths.py`
