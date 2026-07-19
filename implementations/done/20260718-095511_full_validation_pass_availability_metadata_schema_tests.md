# Implementation procedure: full validation pass — MCP runtime availability metadata schema tests (requirement 18, plan step 5)

Source plan: `plans/20260717-175630_plan.md` ("Add schema tests for MCP runtime availability
metadata", requirement 18), Implementation step 5 and the plan's own Validation plan table.

**Disambiguation note (per this batch's established convention)**: the generic slug
`full_validation_pass` has already been reused by multiple unrelated plans in this batch (confirmed
via `ls implementations/*full_validation_pass*.md`: at least 8 distinct existing docs, e.g.
`20260717-202631_full_validation_pass.md` (plugin removal), `20260718-032349_full_validation_pass.md`,
`20260718-033059_full_validation_pass_mcp_tools_diagnostics.md`,
`20260718-084253_full_validation_pass_mcp_schema_version.md`,
`20260718-090322_full_validation_pass_config_dependent_rename.md` (requirement 14's own),
`20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md` (requirement 15's own),
`20260718-091922_full_validation_pass_call_tool_disabled_gate.md` (requirement 16's own)). Checked
each of those docs' Goal lines directly (via filename + grep) before writing this one: none names
`tests/test_tool_schema.py` or `tests/test_tools_endpoint.py` or requirement 18. None covers this
plan's specific two new test files. This doc is therefore named with the feature slug
(`availability_metadata_schema_tests`) rather than the bare generic term, per this batch's
established convention, and is not a duplicate.

## Goal

Run the full standard validation sequence (`rules/toolchain.md`) scoped to this plan's two new test
files, `tests/test_tool_schema.py` and `tests/test_tools_endpoint.py`, once both are written (per
their own companion docs,
`implementations/20260718-095325_test_tool_schema.py.md` and
`implementations/20260718-095410_test_tools_endpoint.py.md`), confirming the plan's own Validation
plan table (lines 178-192 of the source plan) passes end-to-end.

## Scope

**In scope**: running every check in the source plan's Validation plan table against exactly
`tests/test_tool_schema.py` and `tests/test_tools_endpoint.py`, plus the full-repo regression/coverage/
pre-commit gates the plan's table itself specifies as repo-wide (not file-scoped).

**Out of scope**: re-running validation for the other implementation docs in this batch (each has
its own file-scoped Validation plan table, e.g. the two companion docs above already specify their
own `ruff`/`mypy`/`bandit`/`pytest` commands for the individual files) — this doc is the final,
combined, cross-file pass tying both new files together plus the repo-wide gates, matching the same
role the other `full_validation_pass_*` docs in this batch play for their own plans.

## Assumptions

- Both new test files are expected to contain `xfail(strict=True)`-marked assertions at the time this
  validation pass first runs, per
  `implementations/20260718-095246_requirements_14_15_landing_check_for_availability_metadata_schema_tests.md`
  (requirements 14/15 have not landed in real `scripts/` source as of this writing). A "pass" for the
  `pytest` checks below means all non-`xfail` assertions succeed and all `xfail`-marked cases report
  `xfail` (not `XPASS`), not that every assertion is a hard pass — this is the plan's own explicitly
  documented expected state until requirements 14/15 land (see the plan's own Validation plan row:
  "all pass (or all `xfail` as expected... until requirements 14/15 land)").
- `diff-cover` is run against the diff introduced by these two new files only; since they are pure
  test additions, "coverage" here means the test code itself is exercised by `pytest` runs (no
  separate test-of-tests needed), matching the plan's own Validation plan note.
- This doc, like its sibling `full_validation_pass_*` docs elsewhere in this batch, records the
  procedure to run once the files exist as real code — this documents-only workflow pass does not
  itself execute the commands against non-existent files (both target test files are currently only
  documented, not yet written as real `tests/*.py` source, consistent with this being a documents-only
  batch pass).

## Implementation

### Target file

None (process/checklist step spanning `tests/test_tool_schema.py` and `tests/test_tools_endpoint.py`,
not a single source file).

### Procedure

1. Run `uv run ruff format tests/test_tool_schema.py tests/test_tools_endpoint.py` — expect clean
   (no reformatting needed, i.e. exit 0 with no diff).
2. Run `uv run ruff check tests/test_tool_schema.py tests/test_tools_endpoint.py` — expect 0 errors.
3. Run `uv run mypy tests/test_tool_schema.py tests/test_tools_endpoint.py` — expect no new errors.
4. Run `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations; both files import only
   `mcp_servers.*`/`shared.tool_constants`, consistent with the `agent -> all layers` import contract
   (test files sit outside the four production layers but must not introduce a disallowed edge).
5. Run the repo's ast-grep no-bare-except check per `rules/coding.md` convention — expect clean.
6. Run `uv run bandit -r tests/test_tool_schema.py tests/test_tools_endpoint.py` — expect no new HIGH
   findings.
7. Run `uv run pytest tests/test_tool_schema.py tests/test_tools_endpoint.py -v` — expect all pass or
   expected `xfail` per Assumptions above.
8. Run `uv run pytest -m "not integration"` then `uv run pytest` (full regression) — expect all pass,
   confirming the two new files do not destabilize any other test module.
9. Run `diff-cover` on the changed lines (the two new files) — expect >= 90%.
10. Run `grep -rn "xfail" tests/test_tool_schema.py tests/test_tools_endpoint.py` — expect nonzero
    matches today (both files carry `xfail`-gated cases per the landing-check gate), and expect 0
    matches only after requirements 14/15 land and the gate doc's step 6 procedure has been carried
    out.
11. Run `uv run pre-commit run --all-files` — expect pass.

### Method

Direct command execution in sequence, matching `rules/toolchain.md`'s standard validation sequence,
scoped via explicit file arguments where the tool supports it (`ruff`, `mypy`, `bandit`, targeted
`pytest`), and repo-wide where the plan's own table specifies repo-wide checks (`lint-imports`,
full `pytest`, `pre-commit`).

### Details

No pseudocode needed — this is a command-execution procedure, not a code change. The exact command
list and expected targets are given verbatim in Procedure steps 1-11 above, mirroring the source
plan's own Validation plan table (lines 180-192) without alteration.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format tests/test_tool_schema.py tests/test_tools_endpoint.py` | clean |
| Lint | `uv run ruff check tests/test_tool_schema.py tests/test_tools_endpoint.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_schema.py tests/test_tools_endpoint.py` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Static analysis | ast-grep no-bare-except check | clean |
| Security | `uv run bandit -r tests/test_tool_schema.py tests/test_tools_endpoint.py` | no new HIGH findings |
| Tests (scoped) | `uv run pytest tests/test_tool_schema.py tests/test_tools_endpoint.py -v` | all pass or expected `xfail` |
| Full regression | `uv run pytest -m "not integration"` then `uv run pytest` | all pass |
| Coverage | `diff-cover` on changed lines | >= 90% |
| Residual xfail | `grep -rn "xfail" tests/test_tool_schema.py tests/test_tools_endpoint.py` | 0 matches once requirements 14/15 land (see landing-check gate doc) |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
