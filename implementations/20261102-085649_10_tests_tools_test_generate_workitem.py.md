## Goal
- Add tests to `tests/tools/test_generate_workitem.py` for the `--companion` option and the unchanged single-target scaffold (`REQ-005`: companion scaffold and unchanged single-target scaffold).

## Scope
- Modify only `tests/tools/test_generate_workitem.py`: a new test class using the existing `workitem_dirs` and `fixed_timestamp` fixtures. Test-only; Low blast radius.

## Assumptions
- A1: Step 3a: the module exposes the fixtures `workitem_dirs` and `fixed_timestamp` and calls `gw.main(argv)` with a `--source-plan` file under `tmp_path`; `TestFieldOrder` already compares the heading order of a single-target scaffold with the template (verified by Read, 2026-11-02). The new class does not change it.
- A2: The names under test (`--companion`, `apply_companions`, `companion_block`) are created by the `seq` 09 procedure of this Plan.
- A3: The unchanged-scaffold check compares the written file with `gw.extract_fenced_skeleton(gw.TEMPLATE_IMPLEMENTATION_PROCEDURE)` for the same row, byte for byte.

## Design decisions
- One class, `TestCompanionOption` (new), with focused tests; a helper `_run(argv_extra)` builds the base argv for a fixed Plan file, row, and `seq`.

## Alternatives considered
- Snapshot the whole scaffold text: rejected; assertions on the specific lines keep the intent visible.

## Implementation
### Target file
`tests/tools/test_generate_workitem.py`

### Procedure
1. Add `TestCompanionOption` (new): one companion lists the target and the companion in `Related target files` (target first), writes the target under `### Target file`, and inserts a `### Companion test files` block after `### Details` with `Procedure:` and `Validation:` lines; two companions list both in order; the file name is derived from the target path only.
2. Rejections, each returning non-zero with nothing written: a companion outside `tests/`; a companion equal to the target; a duplicated companion; `--companion` with `--all-rows`; `--companion` with another `--kind`.
3. Unchanged scaffold: the same call without `--companion` writes exactly the template's fenced skeleton.
4. Drift guard: the heading string the helper writes appears in `templates/implementation-procedure.md`.

### Method
- Call `gw.main([...])` and read the single created file under `workitem_dirs["implementations"]`; use `capsys` for the error text of rejections.

### Details
- Plan fixture: an empty Plan file written under `tmp_path`; the pass-timestamp marker side effect is tolerated as in the existing tests.

## Compatibility considerations
- N/A: tests only; existing cases are not edited.

## Security considerations
- N/A: tests write only under `tmp_path` and the monkeypatched work-item directories.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_generate_workitem.py -v`: all pass.
- `uv run ruff format tests/tools/test_generate_workitem.py` and `uv run ruff check tests/tools/test_generate_workitem.py`: clean.

## Completion criteria
- The option scaffold, every rejection, the byte-identical single-target scaffold, and the template drift guard are tested and pass (AC-6).

## Out of Scope
- Changing existing test cases and testing `--all-rows` grouping.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestCompanionOption` (new) | Pending | — | — | |
| 2 | Run the new tests and the lint commands in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (tests for the companion option and unchanged scaffold)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tests/tools/test_generate_workitem.py`
