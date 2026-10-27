## Goal

Extend `tools/check_adr_invariant_matrix.py` with two read-only rules that report an empty verification-evidence cell in an ADR body (Rule 1) and a disagreement between an ADR body and the index for the same invariant (Rule 2), both at `WARNING` severity (`REQ-001`, `REQ-002`, `REQ-003`), without changing the existing rule or its contracts (`REQ-004`).

## Scope

- Edit only this module: add parsing helpers, two rule functions, a severity constant, extend `collect_issues()`, and update the module docstring and `--help` text.
- Keep `_TEST_PATH_RE`, `ADR_INDEX`, `check_invariant_matrix_test_paths()` (signature, behavior, `ERROR` severity), the JSON keys written by `render_json()` and the exit-code behavior of `report_and_exit()` unchanged.
- Tests (row 02) and the catalog (row 03) are separate rows.

## Assumptions

- Order: this row is applied after the implementation procedures of `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` and `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md`. Phase 1 re-reads the implemented marker text (UNK-01); if it differs from "a cell whose text begins with `Not verified`", match the implemented text and report it.
- Step 3a survey: 13 empty body cells in three ADRs today (ADR-001 five, ADR-002 two, ADR-003 six); the index `ADR List` resolves every matrix ADR ID to an existing file (UNK-03 resolved). Comparing cited test file paths per invariant as a union over all body rows, 24 invariants appear in both places and 11 disagree, so `WARNING` is required: an `ERROR` would fail pre-commit and CI.
- `.github/run_cited_adr_tests.py` loads this module by file path and reads `_TEST_PATH_RE` and `ADR_INDEX`; `.pre-commit-config.yaml` hook `adr-invariant-matrix` runs `python -m tools.check_adr_invariant_matrix`; `tests/tools/test_check_adr_invariant_matrix.py` imports `check_invariant_matrix_test_paths`. None is modified.
- Names created by an earlier row: none. Names created here are marked `(new)` below.
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- Keep the new rules as pure functions over lines and a mapping so tests need no filesystem (`check_adr_body_evidence_cells` (new), `check_body_index_agreement` (new)); only `collect_issues()` does I/O.
- Resolve an invariant's ADR file through the index `ADR List` table (`_adr_file_map` (new)), not a filename pattern. An ADR ID in the matrix with no mapped or no existing file is reported as a `WARNING` finding.
- Rule 2 compares the union of cited test file paths per `(ADR number, invariant number)`: body rows come from the `### Automated Tests` table's `Verifies` and `Implementation` columns, index rows from the matrix. A path cited as `file.py::test` or as a bare `file.py` counts as `file.py`. A finding is raised only when both sides cite at least one path and the sets differ.
- Both rules use a module constant `_BODY_RULE_SEVERITY` (new) set to `"WARNING"`, and the docstring states the promotion condition to `ERROR`: the corpus survey reports no finding and the repository owner approves, per the sign-off channel in `rules/coding.md` "Explicit sign-off gates".

## Alternatives considered

- Immediate `ERROR`: rejected, because ADR-003 still has six empty cells and the live run would fail unrelated changes.
- ADR file by filename pattern: rejected, because the `ADR List` table is stable under renames.
- Row-by-row comparison for Rule 2: rejected, because one invariant legitimately spans several body rows and the survey showed it over-reports.

## Implementation
### Target file

`tools/check_adr_invariant_matrix.py`

### Procedure

1. Phase 1 re-check (read-only): read the implemented marker text in `docs/10_adr/adr_01_index.md` and in the ADR-001 and ADR-002 body tables; re-run the corpus survey; confirm every ADR ID resolves.
2. Add `_BODY_RULE_SEVERITY` (new) and a `_NOT_VERIFIED_RE` (new) matching a cell that begins with `Not verified` (case-insensitive), using the marker confirmed in step 1.
3. Add `_adr_file_map` (new): parse the `## ADR List` table of the index lines into `{ "001": "docs/10_adr/<file>" }`, reading the ID and File columns by header name.
4. Add `_body_automated_tests_rows` (new): from an ADR body's lines, return `(line_no, verifies_ids, implementation_cell)` for each data row of the `### Automated Tests` table, parsing by header name and returning nothing when the table or the `Implementation` column is absent.
5. Add `check_adr_body_evidence_cells` (new) for Rule 1: an empty or `-` Implementation cell that does not match `_NOT_VERIFIED_RE` (new) yields an `Issue` naming the ADR file, the invariant IDs and the line number.
6. Add `check_body_index_agreement` (new) for Rule 2 per the Design decisions; parse index rows that name several ADRs or invariants (for example `ADR-002 INV-01, INV-02 and ADR-004 INV-07, INV-10`) by splitting on ` and ` before an `ADR-` token.
7. Extend `collect_issues()`: after the existing rule, read each ADR body file mapped by `_adr_file_map` (new) (skip and report an unreadable one as a `WARNING`), run both rules, and return the concatenated list. Do not change the early `ERROR` return when the index is missing.
8. Update the module docstring (new rules, severity, promotion condition) and the `argparse` description.

