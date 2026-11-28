## Goal

Classify `tests/mcp_servers/mdq/test_mdq_service.py` as `characterization`: the module asserts observed behavior with no requirement source, and the accepted citation it already carries (issue path issues/20260719-142152_parser_spurious_empty_root_section_after_frontmatter.md) is left as it is (`REQ-003`, `AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One module-level `pytestmark` line is added; no assertion or fixture in the module changes.
- No citation is added: `tools/check_test_taxonomy.py` requires one only for `contract` modules. The module already names issue path issues/20260719-142152_parser_spurious_empty_root_section_after_frontmatter.md, which the checker accepts as a citation.

## Assumptions

- `characterization` is the classification the plan records for this module.
- `tests/mcp_servers/mdq` is not in `CLASSIFIED_AREAS` at current HEAD (`tools/check_test_taxonomy.py:66`, `in_classified_area()` matches by prefix), so this module is judged only after the classified-area addition. That addition is the same release unit (`mdq-taxonomy-gate`, plan Phases 4 and 5), so the markers and the gate land in one commit.
- The marker is written through `tools/apply_test_taxonomy_markers.py` from a records JSON array (plan Phase 4); the tool places the marker after the module-level import block and writes nothing else, and it refuses a record whose `pytestmark` already exists or whose kind is not registered in `pyproject.toml`.
- `import pytest` is present, so the records record needs `add_import: false`.
- Verified at current HEAD with `has_requirement_citation()`: the module carries an accepted citation — issue path issues/20260719-142152_parser_spurious_empty_root_section_after_frontmatter.md — so the docstring is not changed.
- The existing citation stays as it is; repointing it to the MDQ canonical doc is a separate decision (plan Risk).
- The plan's row states the citation is present, and that claim holds at current HEAD through the issue path `issues/20260719-142152_parser_spurious_empty_root_section_after_frontmatter.md`. The plan's Background count of six modules that already carry a citation was computed without the registry-path form; corrected at current HEAD it is fifteen, which is what changes the number of contract modules that need the `REQ-003` clause from eleven to nine.

## Design decisions

- Classify as `characterization` because the module asserts observed behavior with no requirement source.

## Alternatives considered

- `N/A: one-line classification change; the plan names the marker.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_service.py`

### Procedure
1. Add `pytestmark = pytest.mark.characterization` after the module-level import block.
2. Leave the docstring as it is.

### Method

- Applied through `tools/apply_test_taxonomy_markers.py` from the batch records JSON array; the marker line is the only change the tool makes to the module.
- The marker is placed after the import block, not in the docstring, so the module docstring stays the place the citation clause is written.

### Details

- Records record: `{"path": "tests/mcp_servers/mdq/test_mdq_service.py", "pytestmark": "characterization", "add_import": false}`.
- No citation clause is written; the module is judged by its marker alone.

## Compatibility considerations

- `N/A: test-only change.`
- After classification the CI report step groups this module under `characterization` (`AC-6`). A characterization failure remains report-only.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_test_taxonomy.py` — no finding for this module (`AC-3`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The module carries exactly one taxonomy marker, `characterization` (`AC-3`).

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
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_service.py`
