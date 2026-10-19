## Goal
Make `test_github_tools_in_tools_definitions` follow the GitHub MCP server's `startup_mode`: all registry tools must be defined when the server is enabled and none when it is disabled, backed by a pure helper with parametrized tests (`REQ-001`, `REQ-002`), without changing the other tests (`REQ-003`).

## Scope
- The module's imports, one new helper, one new test class, and the body and docstring of `test_github_tools_in_tools_definitions`.
- `test_github_mcp_server_exists`, `test_github_tool_names_match_tools_definitions`, `test_github_tool_names_match_tool_list`, `test_tool_names_not_required_for_routing`, and `_parse_mcp_server_tool_names` stay untouched.

## Assumptions
- `startup_mode == "none"` means disabled (`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`); any other value, or a missing `[mcp_servers.github]` table, is treated as enabled.
- `config/agent.toml` parses with `tomllib` (verified on 2026-10-19: 42 tool definitions, none for GitHub, `startup_mode = "none"`), and `get_registry().get_tool_names("github")` returns 21 names.

## Design decisions
- Put the decision in a pure helper that returns problem strings, so tests can feed it synthetic configurations and the enabled-case rule stays verified while the real config is disabled.
- Read the real config with `tomllib` instead of scanning lines for `"github_` and `name`, which could also match `tool_names` entries.

## Alternatives considered
A plain skip when the server is disabled was rejected: it would stop checking anything, and re-enabling the server without restoring definitions would go unnoticed (Plan UNK-01).

## Implementation
### Target file
`tests/docs/test_github_config_consistency.py`

### Procedure
1. Add `import tomllib`, `from typing import Any`, and `import pytest` to the imports.
2. Add `TestGitHubDefinitionProblems` (new) with a parametrized test `test_problems_by_state` (new) over four cases using a synthetic `cfg` and registry set {`github_a` (new), `github_b` (new)}: enabled with both defined (no problems), enabled with `github_b` (new) missing (one problem naming it), disabled with none defined (no problems), disabled with `github_a` (new) defined (one problem naming it). Run it and confirm it fails because the helper does not exist.
3. Add the module-level helper `_github_definition_problems` (new) `(cfg: dict[str, Any], registry_tools: Iterable[str]) -> list[str]`.
4. Rewrite `test_github_tools_in_tools_definitions`: keep the `len(github_tools) == 21` assertion, load `config/agent.toml` with `tomllib` in binary mode, call the helper, and assert it returns no problems with the problems joined in the message; update the docstring to describe both states and why.

### Method
- Helper logic: `enabled = cfg.get("mcp_servers", {}).get("github", {}).get("startup_mode") != "none"`; `defined = {entry.get("function", {}).get("name") for entry in cfg.get("tool_definitions", [])}`; `github_defined = {n for n in defined if isinstance(n, str) and n.startswith("github_")}`.
- Enabled: if `set(registry_tools) - defined` is non-empty, return one problem listing the sorted missing names and saying the server is enabled. Disabled: if `github_defined` (new) is non-empty, return one problem listing them and saying the server is disabled (`startup_mode="none"`) so definitions must be absent.
- Build the synthetic configs inline in the parametrization (small dicts), not from files.

### Details
- Keep `from __future__ import annotations` first; import `Iterable` from `collections.abc` for the helper's type.
- Expected before the helper: the new test errors with a name error; the rewritten test is not applied until step 4.
- Do not read or write anything under `/opt/llm`; the real config is read from the repository path `config/agent.toml`.

## Compatibility considerations
N/A: test-only change; the other tests in the file keep their behavior.

## Security considerations
N/A: tests only; no production path is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/docs/test_github_config_consistency.py -q`
- `uv run ruff format tests/docs/test_github_config_consistency.py && uv run ruff check tests/docs/test_github_config_consistency.py`
- `uv run mypy tests/docs/test_github_config_consistency.py`
- `uv run python tools/check_suppression_justification.py` and `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The helper tests pass for all four cases, `test_github_tools_in_tools_definitions` passes on the current tree, and the file's other tests pass unchanged.

## Out of scope
- Changing `config/agent.toml` or restoring the removed definitions
- Re-enabling the GitHub server
- Any other test or document

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the parametrized helper tests and confirm they fail | Completed | 20261019-151040 | 20261019-151040 | before the helper: 4 new cases failed with NameError; after: 9 passed in the file; real config disabled -> no problems, same config enabled -> 1 problem |
| 2 | Add the helper and rewrite the failing test | Completed | 20261019-151040 | 20261019-151040 |  |
| 3 | Run the file's tests and the validation sequence (`rules/toolchain.md`) for it | Completed | 20261019-151040 | 20261019-151040 | tests/docs 20 passed; production snapshot identical; the full suite was not rerun (test-only change confined to this file) |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (startup_mode-aware check, helper, unchanged siblings)
- **Source issue**: issues/20261019-143959_testfix001_github-tool-definitions-test-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-144702_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-150230
- **Related target files**: tests/docs/test_github_config_consistency.py