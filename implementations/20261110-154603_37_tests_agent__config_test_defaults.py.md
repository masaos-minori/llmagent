## Goal
Remove the strict-key overrides from the shared test defaults and give the default fixtures a non-empty `allowed_tools` and `allowed_root`, so every test built on them survives the fail-closed changes (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `ALL_TOOL_NAMES` (line 59-61) already supplies a non-empty `allowed_tools`; the missing default is `allowed_root`: `build_agent_config` will reject an empty `allowed_root` after `scripts/agent/config_section_builders.py` (row 07), and `tool_policy.py` (row 09) denies path-bearing calls for an empty root.
- A test root of `"/"` keeps every absolute test path inside the jail, so it is the neutral default; tests that exercise the jail pass their own root.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).
- ADDITIONAL TARGET DISCOVERY (not in the Plan table): `STRICT_PRODUCTION_OVERRIDES` is also imported and spread by `tests/agent/test_repository_gateway.py` (line 27) and `tests/agent/test_tool_audit.py` (line 30). Removing the constant breaks both; the Plan must be amended with those two rows (fallout class, `tools/amend_plan.py`) before this document is executed. The rows in this group that import it (`test_tool_approval_preflight.py`, `test_tool_approval_paths.py`, `test_tool_approval_repos.py`, `test_tool_approval_risk.py`) are already targets.

## Design decisions
- Delete `STRICT_PRODUCTION_OVERRIDES` instead of emptying it: an empty dict under the old name would be a compatibility shim (`tools/check_compat_shims.py`) and would hide the removal from importers.
- Add one constant, `PERMISSIVE_ALLOWED_ROOT` (new), and have fixtures spread or reference it, rather than editing each test's dict literal.

## Alternatives considered
Defaulting `allowed_root` to a per-test `tmp_path`: rejected because the defaults module is import-time and shared; a per-test value would have to be threaded through every `_make_cfg`.

## Implementation
### Target file
`tests/agent/_config_test_defaults.py`

### Procedure
- Delete the `STRICT_PRODUCTION_OVERRIDES` definition (lines 14-17).
- Rewrite the module docstring (lines 1-10): it must no longer claim the validator requires `tool_definitions_strict`/`routing_drift_strict`; keep the statements about `allowed_tools` and add `allowed_root`.
- Add `PERMISSIVE_ALLOWED_ROOT: str = "/"` (new) with a comment: a non-empty root that contains every absolute test path.
- Update the comment above `ALL_TOOL_NAMES` (lines 56-58) so it says an empty list now denies every tool at runtime.

### Method
- Keep `ALL_TOOL_NAMES`, `ALL_TOOL_SAFETY_TIERS`, `ALL_APPROVAL_RISK_RULES` and `GIT_RISK_FLOOR` unchanged.

### Details
- Update importers listed above in their own documents (rows 46, 47, 80, 81) and the two newly discovered files once added to the Plan.

## Compatibility considerations
The constant removal breaks every importer until the importers are updated in the same change; run `rg -n STRICT_PRODUCTION_OVERRIDES tests` to confirm none remain.

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `rg -n STRICT_PRODUCTION_OVERRIDES tests` returns nothing after all importers are updated.
- `uv run pytest tests/agent -q` (import-time check of the module via its importers).
- `uv run ruff check tests/agent/_config_test_defaults.py`

## Completion criteria
- `STRICT_PRODUCTION_OVERRIDES` is gone and `PERMISSIVE_ALLOWED_ROOT` (new) exists.
- The docstring matches the validator after row 01.
- No importer references the deleted name.

## Out of Scope
- Editing the importers outside this Plan's table (Plan amendment first).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `STRICT_PRODUCTION_OVERRIDES`, update docstrings and comments | Pending | — | — | |
| 2 | Add `PERMISSIVE_ALLOWED_ROOT` (new) | Pending | — | — | |
| 3 | Update every importer (`rg -n STRICT_PRODUCTION_OVERRIDES tests`) and run `uv run pytest tests/agent -q` | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (non-empty `allowed_tools` fixtures), `REQ-003` (non-empty `allowed_root` fixtures), `REQ-001` (strict overrides removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/_config_test_defaults.py`