### Method

Pure helper functions with explicit type annotations (`list[Issue]`, `dict[str, list[str]]`); no new third-party import; paths built from `REPO_ROOT`. Read-only: no file is written.

### Details

- `Issue` fields stay `file`, `line_no`, `severity`, `message`; body-rule `file` is the ADR file's base name.
- Follow `rules/coding.md`: comments and messages in English, line length 88, no bare `except`.
- Keep `_matrix_rows()` unchanged (complexity grade B today); add no branching to it.

## Compatibility considerations

Existing callers keep working: `check_invariant_matrix_test_paths()` signature and result are unchanged, `ADR_INDEX` and `_TEST_PATH_RE` are untouched, `render_json()` keys are unchanged, and a `WARNING` does not change the process exit code (`report_and_exit()` exits 1 only for an `ERROR`). The live run MUST exit 0 and print warnings for the remaining empty cells and body/index disagreements.

## Security considerations

N/A: read-only, local files only, no subprocess, network, or credential.

## Rollback considerations

Revert the commit. The hook and the consumer need no change because their contracts are untouched.

## Validation plan

- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` (after row 02).
- `uv run ruff format tools/check_adr_invariant_matrix.py`, `uv run ruff check tools/check_adr_invariant_matrix.py --fix`, then `uv run ruff check tools/check_adr_invariant_matrix.py`.
- `uv run mypy tools/check_adr_invariant_matrix.py` (explicit path) and `uv run bandit tools/check_adr_invariant_matrix.py`.
- Live smoke test: `uv run python tools/check_adr_invariant_matrix.py` and `--format json`; exit 0, warnings only.
- Consumer check: `uv run python .github/run_cited_adr_tests.py --help` or an equivalent import check.
- `uv run pre-commit run adr-invariant-matrix --all-files`.
- diff-cover threshold per `rules/toolchain.md` Completion checklist (baseline was `Not available` in planning).

## Completion criteria

- Rule 1 and Rule 2 report `WARNING` findings on the live corpus and nothing for a cell with the marker or a cited test, or for agreeing citations.
- The existing rule, JSON keys, exit-code behavior, `_TEST_PATH_RE` and `ADR_INDEX` are unchanged and the consumer still loads the module.
- The docstring and help text state both rules, the severity and the promotion condition.
- ruff, mypy, bandit and the pre-commit hook report no finding.

## Out of Scope

- Fixing the empty cells of ADR-001, ADR-002 or ADR-003.
- Making the index machine-generated; running the cited tests (a GV-012 sub-step).
- Defining the Verification Status vocabulary.
- Modifying `.github/run_cited_adr_tests.py` or `.pre-commit-config.yaml`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-check preconditions, marker text and corpus survey (read-only) | Pending | — | — | UNK-01, UNK-03 |
| 2 | Add constants, parsing helpers, Rule 1 and Rule 2, extend `collect_issues()` | Pending | — | — | |
| 3 | Update the docstring and help text | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | Done in row 02 |
| 5 | Run the validation sequence for `tools/` (`routing.md` "Adding a new tool") | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (empty body cell rule), `REQ-002` (body/index agreement rule), `REQ-003` (warning severity, promotion condition), `REQ-004` (existing contracts unchanged)
- **Source issue**: issues/20261027-102002_govrev005_adr-matrix-checker-extension.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105004_govrev005_adr-matrix-checker-extension.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-112226
- **Related target files**: tools/check_adr_invariant_matrix.py
