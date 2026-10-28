# Procedure: add strict-builder, fixture-equivalence and import-guard tests

## Goal

Cover the strict builder, the fixture builder's equivalence to the old defaults and the guard against production imports (Plan REQ-002..005).

## Scope

- Modify only `tests/shared/test_runtime_tool.py`.
- Test-only change; no source file is edited.

## Assumptions

- Row 02 has landed; the strict tests are written before row 01 and run red until it lands (ordering note).
- Overlap (compatible): `plans/done/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md` (archived, procedures pending) also targets `tests/shared/test_runtime_tool_registry.py`; it adds exclusion-reason tests, while this procedure only changes which builder the existing calls use. The mcpcompat003 work (`implementations/20261028-065435_*`, already executed) edited `tests/shared/test_resource_scope.py`; re-read it before editing.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/shared/test_runtime_tool.py`

### Procedure

- Replace the import `from shared.runtime_tool import ..., build_runtime_tool` with `from tests.shared.runtime_tool_factory import build_fixture_runtime_tool` (keep other names from `shared.runtime_tool`) and rename every `build_runtime_tool(` call that omits `is_write`, `requires_serial`, `resource_scope_kind` or `resource_scope_keys` to `build_fixture_runtime_tool(`; leave calls that already pass all four fields on the strict builder.
- Add `test_strict_builder_rejects_each_missing_required_field` (new) (parametrized over the four fields, expecting `TypeError`) and `test_strict_builder_rejects_none_for_each_required_field` (new) (expecting `ValueError`).
- Add `test_fixture_builder_matches_the_old_permissive_defaults` (new): omitted `is_write` gives `is_write=False` and `requires_serial=True`; explicit `is_write=True` gives `requires_serial=False`; omitted scope gives `""` and `()`.
- Add `test_scripts_do_not_import_the_fixture_builder` (new): parse every `scripts/**/*.py` with `ast` and assert no import of `tests.shared.runtime_tool_factory` and no name `build_fixture_runtime_tool`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- The file has 20 builder calls, 19 of which omit a required field; the one complete call stays on the strict builder.
- Write the strict tests before row 01 and confirm they fail on the permissive builder.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_runtime_tool.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/test_runtime_tool.py`; `uv run ruff check tests/shared/test_runtime_tool.py` | No finding |

## Completion criteria

- The strict and guard tests fail on the pre-change code where applicable and pass after row 01.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005 (strict builder tests; guard test)
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120306
- **Related target files**: tests/shared/test_runtime_tool.py
