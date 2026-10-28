# Procedure: replace the obsolete seven-column fixtures and add marker and unparseable-matrix tests

## Goal

Rebuild the fixtures on the six-column matrix and cover the marker rule and the zero-reference failure (Plan REQ-005, REQ-007).

## Scope

- Modify only `tests/tools/test_check_adr_reference.py`.
- Test-only change; no source file is edited.

## Assumptions

- The rows named in the ordering note have been applied first.
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/tools/test_check_adr_reference.py`

### Procedure

- Replace `_HEADER`, `_SEPARATOR` and every fixture row with the six-column shape (`Invariant | Statement | Type | Timing | Gate | Verification Status`) and IDs like `ADR-004 INV-07`; update the expected `line_no` values.
- Rewrite `test_file_with_adr_reference_produces_no_issue` to write `# ADR-004: startup checks` and keep `test_file_missing_adr_reference_produces_error`.
- Add `test_prose_only_adr_mention_is_not_a_marker` (new) (the ID appears in a docstring and a string), `test_marker_after_other_comment_text_is_accepted_only_at_comment_start` (new), `test_matrix_with_no_parsable_rows_is_an_error` (new) through `collect_issues` with a patched `ADR_INDEX`, and `test_unparseable_source_file_is_an_error` (new).
- Keep the tests that skip test-node citations and bare filenames.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 3 has landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/tools/test_check_adr_reference.py -q` | Pass |
| 2 | `uv run ruff format tests/tools/test_check_adr_reference.py`; `uv run ruff check tests/tools/test_check_adr_reference.py` | No finding |

## Completion criteria

- All fixtures use the six-column shape and each new failure mode has a test.

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
- **Requirement ID**: REQ-005, REQ-007 (current table shape; marker rule; zero rows)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: tests/tools/test_check_adr_reference.py
