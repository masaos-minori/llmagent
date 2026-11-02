## Goal
- Make `tools/check_workitem_traceability.py` accept a document whose `Related target files` lists a target and its companions, still report a differing list (`REQ-003`: list-aware equality), and add an opt-in per-Plan coverage and uniqueness mode (`REQ-002`: covered, uncovered, duplicate, and multi-row companion detection).

## Scope
- Modify only `tools/check_workitem_traceability.py`: a list reader and a companion reader (new helpers), the equality check, a new coverage check, and one CLI option. The default scan, finding categories, exit rules, and the `workitem-traceability` pre-commit hook invocation (`--active-only`) stay as they are. Medium blast radius (a pre-commit hook runs it).

## Assumptions
- A1: Step 3a (verified by Read and `rg`, 2026-11-02): `_clean_field_value` keeps only the first whitespace-delimited token, so `extract_related_target_files_value` returns only the first path of a list; `find_target_file_mismatches` compares that token with the first token of `### Target file`. Without a new reader a list would pass or fail on its first path alone and a differing tail would go unreported (Plan Background correction). The existing function is therefore left as it is for single-target documents and a new list reader is added (Plan A12).
- A2: Step 3a: `find_no_procedure_yet` matches Plans by `Source plan` field value; the same field, matched by basename so `plans/<file>` and `plans/done/<file>` agree, selects a Plan's documents in the coverage check. `discover_documents` reads the six work-item directories relative to `ROOT_DIR`, which the tests monkeypatch.
- A3: Decision (Plan A3): the coverage check is a separate option taking a Plan path, `--plan-coverage PLAN`, not part of `collect_findings` and not run by the hook, because a Plan mid-batch legitimately has uncovered rows. When given, only coverage findings are produced and the exit code is 1 on any finding (REQ-002 "MUST fail when a row is uncovered").
- A4: The Plan table is read by header: the `File Path` and `Related Tests` columns are located by their header text in the `## Implementation Target Files` table, because `tools/generate_workitem.py` `extract_target_file_rows` returns only the first column. A `Related Tests` cell is scanned for backticked paths; prose cells (tool names, `itself`) yield none (Plan A1: cells that are prose tie no test to a row).
- A5: Overlap judgment (Step 2, 2026-11-02): this file is targeted by no other active Plan. The other Plans that read `Related target files` (flowimp008, Plan A6) must read it as a list; this procedure's list reader is the reference form (comma-separated, backticked, target first).
- A6: Companion section parsing is defined by the `seq` 03 template note: a top-level bullet in `### Companion test files` whose first backticked token is the path; the section ends at the next heading.

## Design decisions
- New helpers: `extract_related_target_files_list` (new) returns the backticked paths of the field in order (falling back to the first token when none are backticked), and `extract_companion_files` (new) returns the companion paths of the body section; both return an empty list when absent.
- `find_target_file_mismatches` keeps the existing comparison when the body has no companion section (identical findings for documents without companions) and, when it has one, compares the list reader's result with the body target followed by its companions: the first path must equal the target and the remaining set must equal the companions.
- Coverage findings use four categories: `row-uncovered`, `path-covered-twice`, `companion-multi-row`, `companion-not-eligible`.

## Alternatives considered
- Change `_clean_field_value` to keep a list: rejected; every other field relies on the first-token rule.
- Add the coverage check to `collect_findings`: rejected (A3).

## Implementation
### Target file
`tools/check_workitem_traceability.py`

### Procedure
1. Add `_COMPANION_HEADING_RE` (new) next to `_TARGET_FILE_HEADING_RE`, and a backtick-path regex `_BACKTICK_PATH_RE` (new).
2. Add `extract_related_target_files_list` (new) and `extract_companion_files` (new) after `extract_target_file_value`.
3. Extend `find_target_file_mismatches` as described; keep the finding category `target-file-mismatch` and a detail that names the declared list and the body's target and companions.
4. Add `_plan_target_rows` (new) returning `(file_path, related_tests_cell)` per table row, and `find_plan_coverage_findings` (new) taking the Plan path, the documents, and returning findings; add the module-level constant `COVERAGE_CATEGORIES` (new).
5. Add `--plan-coverage PLAN` to `build_arg_parser` and handle it first in `main`: build documents with `discover_documents`, run the coverage check, render with the existing renderers, exit 1 on any finding.
6. Extend the module docstring with two sentences (companions in the equality check; the opt-in mode).

### Method
- `find_plan_coverage_findings` (new): read the Plan rows; select documents with `kind == "implementation"` whose `Source plan` basename equals the Plan basename (active and `done/`); for each, `covered = [target] + companions` from `extract_target_file_value` and `extract_companion_files` (new).
- `row-uncovered`: a Plan row whose path is in no `covered` list. `path-covered-twice`: a path appearing in the `covered` lists of two documents (or twice in one). `companion-multi-row`: a companion path found in the `Related Tests` cell of two or more rows. `companion-not-eligible`: a companion that is not a Plan row, is not under `tests/`, or is not named in the `Related Tests` cell of its own document's target row.
- Findings are built with `make_finding(category, file, detail)`; `file` is the document path (or the Plan path for `row-uncovered`).

### Details
- Parse the Plan table by locating the `## Implementation Target Files` heading, the header row, and the cells by header names; stop at the next `## ` heading; unwrap backticks from the path cell.
- Report paths repository-relative as in the document text; no filesystem existence check is made (that is `audit_plan_target_paths.py`).
- `--plan-coverage` combined with `--age-threshold-days`, `--active-only` is accepted and ignored for the coverage mode; combined with `--format` it uses that format.

## Compatibility considerations
- The default scan and the hook are unchanged: no new argument is passed there and `collect_findings` is untouched. A document without a companion section produces the same `target-file-mismatch` findings as before (regression test in seq 06).

## Security considerations
- N/A: read-only text parsing of repository files; no subprocess, network, or write.

## Rollback considerations
- N/A: revert the commit; no persisted data changes.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_traceability.py -v`: all pass (tests in seq 06).
- `uv run ruff format tools/check_workitem_traceability.py`; `uv run ruff check tools/check_workitem_traceability.py`; `uv run mypy tools/check_workitem_traceability.py`; `uv run bandit tools/check_workitem_traceability.py`: clean.
- Smoke test on live data: `uv run python tools/check_workitem_traceability.py --active-only` (unchanged output) and `uv run python tools/check_workitem_traceability.py --plan-coverage plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (expected: no finding, since every row there has a document of its own; read any finding rather than trusting it).

## Completion criteria
- A document with a target and companions passes the equality check and a differing list is reported (AC-3); the coverage mode passes the Plan fixture of AC-2 and fails when a companion is removed, listed twice, or tied to two rows; the default scan output is unchanged; the four tool checks are clean.

## Out of Scope
- Adding the coverage mode to the hook or `collect_findings` (Plan A3), reading `Related target files` in other tools (flowimp008), `tools/TOOL_DESCRIPTIONS.md` text (Plan UNK-03), and path existence checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the list and companion readers, extend `find_target_file_mismatches` | Pending | — | — | |
| 2 | Add the Plan table reader, coverage check, and `--plan-coverage` option; update the module docstring | Pending | — | — | |
| 3 | Add or update tests per Validation plan (seq 06 procedure) | Pending | — | — | |
| 4 | Run the tool lint sequence (ruff format, ruff check, mypy, bandit) and the live-data smoke tests | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (coverage and uniqueness mode), REQ-003 (list-aware equality check)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tools/check_workitem_traceability.py`
