## Goal

Classify `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` as `contract`: the public error-code taxonomy is a documented contract, and the citation the plan recorded as missing is present at current HEAD in the module text at line 62 (`REQ-003`, `AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One module-level `pytestmark` line is added; no assertion or fixture in the module changes.
- No citation clause is written: the `REQ-004` citation at line 62 already satisfies what `tools/check_test_taxonomy.py` requires of a `contract` module, so this row is the marker line only.

## Assumptions

- `contract` is the classification the plan records for this module.
- `tests/mcp_servers/mdq` is not in `CLASSIFIED_AREAS` at current HEAD (`tools/check_test_taxonomy.py:66`, `in_classified_area()` matches by prefix), so this module is judged only after the classified-area addition. That addition is the same release unit (`mdq-taxonomy-gate`, plan Phases 4 and 5), so the markers and the gate land in one commit.
- The marker is written through `tools/apply_test_taxonomy_markers.py` from a records JSON array (plan Phase 4); the tool places the marker after the module-level import block and writes nothing else, and it refuses a record whose `pytestmark` already exists or whose kind is not registered in `pyproject.toml`.
- `import pytest` is present, so the records record needs `add_import: false`.
- Verified at current HEAD with `has_requirement_citation()`: the module carries the `REQ-004` citation at line 62, which is one of the accepted forms (requirement number, Accepted ADR path, issue path, or a Canonical Source Registry path named in the module text).
- The existing `REQ-004` citation at line 62 is left as it is; this row writes the marker only.

## Design decisions

- Classify as `contract` because the public error-code taxonomy is a documented contract.

## Alternatives considered

- `N/A: one-line classification change; the plan names the marker, and the citation the plan expected to be absent is already present.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`

### Procedure
1. Add `pytestmark = pytest.mark.contract` after the module-level import block.
2. Add the `REQ-003` citation clause to the module docstring.

### Method

- Applied through `tools/apply_test_taxonomy_markers.py` from the batch records JSON array; the marker line is the only change the tool makes to the module.
- The marker is placed after the import block, not in the docstring, so the citation the module already carries is not touched.

### Details

- Records record: `{"path": "tests/mcp_servers/mdq/test_mdq_error_taxonomy.py", "pytestmark": "contract", "add_import": false}`.
- The citation clause names `REQ-003` in the module docstring, which is the form the checker reads from source text.

## Compatibility considerations

- `N/A: test-only change.`
- After classification the CI report step groups this module under `contract` (`AC-6`), so a failure here is a checker finding, not a report-only result.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_test_taxonomy.py` — no finding for this module (`AC-3`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The module carries exactly one taxonomy marker, `contract`, and the `REQ-003` citation (`AC-3`).

## Out of Scope

- The classified-area addition (`tools/check_test_taxonomy.py`, row 05).
- `tools/apply_test_taxonomy_markers.py` itself, which is not a plan target.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row is the test module itself |

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
- **Requirement ID**: REQ-003, AC-3
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`
