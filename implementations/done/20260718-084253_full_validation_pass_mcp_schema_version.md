# Implementation procedure: full validation pass — MCP tool schema_version + validation tests

Source plan: `plans/20260717-131019_plan.md` ("Add MCP tool schema versioning and validation tests"),
Implementation step 5.

This doc is intentionally scoped to *this plan only*, per the batch-wide convention (see other plans'
implementation docs, e.g. `implementations/20260718-033059_full_validation_pass_mcp_tools_diagnostics.md`)
that the generic `full_validation_pass` slug has been reused by multiple unrelated plans in this batch and
is not interchangeable across them. Checked existing candidates before writing this doc:
- `implementations/20260717-202631_full_validation_pass.md` — Goal is about the plugin-registry removal
  requirement; unrelated.
- `implementations/20260718-032349_full_validation_pass.md` — Goal is about a docstring/comment-only
  documentation requirement; unrelated.
- `implementations/20260718-033059_full_validation_pass_mcp_tools_diagnostics.md` — Goal is about the
  `/mcp tools` diagnostic subcommand (`cmd_mcp.py`); a different MCP-related requirement, not this one.
None of the three genuinely cover this plan's feature (MCP `/v1/tools` `schema_version` + validation test
matrix) — confirmed by reading each one's Goal line, not just matching on filename. Hence a new, distinctly
named doc.

## Goal

Run the standard validation sequence (`rules/toolchain.md`) scoped to the files touched by this plan's
four implementation docs — `scripts/mcp_servers/server.py`, the 9 individual MCP server files (`mdq`,
`cicd`, `github`, `git`, `web_search`, `shell`, `file/read_server.py`, `file/write_server.py`,
`file/delete_server.py`), `scripts/agent/services/mcp_tool_discovery.py`, and
`tests/test_mcp_tool_discovery.py` — then the full suite, to confirm the new `schema_version` field and
its validation test matrix introduce zero regressions and satisfy the plan's acceptance criteria: every
server's `/v1/tools` response includes `schema_version`; missing `schema_version` is tolerated; every tool
schema is validated with clear server+tool identification on failure.

## Scope

**In scope**
- Scoped ruff/mypy/bandit/lint-imports runs against exactly the files this plan's 4 implementation docs
  touch (listed above).
- The new `tests/test_mcp_tool_discovery.py` test run.
- The full test suite (`uv run pytest -v`) to catch any cross-file regression (e.g. any other test that
  asserts on a `/v1/tools` response's exact keys and would break from the new additive `schema_version`
  key).
- `pre-commit run --all-files`.

**Out of scope**
- Any change to production code — this doc is validation-only, per this workflow's documents-only
  constraint.
- Validating unrelated requirements from other plans in this batch (e.g. `cmd_mcp.py`'s `/mcp tools`
  diagnostic subcommand, RuntimeToolRegistry migration files) — each has (or should have) its own scoped
  validation doc.

## Assumptions

1. This doc is written and can be executed only after all 4 of this plan's implementation docs are
   actually implemented in source: `implementations/20260718-084001_mcp_servers_server.py.md`,
   `implementations/20260718-084035_mcp_server_schema_version_rollout.md`,
   `implementations/20260718-084109_mcp_tool_discovery.py.md`, and
   `implementations/20260718-084145_test_mcp_tool_discovery.py.md`. Since `mcp_tool_discovery.py` does not
   exist in real source yet (confirmed via `ls`), this plan's step 3/4 depend on that file being created
   first, per the base req-03 doc (`implementations/20260717-203830_mcp_tool_discovery.py.md`) and its
   extension (`implementations/20260717-224511_mcp_tool_discovery.py.md`) — those are a prerequisite,
   not part of this plan's own scope, but must land before this plan's step 3 can be validated end-to-end.
2. A search for any existing test that asserts the **exact** key set of a `/v1/tools` response body (e.g.
   `assert response.json() == {"tools": [...]}` with no other keys) should be run before this plan's
   rollout lands, to catch any hidden equality-based assertion that the additive `schema_version` key
   would break — `rg -n 'v1/tools' tests/` (run at implementation time) to enumerate any such call sites
   not already covered by `tests/test_mcp_server_base.py`.

## Implementation

### Target file

N/A — validation-only doc, no single target file. Scope is the set of files listed above.

### Procedure

1. Format and lint the 11 production files (base `server.py` + 9 servers + `mcp_tool_discovery.py`) and
   the 1 new test file.
2. Type-check the same set with mypy.
3. Run `lint-imports` to confirm no import-layer violation (in particular: `mcp_tool_discovery.py`
   importing `agent.repl_health._check_tool_definitions` per the 224511 doc's Assumption 1 stays a legal
   agent-to-agent import; the 9 servers' new import of `build_tools_response` from `mcp_servers.server`
   stays within the `mcp_servers` package, no cross-layer concern).
4. Run bandit against the same production file set.
5. Run `rg -n 'v1/tools' tests/` to check for any pre-existing exact-equality assertion on the response
   body shape (Assumption 2) that the new `schema_version` key might break; fix any such test if found (as
   an acknowledged, in-scope fix, not a scope-creep item — mirrors the plan's own Risk section's guidance
   for real, previously-unnoticed issues surfaced by this change).
6. Run `tests/test_mcp_tool_discovery.py` targeted, then `tests/test_mcp_server_base.py` (regression check
   for the 9 servers' shared base-class behavior), then the full suite.
7. Run `diff-cover` against the changed lines.
8. Run `pre-commit run --all-files`.

### Method

Command-line validation only; no code edits expected unless step 5 surfaces a genuine pre-existing
exact-equality assertion (see Assumption 2), in which case the fix is scoped narrowly to that one
assertion.

### Details

N/A — no production code, this is a checklist execution doc.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format | `uv run ruff format scripts/mcp_servers/ scripts/agent/services/mcp_tool_discovery.py tests/test_mcp_tool_discovery.py` | 0 diffs |
| Lint | `uv run ruff check scripts/mcp_servers/ scripts/agent/services/mcp_tool_discovery.py tests/test_mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/ scripts/agent/services/mcp_tool_discovery.py tests/test_mcp_tool_discovery.py` | 0 errors |
| Import architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| ast-grep constraint sweep | `ast-grep --pattern 'except: $$$' --lang python scripts/mcp_servers/ scripts/agent/services/mcp_tool_discovery.py` | no bare except introduced |
| Security | `uv run bandit -r scripts/mcp_servers/ scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Pre-existing exact-equality check | `rg -n 'v1/tools' tests/` | no broken exact-equality assertion on `/v1/tools` response shape (or fixed if found) |
| Targeted tests | `uv run pytest tests/test_mcp_tool_discovery.py tests/test_mcp_server_base.py -v` | all pass |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | meets project threshold |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
