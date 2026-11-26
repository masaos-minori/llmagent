## Goal

Mark the requirement-cited assertions as `contract` and the characterization section as `characterization`
(REQ-003 — a module that mixes both kinds carries per-test markers).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the module cites REQ-001/REQ-004 at `:511` and
  REQ-005/REQ-002/REQ-008 at `:1039`.
- The characterization section begins at `:598`, where the heading states that `list_entries()` had no direct
  coverage before the shared `SELECT` column-list constant was extracted.
- Those tests assert observed behavior with no requirement source, so they cannot be presented as normative.

## Design decisions

- Module-level `pytestmark = pytest.mark.contract` for the requirement-cited part, with per-test
  `@pytest.mark.characterization` on the tests in the section beginning at `:598`.

## Alternatives considered

- Marking the whole module `characterization` — rejected: most assertions are traceable to recorded
  requirements, so the module mixes kinds.

## Implementation
### Target file
`tests/agent/memory/test_memory_store.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add `@pytest.mark.characterization` to each test in the section beginning at `:598`.

### Method

- No assertion is changed.

### Details

- The section heading already separates the two parts; the markers make the split machine-readable.

## Compatibility considerations

- The module appears in both `-m` selections; the full suite is unchanged.
- `tests/agent/memory/test_memory_vec_session.py` already carries a `pytestmark` and is not this row, so it is
  reported as classified by the checker, not as a baseline entry.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/memory/test_memory_store.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the mixed module is detected through its per-test
  markers.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every test in the module resolves to exactly one kind, the `contract` part carries a citation, and the
  checker reports no finding.

## Out of Scope

- The checker (document 02) and the authority-model wording (document 09).

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
- **Related target files**: `tests/agent/memory/test_memory_store.py`
