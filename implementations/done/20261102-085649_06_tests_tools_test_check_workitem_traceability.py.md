## Goal
- Add tests to `tests/tools/test_check_workitem_traceability.py` for the list-aware equality check and the per-Plan coverage mode (`REQ-003`: equality with and without companions; `REQ-002`: covered, missing, duplicate, and multi-row companion cases).

## Scope
- Modify only `tests/tools/test_check_workitem_traceability.py`: new test classes beside `TestTargetFileMismatch`. Test-only; Low blast radius.

## Assumptions
- A1: Step 3a: the module uses `_write(path, text)`, `monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)`, and `cwt.discover_documents()` for fixtures; `TestTargetFileMismatch._write_implementation` builds a document with a `### Target file` value and a `Related target files` line (verified by Read, 2026-11-02). New classes follow the same pattern instead of changing existing ones.
- A2: The names under test (`extract_related_target_files_list`, `extract_companion_files`, `find_plan_coverage_findings`, the `--plan-coverage` option, the categories `row-uncovered`, `path-covered-twice`, `companion-multi-row`, `companion-not-eligible`) are created by the `seq` 05 procedure of this Plan, so they exist when these tests are written; they are cited with `(new)` only in the `seq` 05 document.
- A3: The fixtures are fixture Plans written under `tmp_path` (not real Plans), with a code row and two test rows (AC-2).

## Design decisions
- Two new classes, `TestCompanionEquality` (new) and `TestPlanCoverage` (new); helper `_write_plan(tmp_path, rows)` builds a Plan with an `## Implementation Target Files` table (columns `File Path` and `Related Tests`) and a `Traceability` section.
- Cases are one assertion-focused test each, so a failure names the rule.

## Alternatives considered
- Parametrize all coverage cases in one test: rejected; separate tests give clearer failure messages.

## Implementation
### Target file
`tests/tools/test_check_workitem_traceability.py`

### Procedure
1. Add `TestCompanionEquality` (new): list equal to target plus companions reports no finding; list missing a companion reports `target-file-mismatch`; list with an extra path reports it; first path not the target reports it; a document without a companion section behaves as before (existing cases stay).
2. Add `TestPlanCoverage` (new): a document with the code file as target and two test files as companions passes; removing a companion from the document yields `row-uncovered` for that test row; a test file listed by two documents yields `path-covered-twice`; a test file named in the `Related Tests` cell of two code rows yields `companion-multi-row`; a companion that is not a Plan row or not under `tests/` yields `companion-not-eligible`; a document of another Plan is ignored; `plans/done/` basename matching works.
3. Add a CLI case: `cwt.main(["--plan-coverage", str(plan)])` returns 1 on a finding and 0 when covered, and does not run the default categories.

### Method
- Use `monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)` and `_write` as the existing tests do; build documents with `### Target file`, an optional `### Companion test files` section, and a Traceability section carrying `Source plan` and `Related target files`.
- Compare `findings[i]["category"]` and that the detail names the path.

### Details
- Fixture Plan rows: `scripts/agent/foo.py` with `Related Tests` listing `tests/agent/test_foo.py` and `tests/agent/test_foo_edge.py`, plus the two test rows.
- No `freezegun` is needed; the coverage mode has no age logic.

## Compatibility considerations
- N/A: tests only; existing cases are not edited.

## Security considerations
- N/A: tests write only under `tmp_path`.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_traceability.py -v`: all pass.
- `uv run ruff format tests/tools/test_check_workitem_traceability.py` and `uv run ruff check tests/tools/test_check_workitem_traceability.py`: clean.

## Completion criteria
- The new tests cover covered, missing, duplicate, multi-row, and not-eligible companions and both equality directions, and pass (AC-2, AC-3).

## Out of Scope
- Changing existing test cases, and tests for tools other than `tools/check_workitem_traceability.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestCompanionEquality` (new) and `TestPlanCoverage` (new) and the CLI case | Completed | 20261102-133947 | 20261102-133947 | added TestCompanionEquality, TestPlanCoverage (+CLI cases); 44 passed (was 24); ruff, mypy clean; full suite deferred to plan end |
| 2 | Run the new tests and the lint commands in the Validation plan | Completed | 20261102-133947 | 20261102-133947 | — |

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
- **Requirement ID**: REQ-002, REQ-003 (tests for coverage and equality)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tests/tools/test_check_workitem_traceability.py`
