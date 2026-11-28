## Goal

Classify `tests/mcp_servers/mdq/test_mdq_health_posture.py` as `contract`: the HTTP bind posture is a documented contract (citation already present), and the accepted citation it already carries (requirement number REQ-004) is left as it is (`REQ-003`, `AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One module-level `pytestmark` line is added; no assertion or fixture in the module changes.
- No citation is added: the module already carries an accepted one (requirement number REQ-004).

## Assumptions

- `contract` is the classification the plan records for this module.
- `tests/mcp_servers/mdq` is not in `CLASSIFIED_AREAS` at current HEAD (`tools/check_test_taxonomy.py:66`, `in_classified_area()` matches by prefix), so this module is judged only after the classified-area addition. That addition is the same release unit (`mdq-taxonomy-gate`, plan Phases 4 and 5), so the markers and the gate land in one commit.
- The marker is written through `tools/apply_test_taxonomy_markers.py` from a records JSON array (plan Phase 4); the tool places the marker after the module-level import block and writes nothing else, and it refuses a record whose `pytestmark` already exists or whose kind is not registered in `pyproject.toml`.
- `import pytest` is present, so the records record needs `add_import: false`.
- Verified at current HEAD with `has_requirement_citation()`: the module carries an accepted citation — requirement number REQ-004 — so the docstring is not changed.
- The existing citation stays as it is; repointing it to the MDQ canonical doc is a separate decision (plan Risk).

## Design decisions

- Classify as `contract` because the HTTP bind posture is a documented contract (citation already present).

## Alternatives considered

- `N/A: one-line classification change; the plan names the marker.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_health_posture.py`

### Procedure
1. Add `pytestmark = pytest.mark.contract` after the module-level import block.
2. Leave the docstring as it is.

### Method

- Applied through `tools/apply_test_taxonomy_markers.py` from the batch records JSON array; the marker line is the only change the tool makes to the module.
- The marker is placed after the import block, not in the docstring, so the module docstring stays the place the citation clause is written.

### Details

- Records record: `{"path": "tests/mcp_servers/mdq/test_mdq_health_posture.py", "pytestmark": "contract", "add_import": false}`.
- No citation clause is written; the module is judged by its marker alone.

## Compatibility considerations

- `N/A: test-only change.`
- After classification the CI report step groups this module under `contract` (`AC-6`).

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_test_taxonomy.py` — no finding for this module (`AC-3`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The module carries exactly one taxonomy marker, `contract` (`AC-3`).

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
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_health_posture.py`
