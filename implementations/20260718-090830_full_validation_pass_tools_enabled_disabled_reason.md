# Implementation: full validation pass — /v1/tools enabled/disabled_reason feature

Source plan: `plans/20260717-174024_plan.md` ("Add runtime availability metadata
(enabled / disabled_reason) to /v1/tools"), Implementation steps 6-7.

Note on disambiguation: five other `*full_validation_pass*` docs already exist in
`implementations/` (`20260717-202631_full_validation_pass.md`,
`20260718-032349_full_validation_pass.md`,
`20260718-033059_full_validation_pass_mcp_tools_diagnostics.md`,
`20260718-084253_full_validation_pass_mcp_schema_version.md`,
`20260718-090322_full_validation_pass_config_dependent_rename.md`). Their Goal lines were
checked: each names a different feature (plugin-registry removal, mcp-tool-discovery
diagnostics, mcp schema-version rollout, and the sibling `config_dependent` rename
respectively) — none covers this plan's `enabled`/`disabled_reason` metadata feature. This
doc is deliberately named with the feature slug
(`tools_enabled_disabled_reason`) to stay unambiguous from all of them.

## Goal

Run the repo's standard validation sequence (`rules/toolchain.md`), scoped to the changes
made across the 6 files touched by this plan
(`scripts/mcp_servers/file/common.py`, `read_server.py`, `write_server.py`,
`delete_server.py`, `scripts/mcp_servers/git/server.py`,
`tests/test_mcp_tools_validation.py`), then run a targeted grep sweep to confirm the new
`enabled`/`disabled_reason` fields appear only in the intended locations. This corresponds
to the plan's Implementation steps 6 ("Run the Validation plan") and 7 (residual grep
check) — both are cross-cutting, file-set-wide steps with no single target source file, so
they are combined into one procedure doc per this batch's convention for non-file-mapped
plan steps.

## Scope

**In scope**: full local validation sequence + a single confirmatory grep, run only after
all 5 file-implementation docs for this plan
(`20260718-090551_common.py.md`, `20260718-090617_read_server.py.md`,
`20260718-090638_write_server.py.md`, `20260718-090653_delete_server.py.md`,
`20260718-090710_git_server.py.md`, `20260718-090741_test_mcp_tools_validation.py.md`)
have been applied.

