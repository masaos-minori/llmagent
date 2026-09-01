## Goal
Add `tests/tools/test_manage_workitem_stage.py` using a temporary git repository
fixture, covering: a successful move for each of the three subcommands; a blocked
move due to a `Pending` Execution Status row; and a forced move via `--force
--reason` (REQ-008).

## Scope
- In scope: unit tests for all three subcommands' success paths, the
  `Pending`-row block, and the forced override, entirely against a temporary git
  repository fixture (not the live repository).
- Out of scope: testing the deferred `close-plan` downstream-reference check
  (UNK-01, not part of this Plan's scope); testing malformed/reordered Execution
  Status table parsing beyond one well-formed fixture (per the Plan's Risks
  section, deferred as a follow-up hardening pass).

## Assumptions
- `tools/manage_workitem_stage.py` (seq 01 of this Plan) exposes
  `cmd_close_issue`/`cmd_close_plan`/`cmd_close_implementation` as importable
  functions, matching `tests/tools/test_manage_frontmatter.py`'s `from
  tools.manage_frontmatter import cmd_add_missing` precedent.
- The temporary git repository fixture is built via a `pytest` fixture that runs
  `git init` in a `tmp_path` directory and commits a fixture file under
  `issues/`/`plans/`/`implementations/` before each test invokes the subcommand
  under test.

## Design decisions
- One shared `pytest` fixture (e.g. `temp_git_repo`) builds the `git init`'d
  temporary repository and yields its path, reused across all test functions,
  rather than duplicating repo-setup boilerplate per test.
- The content-unchanged assertion (REQ-005) reads the moved file's bytes before
  and after the move and asserts equality, rather than asserting on specific
  Execution Status row values — this stays valid even if the fixture's Execution
  Status table content changes later.

## Alternatives considered
- Running these tests against a real clone of the live repository: rejected —
  the Plan's Scope explicitly requires a temporary git repository fixture, to
  keep tests fast, isolated, and independent of the live repository's actual
  content/history.

## Implementation
### Target file
`tests/tools/test_manage_workitem_stage.py`

### Procedure
1. **`close-issue`/`close-plan` success** (REQ-001, REQ-002; AC-1): in the
   temporary git repo fixture, create and commit a fixture file under
   `issues/{file}.md` (respectively `plans/{file}.md`), invoke
   `cmd_close_issue`/`cmd_close_plan`, and assert: the destination file exists
   under `issues/done/`/`plans/done/`, the source no longer exists, and `git
   status`/`git log --follow` on the temp repo shows the move recorded as a
   rename.
2. **Missing-source / existing-destination refusal** (REQ-001, REQ-002): invoke
   `cmd_close_issue`/`cmd_close_plan` against a nonexistent source path, and
   separately against a source whose destination already exists; assert
   non-zero exit / a raised error and no filesystem change in the fixture repo.
3. **`close-implementation` blocked-Pending case** (REQ-003; AC-2): create a
   fixture implementation-procedure file with an `### Execution Status` table
   containing at least one `Pending` row, invoke `cmd_close_implementation`
   without `--force`, and assert: non-zero exit / raised error, the blocking
   row's `Step`/`Description` named in the result, and the file was not moved.
4. **`close-implementation` forced override** (REQ-004, REQ-006; AC-3): invoke
   `cmd_close_implementation` on the same fixture with `--force --reason
   "test override"`, and assert: the move succeeds, the printed/returned result
   includes both the resulting path and the supplied reason string.
5. **Content-unchanged assertion** (REQ-005): read the fixture file's bytes
   before the move and again after the move (at its new `done/` path), and
   assert byte-for-byte equality — no Execution Status row was rewritten by the
   tool itself.
6. **Result/exit-code assertions** (REQ-006): for at least one success case and
   one failure case, assert both on the returned/printed resulting-path string
   and on the function's/process's exit code.

### Method
`pytest` test module using a `tmp_path`-based `git init`'d fixture repository
(one shared fixture function, reused via `pytest.fixture`); imports
`tools.manage_workitem_stage`'s `cmd_*` functions directly (not via
`subprocess`), matching `tests/tools/test_manage_frontmatter.py`'s import
pattern. Git-state assertions (rename detection) use `subprocess.run(["git",
"status", "--short"], cwd=temp_repo, ...)` or GitPython's own inspection API
against the temporary repo — never against the real repository the test suite
itself runs inside.

