# Implementation: full validation pass — requires_config -> config_dependent rename

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

Note on disambiguation: 4 other `*full_validation_pass*` docs already exist
under `implementations/` (`20260717-202631_full_validation_pass.md` — plugin
removal sweep; `20260718-032349_full_validation_pass.md` — docstring/comment
edits; `20260718-033059_full_validation_pass_mcp_tools_diagnostics.md` —
`cmd_mcp.py`/diagnostics; `20260718-084253_full_validation_pass_mcp_schema_version.md`
— schema-version rollout). Each has a Goal naming a DIFFERENT feature; none
covers this plan's `requires_config` -> `config_dependent` rename. This doc
is deliberately named with the feature slug (`config_dependent_rename`) to
avoid future collisions.

## Goal

Run the repo's standard validation sequence (`rules/toolchain.md`), scoped to
the files touched by this plan's 15 file-level implementation docs, plus a
repo-wide residual-string grep, to confirm the `requires_config` ->
`config_dependent` rename is complete, value-preserving, and introduces no
regressions.

## Scope

**In scope**: validation only — no new production/test code beyond what the
other 15 docs in this batch already specify (`read_tools.py.md`,
`write_tools.py.md`, `delete_tools.py.md`, `git_tools.py.md`,
`shell_tools.py.md`, `cicd_tools.py.md`, `github_tools_file.py.md`,
`github_tools_issues.py.md`, `github_tools_pull_requests.py.md`,
`github_tools_repository.py.md`, `test_mcp_tools_validation.py.md`, and the
4 doc-file updates). This doc must run AFTER all 15 of those are applied.

**Out of scope**: fixing failures found during validation — if a check
fails, that indicates one of the other 15 docs' Procedure was not followed
correctly or was itself incomplete; re-open the relevant per-file doc rather
than improvising a fix here.

## Assumptions

- The rename is purely mechanical (same boolean values, no schema/type
  changes) per every other doc in this batch, so no new mypy/bandit findings
  are expected; ruff format/check should be a no-op beyond the touched
  lines.
- `PYTHONPATH=scripts uv run lint-imports` is unaffected since this plan
  makes zero import changes (confirmed in the plan's Design section and its
  own Affected areas table: `server.py` and `tool_registry.py` need no
  changes).

## Implementation

### Target file

None (cross-cutting; no single file to edit — this doc only runs commands).

### Procedure

1. Confirm all 15 file-level docs in this batch have been applied to the
   real source files (10 Python renames, 1 test addition, 4 doc updates).
2. Run each command in the Validation plan table below, in order.
3. If the residual-string grep (`grep -rn "requires_config" scripts/ tests/
   docs/`) returns ANY match, do not proceed — identify which of the 15
   per-file docs was missed or incompletely applied, and re-apply it.
4. If the new pytest assertion
   (`test_all_tool_lists_use_config_dependent_not_requires_config`) is
   skipped or not collected, treat this as a hard failure per the plan's
   Risks table — investigate import errors or a wrong module path before
   considering the batch done.

### Method

Sequential command execution; no code changes in this doc itself.

### Details

- Scope the mypy/bandit runs to `scripts/` (repo convention per
  `rules/toolchain.md`); scope ruff format/check to `scripts/ tests/` since
  both directories were touched.
- The `diff-cover` check should show high coverage on the diff's line
  changes: for the 10 Python files, the changed lines are dict-literal
  key names already exercised by every existing test that imports
  `TOOL_LIST` (plus the new assertion test); for the 4 doc files, no code
  coverage applies (markdown is not measured).
- After this doc's validation passes, the target plan file
  `plans/20260717-173602_plan.md` is moved to `plans/done/` (a separate step
  in the 02_design.md workflow, not part of this validation doc).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/ tests/` | clean |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Static analysis (no bare except) | ast-grep no-bare-except check per repo convention | clean |
| Security | `uv run bandit -r scripts/` | no new HIGH findings |
| New test in isolation | `uv run pytest tests/test_mcp_tools_validation.py::test_all_tool_lists_use_config_dependent_not_requires_config -v` | 1 passed, not skipped |
| Scoped test file | `uv run pytest tests/test_mcp_tools_validation.py -v` | all pass |
| Full regression | `uv run pytest -m "not integration"` (or full `uv run pytest` if time allows) | all pass |
| Coverage | `diff-cover` on changed lines | >= 90% |
| Residual-string check | `grep -rn "requires_config" scripts/ tests/ docs/` | 0 matches |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
