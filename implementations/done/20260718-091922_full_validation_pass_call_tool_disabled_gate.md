# Implementation: full validation pass — /v1/call_tool disabled-tool gate + validate_args feature

Source plan: `plans/20260717-174848_plan.md` ("Reject disabled tools before dispatch in
/v1/call_tool and clarify validation policy"), Implementation steps 6-7.

Note on disambiguation: multiple other `*full_validation_pass*` docs already exist in
`implementations/` (e.g. `20260717-202631_full_validation_pass.md`,
`20260718-032349_full_validation_pass.md`,
`20260718-033059_full_validation_pass_mcp_tools_diagnostics.md`,
`20260718-084253_full_validation_pass_mcp_schema_version.md`,
`20260718-090322_full_validation_pass_config_dependent_rename.md`,
`20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md`). Their Goal
lines were checked: each names a different feature. In particular,
`20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md` is the closest
by topic (same requirement batch, same servers) but its Goal is explicitly scoped to
requirement 15's `GET /v1/tools` metadata feature and its own Scope names the 6
files/docs for THAT plan (`plans/20260717-174024_plan.md`) — it does not cover this
plan's `/v1/call_tool` disabled-gate + `validate_args()` feature. This doc is deliberately
named with the feature slug `call_tool_disabled_gate` to stay unambiguous from all of
them, per this batch's disambiguation convention for the generic `full_validation_pass`
slug.

## Goal

Run the repo's standard validation sequence (`rules/toolchain.md`), scoped to the changes
made across the 6 files touched by this plan (`scripts/mcp_servers/file/read_server.py`,
`write_server.py`, `delete_server.py`, `scripts/mcp_servers/git/server.py`,
`scripts/mcp_servers/file/common.py` if not already covered by requirement 15's landing,
and the new `tests/test_call_tool_validation.py`), then run a targeted grep sweep to
confirm the `"Tool disabled:"` response string appears only at the four intended
`call_tool()` call sites. This corresponds to the plan's Implementation steps 6 ("Run the
Validation plan") and 7 (residual grep check) — both cross-cutting, file-set-wide steps
with no single target source file, combined into one procedure doc per this batch's
convention for non-file-mapped plan steps.

## Scope

**In scope**: full local validation sequence + a single confirmatory grep, run only after
all companion implementation docs for this plan have been applied:
`20260718-091639_read_server_call_tool.py.md`,
`20260718-091715_write_server_call_tool.py.md`,
`20260718-091735_delete_server_call_tool.py.md`,
`20260718-091755_git_server_call_tool.py.md`,
`20260718-091834_test_call_tool_validation.py.md`, plus (if not already landed by the
sibling requirement 15 plan) `20260718-090551_common.py.md` for the shared
`availability_flags()` helper.

**Out of scope**: implementing any of the above changes (this doc is validation-only,
per this workflow being documents-only); shell/cicd/github/rag_pipeline/mdq/web_search
servers (explicitly out of scope per the plan's own Scope section); the sibling
requirement 15 plan's own validation (covered separately by
`20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md`), which this doc
does not supersede or duplicate — the two validation passes are independent and may be
run in either order once each plan's own file changes are applied.

## Assumptions

- All target files' changes (from the companion implementation docs listed in Scope)
  have already been applied to the working tree before this validation procedure is run.
- Standard validation commands and order come from `rules/toolchain.md` (ruff
  format/check, mypy, lint-imports, ast-grep, bandit, pytest, diff-cover, pre-commit) —
  same sequence the plan's own "Validation plan" table specifies.
- `PYTHONPATH=scripts` is required for `lint-imports` per repo convention and the plan's
  own Validation plan table.
- If requirement 15's plan (`plans/20260717-174024_plan.md`) lands `availability_flags()`
  in `common.py` before this plan's changes are applied, that file's change is already
  covered by requirement 15's own validation doc; this doc's file list then narrows to
  the 5 files that are exclusively this plan's (excluding `common.py`).

## Implementation

### Target file

None (cross-cutting; no single source file). Scope is the files listed above under
Scope.

### Procedure

1. Format: `uv run ruff format scripts/mcp_servers/file/read_server.py
   scripts/mcp_servers/file/write_server.py scripts/mcp_servers/file/delete_server.py
   scripts/mcp_servers/git/server.py scripts/mcp_servers/file/common.py
   tests/test_call_tool_validation.py` — expect clean/no diff after first run.
2. Lint: `uv run ruff check scripts/ tests/` — expect 0 errors repo-wide (broad scope
   catches import-order issues from the new `availability_flags`/`GIT_WRITE_TOOLS`
   imports, matching the plan's own Validation plan table).
3. Type check: `uv run mypy scripts/mcp_servers/` — expect no new errors; new branches
   return `CallToolResponse` (unchanged type) in all paths.
4. Architecture: `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations;
   `mcp_servers -> shared` for `GIT_WRITE_TOOLS` in `git/server.py` is an already-allowed
   edge per `.importlinter`.
5. Static analysis: run the repo's ast-grep no-bare-except check per `rules/toolchain.md`
   — expect clean; the new `except ValueError` clauses are specific, not bare.
6. Security: `uv run bandit -r scripts/mcp_servers/` — expect no new HIGH findings.
7. Tests: `uv run pytest tests/test_call_tool_validation.py tests/test_mcp_tool_validators.py -v`
   — expect all pass, including every new disabled/validate_args/spy test.
8. Full regression: `uv run pytest -m "not integration"` (fast path), then
   `uv run pytest` (full, including `@pytest.mark.integration` subprocess tests for all
   MCP servers) — expect all pass.
9. Coverage: run `diff-cover` against the diff covering the 6 changed/added files —
   expect >= 90%; every new branch (disabled gate, validate_args try/except, dispatch
   pass-through) must be hit by at least one test from step 7/8.
10. Pre-commit: `uv run pre-commit run --all-files` — expect pass.
11. Residual grep sweep (plan step 7):
    `grep -rn "Tool disabled:" scripts/mcp_servers/` — expect exactly 4 hits, one each
    in `read_server.py`, `write_server.py`, `delete_server.py`, `git/server.py`'s
    `call_tool()` handlers. Any hit outside these 4 files/handlers is unexpected and must
    be investigated before considering this plan complete.
12. Secondary residual grep: `grep -rn "def availability_flags\|def _git_tool_availability"
    scripts/mcp_servers/` — expect exactly one definition of each (guards against the
    duplicate/diverging-logic risk called out in the plan's Risks table, in case both
    this plan and the sibling requirement 15 plan were implemented without checking for
    each other's work first).

### Method

Shell command sequence (not production code — these are validation/CI invocations, run
as-is from the repo root):

```
uv run ruff format scripts/mcp_servers/file/read_server.py scripts/mcp_servers/file/write_server.py \
  scripts/mcp_servers/file/delete_server.py scripts/mcp_servers/git/server.py \
  scripts/mcp_servers/file/common.py tests/test_call_tool_validation.py
uv run ruff check scripts/ tests/
uv run mypy scripts/mcp_servers/
PYTHONPATH=scripts uv run lint-imports
uv run bandit -r scripts/mcp_servers/
uv run pytest tests/test_call_tool_validation.py tests/test_mcp_tool_validators.py -v
uv run pytest -m "not integration"
uv run pytest
uv run pre-commit run --all-files
grep -rn "Tool disabled:" scripts/mcp_servers/
grep -rn "def availability_flags\|def _git_tool_availability" scripts/mcp_servers/
```

### Details

- Run this doc's procedure only after all companion file-level docs for this plan are
  applied — running it earlier will show expected failures (missing disabled-gate
  behavior) that are not real regressions.
- If the grep sweeps (steps 11-12) surface an unexpected hit, do not silently ignore it —
  trace it back to which companion doc introduced it and correct that file before
  re-running the full sequence.
- This doc is independent of, and does not replace,
  `20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md` (requirement
  15's own validation doc) — both may need to run if both plans land in the same working
  tree, but neither supersedes the other since they validate different features on
  overlapping files.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/ tests/` | clean |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Static analysis | ast-grep no-bare-except check | clean |
| Security | `uv run bandit -r scripts/mcp_servers/` | no new HIGH findings |
| Tests (scoped) | `uv run pytest tests/test_call_tool_validation.py tests/test_mcp_tool_validators.py -v` | all pass |
| Tests (full) | `uv run pytest -m "not integration"` then `uv run pytest` | all pass |
| Coverage | `diff-cover` on changed lines | >= 90% |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Residual grep (response string) | `grep -rn "Tool disabled:" scripts/mcp_servers/` | exactly 4 call sites |
| Residual grep (helper definitions) | `grep -rn "def availability_flags\|def _git_tool_availability" scripts/mcp_servers/` | exactly one definition each |
