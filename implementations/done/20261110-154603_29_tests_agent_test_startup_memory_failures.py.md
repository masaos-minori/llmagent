## Goal
Remove the strict toggle, the non-strict WARNING case and the `SecurityProfile` attribute from `tests/agent/test_startup_memory_failures.py` (`REQ-001`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Keep the FATAL case, rename it so it no longer mentions strict mode; delete the WARNING case.

## Alternatives considered
N/A: the WARNING path no longer exists.

## Implementation
### Target file
`tests/agent/test_startup_memory_failures.py`

### Procedure
- Remove the `SecurityProfile` import (line 17), the `tool_definitions_strict` parameter and the two assignments in `_make_startup_ctx()` (lines 20-31).
- Rename `test_tool_definitions_strict_fatal_on_finding` (line 133) to `test_tool_definitions_finding_is_fatal` (new), call `_make_startup_ctx()` without arguments, and reword its docstring.
- Delete `test_tool_definitions_warning_on_non_strict_finding` (line ~155); drop the argument in `test_tool_definitions_ok_when_clean` (line ~180).

### Method
- Confirm with `rg -n 'strict|SecurityProfile' tests/agent/test_startup_memory_failures.py`.

### Details
- The FATAL case builds the finding itself, so it does not depend on the removed toggle.

## Compatibility considerations
Test-only; release unit.

## Security considerations
N/A: keeps the FATAL assertion; removes only the WARNING-path case.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_memory_failures.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No strict key or `SecurityProfile` remains and the file passes (`AC-01`, `AC-07`).

## Out of Scope
- Source edits; other startup test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the helper parameter, profile attribute and the non-strict case; rename the FATAL case | Done | 20261110-172551 | 20261110-172551 | renamed to `test_tool_definitions_finding_is_fatal`; rg clean |
| 2 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level ruff + `pytest -v`: 5 passed, 2 skipped; mypy deferred to the code-batch end gate |

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
- **Requirement ID**: `REQ-001` (and `REQ-007` for the profile attribute)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_memory_failures.py`
