## Goal
Update the `_cfg()` fixture and negative-path cases in `tests/agent/test_agent_negative_paths.py` for removed strict/profile keys and a non-empty `allowed_root` (`REQ-001`, `REQ-003`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- `_cfg()` defaults (lines 20-50) include the two strict keys (29-30), `"allowed_root": ""` (36) and `"security_profile": "production"` (37); the empty `allowed_root` would now fail `build_agent_config()`. Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Replace the deleted `security_profile` invalid-value class with a removed-key case so the negative-path file still covers config rejection.

## Alternatives considered
Deleting the class without replacement was rejected: the file's purpose is negative-path coverage.

## Implementation
### Target file
`tests/agent/test_agent_negative_paths.py`

### Procedure
- Remove the two strict keys and `security_profile` from `_cfg()`'s defaults; change `"allowed_root": ""` to `"/opt/llm"`.
- Delete `TestSecurityProfileInvalidValue` (lines 52-65).
- Add `TestRemovedConfigKeysRejected` (new) with parametrized cases `_cfg(tool_definitions_strict=True)`, `_cfg(routing_drift_strict=True)`, `_cfg(security_profile="production")` expecting `ConfigReloadValidationError` (import from `agent.services.exceptions`), and `test_empty_allowed_root_rejected` (new) expecting `ValueError` matching `allowed_root`.

### Method
- `ConfigReloadValidationError` subclasses `ValueError` (`scripts/agent/services/exceptions.py:17`), so one `pytest.raises(ValueError)` would also pass; use the specific class for the removed-key cases.

### Details
- Other classes in the file call `_cfg(...)` and are unaffected by the key removal.

## Compatibility considerations
Test-only; release unit.

## Security considerations
Adds negative coverage for the removed keys and the empty `allowed_root` load error.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_agent_negative_paths.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- The fixture is valid under the new schema, `TestSecurityProfileInvalidValue` is gone, removed-key and empty-`allowed_root` cases pass (`AC-01`, `AC-03`, `AC-07`).

## Out of Scope
- Builder and validator source edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `_cfg()` defaults and delete the profile test class | Pending | — | — | |
| 2 | Add the removed-key and empty `allowed_root` cases | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (and `REQ-003`, `REQ-007` for the fixture consequences)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_agent_negative_paths.py`
