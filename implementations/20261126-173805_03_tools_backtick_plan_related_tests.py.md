## Goal
- Rewrite `tools/backtick_plan_related_tests.py` on top of the shared detector so it backticks the `File Path` cells, the `tests/...py` paths of `Related Tests`, and the target paths of `Implementation steps`, changes nothing else, and is idempotent (REQ-002, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the script and its companion test file. Out of scope: renaming the script (documented under this name), `close_procedures_batch.py`, and archived Plans.

## Assumptions
- Verified in Step 3a (experiment on a copy of `plans/done/20261126-161137_wfeff002_test-failure-baseline.md`): the current script changed 24 rows, wrapped the `Related Tests` and `deploy.sh Impact` header cells in backticks, rewrote the sixth cell of the `Affected areas` and `Execution Status` tables, splits cells at commas, always rewrites the file, and ignores `File Path` and steps; no test references it (`rg backtick_plan_related_tests tests` found nothing).
- Procedure 01 creates the detector first (`seq` order), so this document may import it.
- Sibling tools import with `from tools._atomic_write import ...` after the `sys.path` guard (`tools/set_execution_status.py`, `tools/compare_test_baseline.py`).

## Design decisions
- The script keeps its path and command line (`plan` positional) and gains `--dry-run` through `add_dry_run_argument`; it calls `wrap_plain_citations`, writes through `atomic_write_text` only when the text changed, prints `backticked <N> citation(s) in <plan>` (N = number of `find_plain_citations` results before the rewrite) or `no plain citations in <plan>`, and returns 0.
- A missing or unreadable plan path prints an error to stderr and returns 2 (tools convention).
- The module docstring states the extended scope in two or three lines and that other text is never changed.

## Alternatives considered
- A sibling script for steps: rejected (Plan D-1).

## Implementation
### Target file
`tools/backtick_plan_related_tests.py`

### Procedure
1. Write the companion tests first and run them against the current script (the damage cases fail).
2. Replace the body with the thin wrapper described above; keep `main(argv: list[str] | None = None) -> int` and the `__main__` guard (`raise SystemExit(main())`).
3. Run the companion tests, ruff, mypy, bandit.

### Method
- No parsing in this file: all reading and spans come from `tools/_workitem_citation_check.py`.

### Details
- Re-run the experiment: copy the wfeff002 Plan, run the script, and confirm `diff` shows only the intended spans (the target table `File Path` cells and the step citations), and a second run reports `no plain citations`.

### Companion test files
- `tests/tools/test_backtick_plan_related_tests.py` (new)
  - Procedure: import `from tools import backtick_plan_related_tests as bprt` and `from tools import close_procedures_batch as cpb`; write Plan files under `tmp_path`; cover: plain Plan becomes backticked in the three places and `find_plain_citations` finds none; a Plan with an `Affected areas` table, an `Execution Status` table with Notes, a `Related Tests` cell `N/A: data file, covered through x`, and a header row is byte-identical except the intended spans (compare with the backticks of the intended spans removed); second run changes nothing and `main` reports no plain citations; `--dry-run` writes nothing; a missing file returns 2; a fully backticked Plan (an `amend_plan.py`-style row) is unchanged; after normalizing, `cpb.parse_target_paths(text)` equals the set of target paths and `cpb.parse_plan_steps(text, paths)` gives each step its cited paths (AC-04).
  - Validation: `uv run pytest tests/tools/test_backtick_plan_related_tests.py`; the damage cases fail against the old script.

## Compatibility considerations
- The command line is unchanged (`uv run python tools/backtick_plan_related_tests.py plans/<plan>.md`); the behavior narrows (no longer touches other tables) and widens (File Path and steps). No caller exists in `skills/`, `templates/`, or `rules/` yet (procedures 07 and 08 add them).

## Security considerations
- N/A: edits a local Plan file the caller names, atomically, and only on an explicit run.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_backtick_plan_related_tests.py`; ruff format and check; mypy (CI invocation); `uv run bandit tools/backtick_plan_related_tests.py -c pyproject.toml`; the experiment of Details.

## Completion criteria
- Tests fail first (old script) and pass after; the experiment diff shows only intended spans; idempotent; the Plan mapping of AC-04 works.

## Out of Scope
- The checker finding (procedure 05) and the documents (procedures 07 to 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test file(s) first, then confirm they fail before and pass after | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-172913_wfeff003_plan-path-citations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-173805
- **Related target files**: `tools/backtick_plan_related_tests.py`, `tests/tools/test_backtick_plan_related_tests.py`
