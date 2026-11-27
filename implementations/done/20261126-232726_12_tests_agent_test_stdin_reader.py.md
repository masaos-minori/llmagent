## Goal

Classify the module as `characterization` (REQ-003 — every classified module carries exactly one marker).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: no `pytestmark` and no requirement citation; the tests at `:89`, `:124`, `:136` record
  that a line arriving after a cancelled read is discarded, which matches `scripts/agent/stdin_reader.py:39-43`.
  No requirement source defines that behavior, so the module is `characterization`.
- `pytest` is already imported, so no import change is needed.

## Design decisions

- Module-level `pytestmark` only: the module has no requirement-cited assertion, so it does not mix kinds.

## Alternatives considered

- N/A: the rule decides the classification; no design choice remains.

## Implementation
### Target file
`tests/agent/test_stdin_reader.py`
### Procedure

- Add `pytestmark = pytest.mark.characterization` after the imports.

### Method

- No assertion is changed.

### Details

- One line; the module docstring already describes the recorded behavior.
- Step 3b note (2026-11-27): applied. The evidence line numbers `:89`, `:124`, `:136` are the pre-marker
  positions; after the marker the tests are at 91, 126, 138.

## Compatibility considerations

- The module is now selected by `-m characterization`; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_stdin_reader.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`.
- Sequence: lint → type → arch → security.

## Completion criteria

- The module carries exactly one taxonomy marker, no assertion changed, and the module is no longer reported
  as unclassified.

## Out of Scope

- The checker (document 02) and the CI report step (document 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker per Procedure/Method/Details | Completed | 20261127-114755 | 20261127-114755 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-114755 | 20261127-114755 | this row is the test itself this row is the test itself |

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
- **Requirement ID**: `REQ-003` (module-level taxonomy marker)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_stdin_reader.py`