**Out of scope**: implementing any of the above changes (this doc is validation-only, per
this workflow being documents-only); shell/cicd servers (explicitly out of scope per the
plan's Scope section); the sibling `config_dependent` rename plan's own validation
(covered separately by `20260718-090322_full_validation_pass_config_dependent_rename.md`).

## Assumptions

- All 6 target files' changes (from the 6 companion implementation docs) have already
  been applied to the working tree before this validation procedure is run.
- Standard validation commands and order come from `rules/toolchain.md` (ruff
  format/check, mypy, lint-imports, ast-grep, bandit, pytest, diff-cover, pre-commit) —
  same sequence the plan's own "Validation plan" table specifies, scoped here to the
  files this plan touches plus a repo-wide grep for safety (since `enabled`/
  `disabled_reason` are generic-sounding key names that could collide with unrelated code
  if a mistake were made).
- `PYTHONPATH=scripts` is required for `lint-imports` per the plan's own Validation plan
  table and existing repo convention.

## Implementation

### Target file

None (cross-cutting; no single source file). Scope is the 6 files listed above under
Scope.

### Procedure

1. Format: `uv run ruff format scripts/mcp_servers/file/common.py
   scripts/mcp_servers/file/read_server.py scripts/mcp_servers/file/write_server.py
   scripts/mcp_servers/file/delete_server.py scripts/mcp_servers/git/server.py
   tests/test_mcp_tools_validation.py` — expect clean/no diff after first run.
2. Lint: `uv run ruff check scripts/ tests/` — expect 0 errors repo-wide (broad scope
   matches the plan's own Validation plan table, since a narrow per-file lint could miss
   import-order issues introduced by the new `availability_flags`/`GIT_WRITE_TOOLS`
   imports).
3. Type check: `uv run mypy scripts/` — expect no new errors; the new fields are
   `bool`/`str`, compatible with existing `dict[str, Any]` (file servers) and
   `dict[str, object]` (git server) return-type annotations.
4. Architecture: `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations;
   `mcp_servers -> shared` for the new `GIT_WRITE_TOOLS` import in `git/server.py` is an
   already-allowed edge per `.importlinter` (`mcp_servers → db, shared`).
5. Static analysis: run the repo's ast-grep no-bare-except check per `rules/toolchain.md`
   — expect clean; no new exception handling was introduced by this feature (all new
   logic is pure boolean/membership checks).
6. Security: `uv run bandit -r scripts/` — expect no new HIGH findings.
7. Tests: `uv run pytest tests/test_mcp_tools_validation.py -v` — expect all pass,
   including every new `enabled`/`disabled_reason` test added per
   `20260718-090741_test_mcp_tools_validation.py.md`.
8. Full regression: `uv run pytest -m "not integration"` (fast path), then
   `uv run pytest` (full, including the `@pytest.mark.integration` subprocess tests for
   all MCP servers) — expect all pass.
9. Coverage: run `diff-cover` against the diff covering the 6 changed files — expect
   >= 90%; the new branches (git server's 3-way precedence `if`/`elif`/`else`, each file
   server's 2-way `availability_flags` branches) must each be hit by at least one new
   test case from step 7/8.
10. Pre-commit: `uv run pre-commit run --all-files` — expect pass.
11. Residual grep sweep (plan step 7):
    `grep -rn '"enabled"\|disabled_reason' scripts/mcp_servers/` — expect matches ONLY in:
    - `scripts/mcp_servers/file/common.py` (the new `availability_flags` helper)
    - `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py`
      (their `list_tools()` handlers)
    - `scripts/mcp_servers/git/server.py` (its `list_tools()` handler)
    Any hit outside these 5 files is unexpected and must be investigated before
    considering this plan complete (e.g. it would indicate an accidental leak into
    `TOOL_LIST`/`tools.py` static definitions, which the plan's Design section explicitly
    says must NOT happen).

### Method

Shell command sequence (not production code — these are validation/CI invocations, run
as-is from the repo root):

```
uv run ruff format scripts/mcp_servers/file/common.py scripts/mcp_servers/file/read_server.py \
  scripts/mcp_servers/file/write_server.py scripts/mcp_servers/file/delete_server.py \
  scripts/mcp_servers/git/server.py tests/test_mcp_tools_validation.py
uv run ruff check scripts/ tests/
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run bandit -r scripts/
uv run pytest tests/test_mcp_tools_validation.py -v
uv run pytest -m "not integration"
uv run pytest
uv run pre-commit run --all-files
grep -rn '"enabled"\|disabled_reason' scripts/mcp_servers/
```

### Details

- Run this doc's procedure only after all 6 file-level docs for this plan are applied —
  running it earlier will show expected failures (missing `enabled`/`disabled_reason`
  keys) that are not real regressions.
- If the grep sweep (step 11) surfaces an unexpected hit, do not silently ignore it —
  trace it back to which of the 6 companion docs introduced it and correct that file
  before re-running the full sequence.
- This doc supersedes ad-hoc reliance on any of the five pre-existing
  `*full_validation_pass*` docs for this plan's sign-off, per the batch-wide
  disambiguation rule (each covers a different, non-overlapping feature).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/ tests/` | clean |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Static analysis | ast-grep no-bare-except check | clean |
| Security | `uv run bandit -r scripts/` | no new HIGH findings |
| Tests (scoped) | `uv run pytest tests/test_mcp_tools_validation.py -v` | all pass |
| Tests (full) | `uv run pytest -m "not integration"` then `uv run pytest` | all pass |
| Coverage | `diff-cover` on changed lines | >= 90% |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Residual grep | `grep -rn '"enabled"\|disabled_reason' scripts/mcp_servers/` | hits only in the 5 intended files listed in Procedure step 11 |
