## Goal

Add unit tests for the three new checks (`check_last_reviewed`, `check_priority_valid`,
`check_blocking_reference`) and for the extended `_parse_inventory_entries`, plus a
regression guard that the existing 14 tests and `TestExitCodeBehavior` still pass.

## Scope

- **In-Scope**: tests for each new check (valid vs invalid), a parser-extraction test
  for the three new markers, and a regression assertion on the existing suite.
- **Out-of-Scope**: changing the tool's exit-code contract or any other check.

## Assumptions

- Tests construct `NcEntry` objects directly (the extended constructor accepts
  `last_reviewed`/`priority`/`blocking`) rather than parsing a fixture for every case;
  one test parses a fixture to prove the markers are read.
- `governance_03` Priority Values are `High`/`Medium`/`Low`; Status Values are
  `open/investigating/deferred` (no `Blocked`).

## Design decisions

- Each new check is exercised with both a passing and a failing fixture entry so the
  WARNING is both covered and proven to fire.

## Alternatives considered

N/A: direct `NcEntry` construction is the simplest, most readable approach for pure
parsing functions.

## Implementation

### Target file

`tests/tools/test_check_needs_confirmation_inventory.py`

### Procedure

1. Add a helper that builds an `NcEntry` with the three new fields.
2. Test `check_last_reviewed`: valid ISO date yields no issue; missing/malformed
   yields a `WARNING`.
3. Test `check_priority_valid`: each of `High`/`Medium`/`Low` (any case) yields no
   issue; an out-of-enum value yields a `WARNING`.
4. Test `check_blocking_reference`: a dangling reference yields a `WARNING`; a valid
   cross-reference within the corpus yields none; unset `blocking` yields none.
5. Test `_parse_inventory_entries` extracts `Last Reviewed`/`Priority`/`Blocking` from
   an inventory-string fixture.
6. Assert the existing suite (including `TestExitCodeBehavior`) still passes.

### Method

- Import `NcEntry` from the tool under test and construct entries directly:

  ```python
  from tools.check_needs_confirmation_inventory import (
      NcEntry,
      check_last_reviewed,
      check_priority_valid,
      check_blocking_reference,
      _parse_inventory_entries,
  )
  from tools._docs_consistency_lib import DocFile
  ```

- `check_blocking_reference` needs a corpus to resolve against; build two entries where
  one references the other's `nc_id` (valid) and a separate case referencing a
  non-existent id (dangling).
- Parse a fixture via `_parse_inventory_entries(DocFile(...))` whose lines include a
  `#### NC-001` header followed by `**Last Reviewed:** 2026-01-15`,
  `**Priority:** High`, `**Blocking:** NC-002`.
- Assert on `issue.severity == "WARNING"` and message substrings; assert empty lists
  for the passing cases.

### Details

- `REQ-001`: valid `2026-01-15` → no issue; `None` and `"not-a-date"` → `WARNING`.
- `REQ-002`: `"high"`, `"Medium"`, `"LOW"` → no issue; `"Critical"` → `WARNING`.
- `REQ-003`: `blocking="NC-001"` with `NC-001` present → no issue; `blocking="NC-999"`
  → `WARNING`; `blocking=None` → no issue.
- Regression: run the full `tests/tools/` suite; confirm 14 existing tests unchanged
  and `TestExitCodeBehavior` holds after wiring.

## Compatibility considerations

N/A: test-only change; does not affect production code or the exit-code contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_needs_confirmation_inventory.py` | Unit | `.venv/bin/python -m pytest tests/tools/test_check_needs_confirmation_inventory.py` | New + existing 14 tests pass |
| Whole suite | Regression | `.venv/bin/python -m pytest tests/tools/` | No new failures |

## Completion criteria

- One test per new check covers both the passing and failing path.
- A parser test proves the three markers are extracted.
- The existing suite passes unchanged.

## Out of scope

Any change to the tool's exit-code behavior or to checks outside this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add unit tests for the three new checks + parser extension | Pending | — | — | REQ-001/002/003 |
| 2 | Run the tool test suite; confirm existing 14 tests pass | Pending | — | — | all REQs |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (unit coverage for the new checks)
- **Source issue**: `issues/20261018-172829_gov008_automate-needs-confirmation-review-metadata-checks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-175819_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-033526
- **Related target files**: `tests/tools/test_check_needs_confirmation_inventory.py`