### Details
- The fixture repository must have at least one commit before any move is
  attempted (a `git mv`-equivalent operation on an uncommitted file is not the
  scenario under test — REQ-001/REQ-002's own scope is a normally-committed
  work-item file).
- The blocked-Pending fixture file's Execution Status table must exactly match
  `templates/execution-status.md`'s column structure (`Step | Description |
  Status | Started | Completed | Notes`), including the header separator row,
  so the parser under test sees a well-formed table (per this Plan's Risks
  section, malformed-table cases are an explicitly deferred follow-up, not part
  of this file's coverage).
- Tests must not leave any file or git state change outside the `tmp_path`
  fixture directory — no assertion or setup step touches the real
  `issues/`/`plans/`/`implementations/` trees.

## Compatibility considerations
New test file; no existing test module imports it. Adding it does not change any
existing test's behavior.

## Security considerations
Tests operate entirely inside a `tmp_path`-rooted temporary git repository — no
writes outside pytest's managed temporary directory, no network access, no
subprocess with untrusted input (git subprocess calls, if used for assertion,
pass a fixed argument list against the fixture path only).

## Rollback considerations
New file only; rollback is deleting
`tests/tools/test_manage_workitem_stage.py`. No other test or module depends on
it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_manage_workitem_stage.py` | Unit (temporary git repo fixture) | `uv run pytest tests/tools/test_manage_workitem_stage.py -v` | All cases pass: 3 successful moves, 1 blocked-Pending case, 1 forced-override case |
| `tests/tools/test_manage_workitem_stage.py` | Regression | `uv run pytest tests/tools/ -v` | No new failures (note: `tests/tools/test_check_agent_docs_consistency.py` has a pre-existing, unrelated collection error — not this file's responsibility) |

## Completion criteria
- `tests/tools/test_manage_workitem_stage.py` exists and covers all three
  subcommands' success paths, the `Pending`-row block, and the forced override,
  entirely against a temporary git repository fixture.
- `uv run pytest tests/tools/test_manage_workitem_stage.py -v` passes with no
  failures (requires `tools/manage_workitem_stage.py` from seq 01 of this Plan to
  exist first).

## Out of scope
- Testing the deferred `close-plan` downstream-reference check (UNK-01).
- Malformed/reordered Execution Status table parsing beyond one well-formed
  fixture.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-153344 | 20260901-153344 | Verified `cmd_close_issue`/`cmd_close_plan`/`cmd_close_implementation` take `argparse.Namespace` and return `int` (print, no `MoveResult` returned to caller) — built `args` via `build_parser().parse_args([...])`, matching actual source |
| 2 | Add or update tests per Validation plan | Completed | 20260901-153344 | 20260901-153344 | `tests/tools/test_manage_workitem_stage.py` created: 3 subcommands' success paths, missing-source/existing-destination refusals, Pending-row block, forced `--force --reason` override, content-unchanged (REQ-005), and printed-path/exit-code (REQ-006) assertions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-153344 | 20260901-153344 | `ruff format`/`ruff check`/`mypy` clean on the new test file |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-153344 | 20260901-153344 | N/A: no `docs/00_index.md` task-scope mapping for `tools/manage_workitem_stage.py` or this test file |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20260831-194739_tool004_manage_workitem_stage_transitions.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110946_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114646
- **Related target files**: `tests/tools/test_manage_workitem_stage.py`
