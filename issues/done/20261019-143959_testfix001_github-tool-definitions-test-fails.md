# test_github_tools_in_tools_definitions fails since the GitHub MCP server was disabled

## Priority
Medium

## Summary
Make `tests/docs/test_github_config_consistency.py::TestGitHubConfigConsistency::test_github_tools_in_tools_definitions` agree with the intentional configuration change that disabled the GitHub MCP server and removed its tool definitions from `config/agent.toml`, so the suite and CI are green again without hiding a real inconsistency.

## Background
- Found on 2026-10-19 as the single remaining failure of the full test suite (9432 passed, 1 failed); it fails on the unchanged tree as well, so it is not caused by recent changes.
- Commit `4e2442a75` (2026-10-18, "fix: disable the github MCP server until GITHUB_TOKEN is provisioned") changed `config/agent.toml` by 2 insertions and 573 deletions: `[mcp_servers.github]` now has `startup_mode = "none"` and `required = false`, and every GitHub `[[tool_definitions]]` block was removed. The server's `tool_names` list remains.
- CI runs the full suite (`uv run pytest -v` in `.github/workflows/ci.yml`), so this test keeps the pipeline red.

## Problem
- The test asserts that all 21 GitHub tools registered in `shared.tool_registry` appear on lines of `config/agent.toml` that contain both `"github_` and `name`. After the commit above, no `[[tool_definitions]]` entry for a GitHub tool exists, so all 21 names are reported missing.
- The other GitHub consistency tests in the same file still pass (they compare the registry and `TOOL_LIST` with `[mcp_servers.github].tool_names`, which was kept).
- Confirmed (Explicit evidence): the test text and its docstring ("All 21 GitHub tools exist in config/agent.toml [tool_definitions]"); `git show 4e2442a75 --stat` and the removed `[tool_definitions.function]` blocks; `config/agent.toml` lines for `[mcp_servers.github]`. No document under `docs/` states that GitHub tool definitions must be present in `agent.toml` (a search found none).

## Reason for Change
- A permanently failing test hides new failures and blocks a green CI run.
- The test encodes a rule ("definitions exist") that is only true while the server is enabled; the configuration change was deliberate, so the test, not the configuration, is stale.

## Implementation Intent
- Keep the consistency check but make it conditional on the server being enabled: when `[mcp_servers.github].startup_mode` is `"none"`, the definitions must be absent from the LLM-facing tool list (no `[[tool_definitions]]` for GitHub tools) or the test skips with an explicit reason; when the server is enabled, the original assertion applies.
- Prefer asserting the consistent state in both modes over a plain skip, so re-enabling the server without restoring the definitions is caught.
- Do not restore the 573 deleted lines: removing them was a deliberate part of disabling the server.

## Target Files or Areas
- `tests/docs/test_github_config_consistency.py`
- `config/agent.toml` (read only; no change expected)
- Documentation: Unknown (the re-enable procedure for the GitHub server, if documented, may need to say that the tool definitions must be restored from history; to confirm)

## Required Changes
- Read `startup_mode` of `[mcp_servers.github]` in the test (through the same file-reading style the test already uses, or the loader).
- Disabled case: assert that no GitHub tool appears in `[[tool_definitions]]` (consistent with the disabled server), instead of requiring all 21.
- Enabled case: keep the existing assertion that all 21 registry tools are defined.
- Update the test docstring to state both cases and why.
- Add a short note where re-enabling the server is described, if such a description exists (see Unresolved Questions).

## Constraints
- Do not change `config/agent.toml` in this issue.
- Do not weaken the other tests in the file.
- Keep the test independent of production state under `/opt/llm`.

## Acceptance Criteria
- The test passes on the current tree and the full suite has no failing test from this file.
- Switching the GitHub server to an enabled `startup_mode` in a temporary config copy makes the test require the definitions again (verified by a local check or a parametrized case).
- No other test in the file changes behavior.

## Testing Expectations
- `uv run pytest tests/docs/test_github_config_consistency.py -q`.
- The `rules/toolchain.md` sequence for the changed test file.
- If a document is edited, the documentation checkers from `routing.md`.

## Documentation Impact
Possibly: a one-line note in the GitHub MCP server's re-enable instructions that `[[tool_definitions]]` for the GitHub tools must be restored (recoverable from the history before `4e2442a75`). Use `N/A` if no such instructions exist.

## Out of Scope
- Re-enabling the GitHub MCP server or provisioning `GITHUB_TOKEN`.
- Restoring the removed tool definitions.
- The flaky mdq test (filed separately as testfix002).

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Related: testfix002 (separate test problem; independent).

## Unresolved Questions
- Whether the owner prefers "assert absent when disabled" or a plain skip for the disabled case (assumption: assert absent, as it keeps the check meaningful).
- Where the GitHub server re-enable procedure is documented, if anywhere (not found in `docs/`; confirm during planning).

## AI Implementation Instruction
- Keep the diff to the one test file unless a re-enable note is clearly needed.
- Do not edit `config/agent.toml` and do not restore deleted definitions.
- Stop and report if the intended behavior for the disabled case is unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-143959
- **Related target files**: `tests/docs/test_github_config_consistency.py`
