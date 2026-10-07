## Goal

Confirm `tests/tools/test_check_known_deviation_sync.py` still covers Known Issue ID
handling via `## Known Deviations` after `tools/check_known_deviation_sync.py` stops parsing
the old `### Known Issues` subsection (REQ-004 / AC-4): the existing tests already use only
`## Known Deviations`, so they must keep passing, and a new case should prove the subsection
is no longer parsed.

## Scope

- **In-Scope**: `tests/tools/test_check_known_deviation_sync.py` — add a case asserting an
  ID mentioned only in the old `### Known Issues` subsection is no longer parsed, and confirm
  the existing `## Known Deviations` tests are unaffected. And the tool under test
  `tools/check_known_deviation_sync.py` (its own row).
- **Out-of-Scope**: the other two tool test files; the tool source itself.

## Assumptions

- Every existing test in this file references IDs through `## Known Deviations` only (verified
  by reading the file: no fixture places an ID solely in a `### Known Issues` subsection). So
  dropping the subsection parsing does not change their inputs or expected findings.

## Design decisions

- Do not modify the existing tests — they already exercise the `## Known Deviations` path that
  remains.
- Add `test_id_only_in_removed_subsection_is_no_longer_parsed`: an ADR that cites an ID in a
  `### Known Issues` subsection (and nowhere in `## Known Deviations`) yields no parsed
  reference from `parse_adr_references` after the change — demonstrating the subsection is no
  longer read. This is the regression guard for the behaviour change.

## Alternatives considered

- Rewriting existing tests to a new shape — rejected: they already cover the retained path;
  only additive coverage is needed (AGENTS.md Global Rule 5).

## Implementation

### Target file

`tests/tools/test_check_known_deviation_sync.py`

### Procedure

1. Verify each existing test references IDs only via `## Known Deviations` (already true).
   No edits required there.
2. Add a new test class or method, e.g.
   `TestSubsectionNoLongerParsed.test_id_only_in_removed_subsection_is_no_longer_parsed`:
   - Write an ADR whose body contains a `### Known Issues` subsection citing `ID-020` but no
     `## Known Deviations` entry for it.
   - Call `parse_adr_references(_discover(adr_dir))`.
   - Assert the result does not contain `ID-020` (empty, or otherwise not parsed) — proving
     the subsection is no longer read.
   - As a positive control, assert an identical ID cited in `## Known Deviations` IS parsed
     (reusing the pattern from `TestStatusMatch`).

### Method

- Read `test_check_known_deviation_sync.py` lines 17-21 (imports: `parse_adr_references`,
  `cross_check`, `parse_canonical_statuses`) and 29-30 (`_write`, `_discover`).
- Add the new test using the existing `_write`/`_discover` helpers.

### Details

- `parse_adr_references(docs) -> list[AdrReference]`; each `AdrReference` has `.id` and
  `.signal`. After the change, no parsed ref carries a subsection origin.
- Keep the positive-control assertion to avoid a vacuous "always empty" test.

## Compatibility considerations

- These tests target `tools/check_known_deviation_sync.py`; update them together with that
  tool's change (same coordinated commit).

## Security considerations

N/A: test-only change.

## Rollback considerations

Revert `tests/tools/test_check_known_deviation_sync.py` to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_check_known_deviation_sync.py` | Unit: `## Known Deviations` handling unchanged; subsection no longer parsed | `uv run pytest tests/tools/test_check_known_deviation_sync.py -q -p no:cacheprovider -p no:randomly` | Existing cases pass; new case passes |
| Changed tool file | Static analysis | `uv run ruff` / `uv run mypy` / `uv run bandit` on `check_known_deviation_sync.py` | Clean |

## Completion criteria

- Existing `## Known Deviations` tests are unchanged and pass.
- The new case proves an ID only in the old `### Known Issues` subsection is no longer
  parsed.
- Unit tests and static analysis pass.

## Out of scope

- The other two tool test files; the tool source itself (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-144755 | 20261007-144755 | REQ-004 / AC-4 Added test_id_only_in_removed_subsection_is_no_longer_parsed + positive control (same ID in ## Known Deviations still parsed) |
| 2 | Add or update tests per Validation plan | Completed | 20261007-144755 | 20261007-144755 | test_check_known_deviation_sync.py 10 passed (targeted); 8087 passed, 20 skipped (full suite, EXIT=0) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-144755 | 20261007-144755 | ruff/mypy/bandit + pytest ruff format+check clean; mypy clean; bandit B101(Low) only; full suite EXIT=0 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-144755 | 20261007-144755 | N/A: no docs/00_index.md task-scope mapping for tests/tools/ |

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
- **Requirement ID**: `REQ-004` — Known Issue ID handling unchanged for `## Known Deviations`; subsection no longer parsed (AC-4)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tests/tools/test_check_known_deviation_sync.py`