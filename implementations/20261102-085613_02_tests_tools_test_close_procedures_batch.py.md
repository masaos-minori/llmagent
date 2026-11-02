## Goal
- Create `tests/tools/test_close_procedures_batch.py`, unit tests for `tools/close_procedures_batch.py` covering each refusal, the explicit row-completion option, staged-only archival, partial failure, Plan step mapping, and `Work Items Created` updates (`REQ-002` to `REQ-005`; AC-1 to AC-4).

## Scope
- In scope: the new test module only. It exercises the tool created by the row 01 procedure; it does not modify any other file.

## Assumptions
- Plan A1, A4, A10 apply. This procedure runs after the row 01 procedure (earlier `seq`): the module `tools.close_procedures_batch` and the names `verify_procedure`, `parse_plan_steps`, `check_step_marking`, `update_work_items`, and `main` will exist when `code-implementation` executes this row; the stale check may report them until then.
- Step 3a verified (2026-11-02): `tests/tools/test_manage_workitem_stage.py` builds a throwaway repository with a `temp_git_repo` fixture (`git.Repo.init(tmp_path)`, `plans/done` and `implementations/done` directories, an initial commit) and the source tool resolves `plans/` and `implementations/` relative to the current directory, so the new tests chdir into the temporary repository with `monkeypatch.chdir`. `tests/tools/test_set_execution_status.py` shows the fixture-text style (a full procedure body with the Execution Status table). Tests import tools as `tools.<module>`.
- Overlap: no other Plan targets this file.

## Design decisions
- Build fixtures with small helper functions (a procedure text builder taking row statuses, a Plan text builder taking steps and `Work Items Created` rows) so each test states only what differs.
- Pure functions are tested on text; the staged-rename and partial-failure tests use the git fixture and assert on `git status --porcelain` (renames staged, nothing committed: `HEAD` unchanged).

## Alternatives considered
- Mocking `move_to_done` everywhere: rejected for the staging tests (the point is the real staged rename); used only to force one archive failure.

## Implementation
### Target file
`tests/tools/test_close_procedures_batch.py` (new)

### Procedure
1. Create the module with the docstring header, imports, and the fixture and builder helpers.
2. Add the refusal tests (`REQ-002`): a `Pending` row (message names the row, no file changed), a `Blocked` row, an existing destination in `implementations/done/`, and a Plan that cannot be found; each asserts file bytes unchanged.
3. Add the explicit completion tests (`REQ-002`): `--complete-rows` without `--note` is a usage error; with both, only `Pending` rows become `Completed` and a `Blocked` or `N/A` row is never overwritten (Plan A10).
4. Add the dry-run test (AC-1): the output lists row changes, archives, step mappings, and `Work Items Created` updates, and the working tree and index are unchanged; a real run on the same fixture applies exactly the listed changes.
5. Add the archival tests (`REQ-003`): renames appear as staged renames and `HEAD` is unchanged; with one archive forced to fail, it is reported and the other procedures still archive, and the exit status is 1.
6. Add the Plan step tests (`REQ-004`): a named step citing two files with one archived is left unchanged and reported; a named step with all cited files archived (this batch's included) is marked `Completed`; an unparseable step is refused; with no step named, candidates are listed and nothing is changed; a check-only step that cites a file is not marked unless named.
7. Add the `Work Items Created` tests (`REQ-005`): a matching row becomes `Completed`; a Plan with no row for a document is handled without failure and the document is reported unmatched; an unverified (refused) document's row is untouched.
8. Add the companion test: a procedure whose `Related target files` lists a primary target and a companion test path counts for both paths in the step check.

### Method
- Use `tmp_path`, `monkeypatch.chdir`, and `capsys`; call `main([...])` and assert on the return code and captured output.
- Fixed timestamps are not needed; assert on status values and not on the `Completed` stamp text beyond its format.

### Details
- Keep each test under one behavior; share the repository fixture instead of re-initializing it per test where tests do not stage files.

## Compatibility considerations
- N/A: new test file.

## Security considerations
- N/A: tests use temporary directories only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_close_procedures_batch.py -v` all pass.
- `uv run ruff format tests/tools/test_close_procedures_batch.py`, `uv run ruff check tests/tools/test_close_procedures_batch.py`, and `uv run mypy tests/tools/test_close_procedures_batch.py` clean (pass the path explicitly).

## Completion criteria
- Every refusal, the completion option, dry run, staged-only archive, partial failure, step mapping case, and row update case in Procedure steps 2 to 8 has a passing test.

## Out of Scope
- Changing any other test module; testing `close-batch` or `set_execution_status.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the test module per Implementation > Procedure steps 1 to 8 | Pending | — | — | |
| 2 | Run the tests and fix failures per Validation plan | Pending | — | — | |
| 3 | Run ruff format, ruff check, and mypy on the test file (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (refusals, explicit completion, dry run), `REQ-003` (staged archive, partial failure), `REQ-004` (step mapping), `REQ-005` (row updates)
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080631_flowimp008_workitem-bulk-close.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085613
- **Related target files**: tests/tools/test_close_procedures_batch.py
