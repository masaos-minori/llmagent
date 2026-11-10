## Goal
Remove the strict toggles, the non-strict WARNING case and the `SecurityProfile` plumbing from `tests/agent/test_startup.py` (`REQ-001`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Mirror the changes of `tests/agent/test_startup_severity_classification.py`; keep every FATAL case.

## Alternatives considered
N/A: the WARNING path no longer exists.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
- Remove `SecurityProfile` from the import block (line 32), the `tool_definitions_strict` parameter and both assignments in `_make_startup_ctx()` (lines 146-157).
- Delete `test_routing_drift_live_warning_when_non_strict_drift` (line ~489); call `_make_startup_ctx()` without arguments in `test_routing_drift_live_skipped_on_exception` (line ~513).
- Delete the three `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` lines (about 719, 750, 776).
- Reword the `TestBuildAgentConfigErrorPath` docstrings (lines ~797-805) that mention `security_profile_val`; remove the two strict keys from the config literal near lines 885-886.

### Method
- Run `rg -n 'strict|security_profile|SecurityProfile' tests/agent/test_startup.py` before and after.

### Details
- The known-keys test near line 880 uses `ProductionConfigValidator().validate(...)`; keep it, dropping only the two keys.

## Compatibility considerations
Test-only; release unit.

## Security considerations
N/A: fixture and WARNING-path cleanup; FATAL cases stay.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No strict key or `SecurityProfile`/`security_profile` remains; the file passes (`AC-01`, `AC-07`).

## Out of Scope
- Source edits; other startup test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the helper parameter, profile lines, the non-strict WARNING case and the strict keys | Done | 20261110-172551 | 20261110-172551 | rg clean; one script-induced indentation artifact (3 lines) fixed before validation |
| 2 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level ruff + `pytest -v`: 39 passed; mypy deferred to the code-batch end gate |

### Verification Findings
- (corrected) the known-keys test near line 880 asserts `len(result.errors) == 0`; after dropping the two strict keys the literal also needs `"allowed_root": "/opt/llm"` because the landed validator rejects an absent `allowed_root` (doc 01). The Procedure's "dropping only the two keys" would have made this test fail.

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
- **Requirement ID**: `REQ-001` (and `REQ-007` for the profile attributes)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup.py`
