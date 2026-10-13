## Goal

Drop the loopback-health switch from the agent health-poll tests in
`tests/agent/test_http_lifecycle_health_check.py`, keeping the matching-token success case
and ensuring a different-token failure is covered (`REQ-003`; AC-3).

## Scope

Only `tests/agent/test_http_lifecycle_health_check.py`. The `TestHealthPollClientLifecycle`
class (AsyncClient lifecycle) is unrelated to the admission and stays unchanged.

## Assumptions

- With the admission removed, every server's middleware uses the strict default call shape,
  so the poll tests no longer need a switch to model "admitted vs. guarded".
- A server guarded by a token other than the cfg's token makes `/health` return 401, so the
  poll fails — this is exactly the different-token failure the plan wants retained.

## Design decisions

- `_loopback_health_app` loses its `exempt_health_on_loopback` switch and builds the app
  with the default strict call shape.
- Delete the switch-on success test (its premise no longer exists); rename the remaining
  two tests to drop the "switch" wording while keeping their behavior.

## Alternatives considered

N/A: a test-only refactor confined to one file; no design family applies.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_health_check.py`

### Procedure

1. Rewrite `_loopback_health_app` (current lines 212-235): remove the
   `*, exempt_health_on_loopback: bool` parameter and the `extra = {...}` block; call
   `attach_auth_middleware(app, server_token)` with the default shape.
2. Delete `test_poll_succeeds_when_switch_on_and_tokens_differ` (current lines 256-278).
3. Rename `test_poll_fails_when_switch_off_and_tokens_differ` (lines 281-309) to
   `test_poll_fails_when_token_differs` and change its helper call (line 287) from
   `_loopback_health_app("browser-secret", exempt_health_on_loopback=False)` to
   `_loopback_health_app("browser-secret")`.
4. Rename `test_poll_succeeds_when_tokens_match_and_switch_off` (lines 312-331) to
   `test_poll_succeeds_when_tokens_match` and change its helper call (line 317) from
   `_loopback_health_app("main-secret", exempt_health_on_loopback=False)` to
   `_loopback_health_app("main-secret")`.

### Method

Apply the four edits, run the file, and confirm no `exempt_health_on_loopback` remains.

### Details

- The remaining two tests drive the real middleware through an in-process ASGI transport
  (`_asgi_client_factory`, lines 238-249). With the switch gone both use the strict call
  shape identical to every other server.
- The different-token test polls a server guarded by `browser-secret` while the cfg sends
  `main-secret`, so `/health` returns 401 and the poll raises `HttpStartupError` — matching
  AC-3.
- The module docstring's `REQ-002` / `REQ-003` references describe AsyncClient lifecycle and
  are unrelated to the admission; leave them.

## Compatibility considerations

Renamed methods are private to this file; ensure nothing outside it references the old
names.

## Security considerations

Test-only; preserves coverage that the startup poll authenticates with the correct token and
fails against a mismatched one.

## Rollback considerations

Revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q` — matching-token poll
  succeeds, different-token poll fails, existing poll/liveness tests pass unchanged (AC-3).
- `rg -n "exempt_health_on_loopback|_is_loopback_client" scripts tests docs` — no matches.
- Full sequence per `rules/toolchain.md`.

## Completion criteria

No `exempt_health_on_loopback` remains in the file; the matching-token poll succeeds and the
different-token poll fails with the startup error.

## Out of scope

The middleware definition (`scripts/mcp_servers/server.py`), the web-search tests
(`tests/mcp_servers/web_search/test_web_search_health.py`), and the two documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the switch from the agent poll tests and add the different-token failure test | Completed | — | 20261013-175629 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261013-175629 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261013-175629 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261013-175629 |  |

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
- **Requirement ID**: `REQ-003` (poll succeeds with the matching token, fails with a different one)
- **Source issue**: issues/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-185654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-185934
- **Related target files**: tests/agent/test_http_lifecycle_health_check.py