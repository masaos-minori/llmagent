## Goal
- Add tests for `list --plan --order`, including a Plan with no procedures (`REQ-004`).

## Scope
- In scope: new test functions appended to the existing module.
- Out of scope: edits to existing tests and to flowimp002's unit-grouping tests.

## Assumptions
- Names that only the row 03 procedure creates (`cmd_list_order`) will exist when `code-implementation` executes the rows in `seq` order.
- Row 03 adds `cmd_list_order` and the `--plan`/`--order` options; this document runs after it.
- Step 3a verified: the module imports from `tools.manage_workitem_stage`, uses `git.Repo` fixtures for archival tests, and `_plan_text`/`_batch_plan_text` factories; `cmd_list` tests change directory with `monkeypatch.chdir(tmp_path)` because `_get_workitem_files` uses relative `Path("implementations")`.
- Overlap (Step 2): `plans/20261102-080336_flowimp002_plan-release-units.md` also appends tests to this module (unit grouping): a sequencing dependency, append-only on both sides; whichever lands second rebases.

## Design decisions
- Use `main([...])` with `capsys` and `monkeypatch.chdir(tmp_path)` and build `plans/` and `implementations/` fixtures by hand; no git repo needed for a read-only view.

## Alternatives considered
- N/A: matches the existing `list` tests.

## Implementation
### Target file
`tests/tools/test_manage_workitem_stage.py`

### Procedure
- Append a helper `_order_fixture(tmp_path)` (new) writing one Plan whose steps 1 and 2 cite two target files, and three procedures whose `Source plan` is that Plan (two matching a step, one matching none).
- Append the cases under Method.

### Method
- Order: procedures print under `Phase 1` and `Phase 2` in step order, and by `seq` within a phase.
- Unmatched: a procedure whose target file no step cites prints last with the `WARNING: no Plan step cites` line.
- No procedures: a Plan with no matching procedure prints `No procedures found for plan` and exits 0.
- Archived Plan path: `plans/done/x.md` and `plans/x.md` select the same procedures.
- Gated: a procedure whose first pending row Notes start with `Gated:` prints the `[gated]` suffix.
- Flags: `--order` without `--plan` exits 2; a missing plan path exits 1; plain `list --kind plan` output is unchanged (regression).

### Details
- Keep the new cases after the existing `list`/`show` tests so a rebase with flowimp002 touches only the file end.

## Compatibility considerations
- N/A: append-only; no existing test or fixture changes.

## Security considerations
- N/A: tests write only under `tmp_path`.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v`.
- `uv run ruff format tests/tools/test_manage_workitem_stage.py`; `uv run ruff check tests/tools/test_manage_workitem_stage.py`.

## Completion criteria
- Order, unmatched, no-procedure, archived-path, gated, and flag cases exist and pass; all existing tests in both modules still pass.

## Out of Scope
- The implementation (row 03); flowimp002's grouping tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tests described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Run the validation sequence |

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
- **Requirement ID**: REQ-004 (order view tests, including a Plan with no procedures)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tests/tools/test_manage_workitem_stage.py
