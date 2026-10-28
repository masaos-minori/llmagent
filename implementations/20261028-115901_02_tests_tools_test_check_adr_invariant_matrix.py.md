# Procedure: add node, parameterized id, body citation and severity tests to the matrix checker tests

## Goal

Cover node validation, parameterized ids, body citations and the ERROR severity (Plan REQ-007).

## Scope

- Modify only `tests/tools/test_check_adr_invariant_matrix.py`.
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

`tests/tools/test_check_adr_invariant_matrix.py`

### Procedure

- Add `TestNodeValidation` (new) with `test_missing_node_in_existing_file_is_an_error` (new), `test_class_qualified_node_is_accepted` (new), `test_parameterized_id_suffix_is_stripped` (new) and `test_call_parentheses_suffix_is_stripped` (new), building throwaway modules under `tmp_path` and patching `REPO_ROOT` the way the existing tests do.
- Add `test_body_citation_with_missing_node_is_an_error` (new) and `test_path_less_body_citation_is_an_error` (new) for the new body scan.
- Change the existing body-rule tests in `TestBodyEmptyCellWithoutMarker` and `TestBodyIndexDisagreement` to assert severity `ERROR` and add `test_exit_code_is_nonzero_for_body_findings` (new) through `main(["--format", "json"])`.
- Keep `_TEST_PATH_RE` import assertions if present and add `test_ci_runner_regex_import_still_works` (new) that imports the name from the module.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 1 has landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` | Pass |
| 2 | `uv run ruff format tests/tools/test_check_adr_invariant_matrix.py`; `uv run ruff check tests/tools/test_check_adr_invariant_matrix.py` | No finding |

## Completion criteria

- Each new failure mode has a test and the existing tests pass with the new severity.

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
- **Requirement ID**: REQ-003, REQ-004, REQ-007 (new failure modes)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: tests/tools/test_check_adr_invariant_matrix.py
