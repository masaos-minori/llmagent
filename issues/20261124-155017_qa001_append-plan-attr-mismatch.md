# Fix the append_plan_work_items implementations-directory attribute mismatch that errors 6 tests

## Priority
High

## Summary
`tools/append_plan_work_items.py` no longer defines the module attribute its tests monkeypatch, so
all 6 tests in `tests/tools/test_append_plan_work_items.py` fail at fixture setup and the CI test
job cannot pass. Restore one shared name so the fixture redirects the directory the tool actually
reads.

## Background
- The tool used to import the directory constant from the sibling generator: the pre-change version
  of the tool had `from tools.generate_workitem import _PASS_TIMESTAMP_MARKER_RE, IMPLEMENTATIONS_DIR`
  at line 46 and globbed `IMPLEMENTATIONS_DIR` at line 107 (`git show 94eab21c1^:tools/append_plan_work_items.py`).
- Commit `94eab21c1` ("feat(tools): add the read-only gate runners a procedure pass needs", merged
  from upstream on 2026-11-24) rewrote the tool (416 lines changed) and introduced a local constant:
  `IMPL_DIR = REPO_ROOT / "implementations"` at `tools/append_plan_work_items.py:38`, used at
  `tools/append_plan_work_items.py:99`.
- `tools/generate_workitem.py` still exposes `IMPLEMENTATIONS_DIR` (`tools/generate_workitem.py:99`,
  used at line 242), so the repository now carries two names for the same directory.
- The test file was last touched by `7e992a0d2`, i.e. before the rename, and still patches the old
  name at `tests/tools/test_append_plan_work_items.py:78`.

## Problem
`uv run pytest tests/tools/test_append_plan_work_items.py -q` ends with `6 errors in 0.23s`. Every
error is a fixture-setup `AttributeError: <module 'tools.append_plan_work_items' ...> has no
attribute 'IMPLEMENTATIONS_DIR'` raised by the `batch` fixture (`raising=True` is the default).
Affected tests:
- `test_appends_one_row_per_document_of_the_pass`
- `test_a_document_of_another_plan_is_not_added`
- `test_an_unresolvable_step_is_reported_and_stops_the_write`
- `test_rows_are_not_added_twice_on_a_resumed_pass`
- `test_dry_run_prints_the_diff_and_writes_nothing`
- `test_missing_plan_exits_two_and_an_absent_marker_exits_one`

Additional finding (verified 20261124 during the mcpai003 batch, after renaming the constant to
`IMPLEMENTATIONS_DIR` locally and reverting it): the attribute name is only the first mismatch. With
the name restored the 6 tests fail at the call site instead — `TypeError: main() takes 0 positional
arguments but 1 was given` — and the tests also use `tool.table_data_rows(...)` and
`tool.WORK_ITEMS_HEADING`, which the shipped tool does not define (it has `WORK_ITEMS_HEADER` and
parses the section another way). So the fix is not name-only: the tool and the test must agree on the
`main(argv)` entry point and the row-reading helper as well, or the test file must be rewritten
against the shipped contract. The whole-suite count on the current `master` is
`13959 passed, 5 skipped, 6 errors`. CI runs
`uv run pytest -v -n logical --cov=scripts --cov-report= tests/` (`.github/workflows/ci.yml:87`)
with no deselection, so the test job fails for every commit since `94eab21c1`. The GitHub Actions
run status itself is not observed from this environment (no `gh` authentication); the failure is
confirmed by local reproduction of the same command CI runs.

## Reason for Change
The repository's test gate is red on `master`, which blocks every following change and hides real
regressions behind a known-red job. The pair also signals an undeclared coupling: the tests reach
into a module constant that the module no longer owns.

## Implementation Intent
Pick one name and make the tool and its tests agree on it, keeping the isolation the tests were
designed for. Two shapes are acceptable:
- Rename the tool's constant back to the shared name (`IMPLEMENTATIONS_DIR`) so both work-item
  tools expose the same path constant; or
- Keep `IMPL_DIR` and update the test fixture to patch that name.
Either way the fixture must still point the tool at a `tmp_path` directory, so no test can touch
the real `implementations/`. Prefer the shape that leaves a single definition of the path constant
in the work-item tooling rather than two.

## Target Files or Areas
- `tools/append_plan_work_items.py`
- `tests/tools/test_append_plan_work_items.py`

