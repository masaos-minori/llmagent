## Goal

Add unit tests to the existing checker test module `tests/tools/test_check_canonical_document_prose.py`
covering GV-010's area-grouping behavior: multi-primary-per-area (flagged) and single-primary
(not flagged), plus a corpus run confirming zero benign false positives.

## Scope

- **In-Scope**: add single-primary and multi-primary fixtures/assertions to the existing test
  module; a corpus run guard (REQ-004); a regression assertion that existing GV-009 tests still
  pass.
- **Out-of-Scope**: changing the checker's behavior or the existing GV-009 test logic.

## Assumptions

- Tests exercise the area-grouping/multi-primary logic via the checker's public functions or CLI.
- A small inline fixture registry (or the live `config/documentation_canonical_sources.toml`) can
  supply area values for grouping fixtures.

## Design decisions

- Mirror the structure/style of the existing GV-009 test classes so the new tests fit the suite
  and the regression guard is natural.

## Alternatives considered

N/A: mirroring the sibling test module is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_canonical_document_prose.py`

### Procedure

1. Locate the existing test classes/functions for the base GV-009 scanner.
2. Add a multi-primary fixture: two distinct prose designations of the primary/canonical source
   for the SAME area → assert WARNING finding(s) (REQ-002).
3. Add a single-primary fixture: one primary designation for an area → assert no finding
   (REQ-003).
4. Corpus run: run the checker against the current `docs/` and assert zero benign false
   positives (REQ-004).
5. Regression: confirm the existing GV-009 test classes still pass.

### Method

- Reuse the sibling test module's conventions (fixture layout, how it invokes the checker, how
  it asserts on finding severity/blocking status).
- For the multi-primary case, emit two distinct prose sentences sharing one area key but naming
  two different documents as primary.
- For the single-primary case, emit one primary designation for that area.
- Build the area key the same way the checker does (explicit area token → `claim_type` →
  document area) so grouping is exercised end-to-end.
- Assert on non-blocking WARNING findings for multi-primary and no finding for single-primary.

### Details

- `REQ-002`: two distinct primary designations for one area → flagged.
- `REQ-003`: single primary for an area → not flagged.
- `REQ-004`: corpus run yields zero WARNINGs on benign mentions.
- Regression: existing GV-009 suites unchanged.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_canonical_document_prose.py` | Unit | `uv run pytest tests/tools/test_check_canonical_document_prose.py` | Multi-primary flagged; single-primary/corpus clean |
| Whole suite | Regression | `uv run pytest` | Existing GV-009 suites still pass |

## Completion criteria

- One test each covering the passing and failing path for REQ-002 and REQ-003.
- A corpus run proving zero benign false positives (REQ-004).
- The existing GV-009 suites pass unchanged.

## Out of scope

Changing the checker's behavior or the existing GV-009 test logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001/002/003 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit + corpus coverage for area-grouping/multi-primary)
- **Source issue**: `issues/done/20261018-173100_gov010_detect-multiple-primary-canonical-sources-per-area-in-unregistered-prose.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180620_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-065941
- **Related target files**: `tests/tools/test_check_canonical_document_prose.py`
- **Dependency**: extends the test module created by `plans/20261018-180319_plan.md`.
