# Procedure: move the default-reliant builder calls to the fixture builder

## Goal

Move the 2 builder call(s) in this file that omit a required field to `build_fixture_runtime_tool` (Plan REQ-003).

## Scope

- Modify only `tests/integration/test_production_security_regression.py`.
- Test-only change; no source file is edited.

## Assumptions

- Row 02 (`tests/shared/runtime_tool_factory.py`) has landed and the helper imports from this directory (UNK-03 was checked in that row).
- Overlap: none active. Verified 2026-10-28: the mcpexec004 plan is archived with no pending procedures (its `tests/agent/test_mcpexec003*` / `test_mcpexec004*` files and procedures were removed by a deliberate sync), so no other procedure targets this file. The mcpcompat003 work (`implementations/20261028-065435_*`, already executed) edited `tests/shared/test_resource_scope.py`; re-read it before editing (row 08).

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/integration/test_production_security_regression.py`

### Procedure

- Replace the import `from shared.runtime_tool import ..., build_runtime_tool` with `from tests.shared.runtime_tool_factory import build_fixture_runtime_tool` (keep other names from `shared.runtime_tool`) and rename every `build_runtime_tool(` call that omits `is_write`, `requires_serial`, `resource_scope_kind` or `resource_scope_keys` to `build_fixture_runtime_tool(`; leave calls that already pass all four fields on the strict builder.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- The two calls (`kept` and `excluded`) are in `test_disabled_tool_excluded_from_llm_visibility`.
- Assertions stay unchanged: the fixture builder reproduces the old defaults exactly (equality with the old output is asserted in `tests/shared/test_runtime_tool.py`).

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/integration/test_production_security_regression.py -m 'not integration and not production_paths_allowed' -q` | Pass |
| 2 | `uv run ruff format tests/integration/test_production_security_regression.py`; `uv run ruff check tests/integration/test_production_security_regression.py` | No finding |

## Completion criteria

- No default-reliant `build_runtime_tool(` call remains in this file and its tests pass with unchanged assertions.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 2026-10-28 | 2 calls renamed by hardened tool |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-10-28 | pytest 9 passed 1 skipped; ruff+isort clean; mypy 3 findings pre-existing at HEAD |

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
- **Requirement ID**: REQ-003 (call sites rely on the permissive defaults)
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120306
- **Related target files**: tests/integration/test_production_security_regression.py