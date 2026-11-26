## Goal

Mark the requirement-cited assertions as `contract` and the characterization section as `characterization`
(REQ-003 — a module that mixes both kinds carries per-test markers).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: the module docstring cites REQ-001/REQ-002 (`tests/agent/test_http_lifecycle.py:3`),
  and the characterization section begins at `:223`; `pytest` is already imported.
- The cited assertions are the tracking-entry behavior: entries are removed only after a confirmed exit, which
  is the requirement the docstring names.
- The characterization section records observed behavior with no requirement source, so it cannot be presented
  as normative.

## Design decisions

- Module-level `pytestmark = pytest.mark.contract` for the requirement-cited part, with per-test
  `@pytest.mark.characterization` on the tests in the section at `:223` onward, so the module kind stays
  readable from `pytestmark` while the mixed part is explicit.

## Alternatives considered

- Splitting the module into two files — rejected: it breaks the `tests/` mirrors `scripts/` rule recorded in
  `skills/python-test-and-fix/workflow.md`.

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add `@pytest.mark.characterization` to each test in the characterization section beginning at `:223`.

### Method

- No assertion is changed.

### Details

- The section heading already separates the two parts; the markers make the split machine-readable.

## Compatibility considerations

- The module appears in both `-m` selections; the full suite is unchanged.
- cliplc009 also targets this module for assertion changes — judged compatible, since this row adds markers
  only.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the mixed module is detected through its per-test
  markers.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every test in the module resolves to exactly one kind, the `contract` part carries a citation, and the
  checker reports no finding.

## Out of Scope

- The assertion changes owned by cliplc009.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the markers per Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | this row is the test itself |

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
- **Requirement ID**: `REQ-003` (per-test markers for a mixed module)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_http_lifecycle.py`
