# MCP empty-token refusal is split between a shared helper and six inline copies, and the base middleware still fails open

## Priority
Medium

## Summary
Refusing to start an MCP server with an empty `auth_token` is implemented two ways: four servers call `require_auth_token()` from `mcp_servers.server`, and six servers carry a hand-copied module-level `if not token: raise RuntimeError(...)`. `attach_auth_middleware()` itself still accepts every request when given an empty token. Consolidate the rule into one enforcement point so a new or edited server cannot silently omit it.

## Background
Archived issue `issues/done/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md` asked to apply one fail-closed rule to all ten servers and said to "prefer a single shared check (in `attach_auth_middleware` or the posture flow) over four more copies of the import-time `RuntimeError`". Its recorded Plan decision kept the posture check at WARNING and enforced by import-time refusal.

Current source (reviewed head `59dbae624`, evidence label: `Explicit in code`):

- `require_auth_token()` in `scripts/mcp_servers/server.py` is used by `git_server.py`, `cicd_server.py`, `rag_pipeline_server.py`, and `web_search_server.py`.
- `shell_server.py`, `github_server.py`, `mdq_server.py`, `file/read_server.py`, `file/write_server.py`, and `file/delete_server.py` each contain their own inline `if not ...auth_token: raise RuntimeError(...)` followed by `attach_auth_middleware(...)`. The message text is written separately in each file, and `mdq_server.py` reads the token through its own `_load_auth_token()`.
- `attach_auth_middleware()` returns `True` from `_is_authorized` when the token is empty, and its docstring states this accept-all fallback exists only for standalone testability and relies on Agent startup validation.
- Tests: `tests/mcp_servers/test_require_auth_token.py` covers the helper and the four servers; the inline copies are covered per server (`tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/mdq/test_mdq_authentication.py`, and others). No test or checker asserts that every server module routes its token through one enforcement point (evidence label: `Strongly implied by code`, from the search for `require_auth_token` and `auth_token is empty` in `tests/`).

## Problem
The intent of the archived issue (one shared check, so a new server cannot forget it) is only partly met. A future eleventh server, or an edit that removes an inline guard, would start accepting unauthenticated requests without any failing test, because the middleware default is accept-all and enforcement is a per-file convention. The six inline guards also drift independently (message wording, environment variable name text, and the token source).

## Reason for Change
Authentication on loopback servers is the defense against other local processes. The current arrangement keeps today's ten servers safe but depends on each author remembering a local pattern. No incident is reported; this is a hardening and maintainability change, so it is Medium rather than High.

## Implementation Intent
Provide one enforcement point that every server uses, either by making the helper the only way servers attach the middleware or by adding a structural check or test that every `*_server.py` module routes its token through it. Keep the import-time refusal behavior and the Plan decision to keep the posture check at WARNING unless the plan explicitly revisits it. Preserve an explicit, test-only way to attach the middleware without a token.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`require_auth_token`, `attach_auth_middleware`)
- `scripts/mcp_servers/shell/shell_server.py`, `github/github_server.py`, `mdq/mdq_server.py`, `file/read_server.py`, `file/write_server.py`, `file/delete_server.py`
- `tests/mcp_servers/test_require_auth_token.py` and the per-server auth tests

## Required Changes
- Route the six inline guards through the shared enforcement point, keeping each server's variable name in the error message and never echoing the token.
- Add a test or checker that fails when a `*_server.py` module attaches the middleware without going through the enforcement point, so a new server is covered.
- Decide whether `attach_auth_middleware()` should keep accepting an empty token by default; if it does, make the test-only intent explicit in the API (for example an explicit opt-in argument) rather than in a docstring only.

## Constraints
- Importing server modules in tests must remain possible without real secrets, as in the current tests.
- Do not change the Bearer comparison (`hmac.compare_digest`) or the `X-Request-Id` behavior.
- Do not log or echo token values.
- Keep the startup behavior identical for all ten servers: an empty token prevents the module from importing.

## Acceptance Criteria
- All ten servers obtain their middleware token through one shared enforcement point, verified by a test or checker that scans the server modules.
- Adding a server module that calls `attach_auth_middleware` with an unvalidated token fails that test or checker.
- For each of the ten servers, importing the module with an empty token still raises `RuntimeError` naming the server and the environment variable.
- Existing auth tests pass, or are updated only where they relied on the accept-all default.

## Testing Expectations
- Parametrized test over all ten server modules for the empty-token refusal and for the use of the shared enforcement point.
- Run `uv run pytest tests/mcp_servers`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, and `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Update the MCP authentication documentation only if it names the per-server guard or the accept-all fallback as a supported behavior. State the boundary and failure behavior, not implementation details. Run the `docs/` checkers from `routing.md` for any edited doc.

## Out of Scope
- Changing the posture severity of the empty-token check (kept at WARNING by the earlier Plan decision).
- Agent-side startup validation in `scripts/agent/startup_validation.py`.
- Token sourcing, rotation, or storage.

## Dependencies
- Follow-up to `issues/done/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md` (archived; the shared-check preference is only partly implemented, so re-verify against current source when planning).
- Sibling check: no open issue under `issues/` and no in-flight plan under `plans/` targets `scripts/mcp_servers/server.py` or the six server modules for this concern. `issues/20261107-132004_mcpstartup001_python-m-double-execution.md` also edits `scripts/mcp_servers/server.py`; no required order, but plan them together to avoid conflicting edits.

## Unresolved Questions
- `不明`: whether the owner wants `attach_auth_middleware()` to keep the accept-all default for tests, or an explicit opt-in.
- `Needs confirmation`: whether `mdq_server.py`'s separate token loading must stay separate for a reason not visible in the code.

## AI Implementation Instruction
Keep the change minimal: consolidate the guard and add the enforcement test. Do not change authentication semantics, the header comparison, or the posture severity. Do not touch Agent-side validation. Stop and report if consolidation requires changing the import-time refusal behavior.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-132052
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `tests/mcp_servers/test_require_auth_token.py`