## Required Changes
- Reproduce the failure: `uv run pytest tests/tools/test_append_plan_work_items.py -q` (6 errors).
- Grep for every remaining reference to the removed name on this module:
  `rg "IMPLEMENTATIONS_DIR|IMPL_DIR" tools tests` and reconcile the two constants.
- Apply the chosen rename (tool side or fixture side) as a name-only change; do not alter the
  tool's pass-validation or row-writing behavior.
- Confirm the fixture genuinely isolates the tool: with the fix in place, a test that points the
  fixture at an empty `tmp_path/implementations` directory must not see the repository's real
  `implementations/20261124-*` documents.
- Re-run the target file, then the whole suite, then the gates for the changed paths
  (`uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages`).
- If the tool's public surface is described in `tools/TOOL_DESCRIPTIONS.md`, confirm the row stays
  accurate (the current row at `tools/TOOL_DESCRIPTIONS.md:116` names no constant, so no change is
  expected).

## Constraints
- Behavior of `append_plan_work_items.py` (row coverage validation, companion eligibility, exit
  codes `0`/`1`/`2`) MUST NOT change; the tool's contract is the shipped one unless the plan for this
  issue decides otherwise. The Additional finding above shows the mismatch is a contract mismatch, so
  the plan must first decide which side is canonical: the shipped CLI contract (`main()` reading
  `sys.argv`, `{pass timestamp} {plan.md}`) or the test's (`main(argv)`, `table_data_rows`,
  `WORK_ITEMS_HEADING`).
- Suppressing the error with `monkeypatch.setattr(..., raising=False)` or `object.__setattr__` is
  not acceptable: the attribute would exist while nothing reads it, so the tests would silently
  read the real `implementations/` and become vacuous.
- `tools/generate_workitem.py`'s own `IMPLEMENTATIONS_DIR` may be left as-is if the tool-side rename
  is not chosen; do not change its behavior.
- Do not touch the 14 `procedure-length` advisory findings reported by
  `tools/check_workitem_structure.py` for the `implementations/20261124-122732_*` documents; they
  belong to the `cliplc003` batch that generated them (see `issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md`
  for the related gate discussion).

## Acceptance Criteria
- `uv run pytest tests/tools/test_append_plan_work_items.py -q` reports all tests passing, 0 errors.
- `uv run pytest tests/ -n logical -q -m "not integration and not production_paths_allowed and not repo_scan"`
  reports 0 errors.
- `rg "IMPLEMENTATIONS_DIR|IMPL_DIR" tools tests` shows one consistent name per module and no test
  patching an attribute the module does not define.
- Reverting the fix re-breaks the tests as failures (not as setup errors), which shows the fixture
  still drives real behavior.
- CI test job green.

## Testing Expectations
- Existing unit tests in `tests/tools/test_append_plan_work_items.py` are the regression cover; they
  must keep exercising `tmp_path` isolation, not merely stop erroring.
- Whole-suite run per `rules/toolchain.md` with the standard deselect markers.
- Lint and type gates on the changed files only; no coverage gate impact expected (no new branches).

## Documentation Impact
No documentation update required: the fix restores an existing contract rather than changing
behavior. Verify `tools/TOOL_DESCRIPTIONS.md`'s `append_plan_work_items.py` row remains accurate; no
Known Issue or Needs Confirmation entry is needed once the suite is green.

## Out of Scope
- Changing what `append_plan_work_items.py` validates, its diff output, or its exit codes.
- Renaming `tools/generate_workitem.py`'s path constants beyond what the chosen fix requires.
- The `workitem-structure` hook failure and the `procedure-length` advisories (separate issue).
- CI workflow edits.

## Dependencies
- Context only: upstream commit `94eab21c1` introduced the rename; the tests date from `7e992a0d2`.
- No other issue, plan, or external work blocks this fix.

## Unresolved Questions
- `不明`: whether `IMPL_DIR` was an intentional rename or an accident of the `94eab21c1` rewrite; the
  commit message does not say. The maintainer's preference for one canonical constant name decides
  which shape to apply.
- `不明`: whether the same commit left other tool/test attribute-name drift beyond this pair. The
  whole-suite run shows only these 6 errors, which is evidence but not a full audit.

## AI Implementation Instruction
Change only the constant name on one side of the pair, verify the fixture still redirects the
directory the tool reads, and prove the tests are not vacuous by confirming a revert fails as an
assertion rather than as a setup error. No suppression flags, no test skips, no CI changes.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-155017
- **Related target files**: `tools/append_plan_work_items.py`, `tests/tools/test_append_plan_work_items.py`
