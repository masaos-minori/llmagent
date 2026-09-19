# eventbus resolve_principal() unit tests trip the fail-closed auth_token check via a bare MagicMock request

## Priority
Medium

## Summary
`scripts/eventbus/auth.py`'s `resolve_principal()` calls
`get_auth_token(request.app.state.config)` as a fail-closed check before consulting
`_TOKEN_PRINCIPAL_MAP`. `get_auth_token()` asserts `isinstance(token, str)`.
`tests/eventbus/test_eventbus_auth.py::TestPrincipalFieldValidation`'s tests call
`resolve_principal(MagicMock(), credentials=MagicMock(credentials=token))` — passing a
bare `MagicMock()` for `request` — so `request.app.state.config` auto-resolves to a
nested `MagicMock`, and `config.auth_token` is itself a truthy `MagicMock` (not `None`),
so it passes the `if not token` check but fails `assert isinstance(token, str)` with
`AssertionError: Expected str, got MagicMock`. 9 tests in this class fail this way.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` that this
reproduces identically on that commit alone, unrelated to this session's own (Agent/
EventBus reference-table) work rebased on top of it afterward.

## Problem
This is a test-fixture/production-code mismatch, not a production defect:
`resolve_principal()`'s real callers always pass a real `Request` backed by a real
`EventBusConfig` (`request.app.state.config`), so `get_auth_token()` behaves correctly in
production. But `TestPrincipalFieldValidation`'s tests were written to test only the
token-to-`Principal` resolution logic (`_TOKEN_PRINCIPAL_MAP` lookup), using a throwaway
`MagicMock()` for `request` since they never expected `resolve_principal()` to inspect
`request.app.state.config` at all. That assumption broke when the fail-closed
`get_auth_token(config)` check was added to `resolve_principal()`.

## Reason for Change
With 9 of `TestPrincipalFieldValidation`'s tests failing on an unrelated fail-closed check
rather than their actual assertions, this class currently provides no coverage for
`Principal` field resolution (roles/`allowed_consumer_ids`/`allowed_topics` per token
type) — the exact behavior these tests were written to protect (publisher/admin/shared
per-role token grants, described elsewhere in this session's own documentation work on
`docs/06_eventbus_05_configuration-and-operations.md`'s per-role tokens).

## Implementation Intent
Give `TestPrincipalFieldValidation`'s tests a `request` mock whose
`app.state.config.auth_token` resolves to a real string (e.g.
`MagicMock(app=MagicMock(state=MagicMock(config=MagicMock(auth_token="test-token"))))`,
or a small real `EventBusConfig`/lightweight stand-in with `auth_token` set), so the
fail-closed check passes and the tests exercise only the `_TOKEN_PRINCIPAL_MAP` lookup
logic they were written for. Do not weaken or remove `get_auth_token()`'s
`isinstance(token, str)` assertion or `resolve_principal()`'s fail-closed check — those
are production safety behavior, not the source of the bug.

## Target Files or Areas
- `tests/eventbus/test_eventbus_auth.py` (`TestPrincipalFieldValidation`, 9 tests)

## Required Changes
- Update every test in `TestPrincipalFieldValidation` that currently calls
  `resolve_principal(MagicMock(), credentials=...)` to instead supply a `request` mock
  whose `app.state.config.auth_token` is a real, non-empty string.
- Confirm the change does not alter what each test is actually verifying (roles/
  `allowed_consumer_ids`/`allowed_topics` per token).

## Constraints
Do not modify `scripts/eventbus/auth.py`'s production fail-closed logic — this is a
test-only fix.

## Acceptance Criteria
- `uv run pytest tests/eventbus/test_eventbus_auth.py -q` reports 0 failures.
- Each affected test still asserts the same `Principal` field values it did before (roles,
  `allowed_consumer_ids`, `allowed_topics`).

## Testing Expectations
Run `uv run pytest tests/eventbus/test_eventbus_auth.py -q`; also run the full
`uv run pytest tests/ -q` to confirm no new failures are introduced elsewhere.

## Documentation Impact
N/A: test-fixture fix, no behavior or public API change.

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/test_orchestrator.py`, `tests/agent/services/test_config_reload.py`,
`tests/agent/services/test_mcp_tool_discovery.py`,
`tests/mcp_servers/git/test_git_security_compliance.py`) — each is tracked as its own
issue.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the mismatch is directly confirmed by reading `resolve_principal()`/
`get_auth_token()`'s source and the failing tests' fixtures.

## AI Implementation Instruction
Change only the `request` mock construction inside
`tests/eventbus/test_eventbus_auth.py::TestPrincipalFieldValidation`'s 9 failing tests. Do
not touch `scripts/eventbus/auth.py` or any other test class in this file. Keep the diff
minimal — a shared local helper for the corrected mock is acceptable if it avoids
repeating the same construction 9 times.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164247
- **Related target files**: tests/eventbus/test_eventbus_auth.py
