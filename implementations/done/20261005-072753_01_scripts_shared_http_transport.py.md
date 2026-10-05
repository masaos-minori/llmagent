## Goal

Make `HttpTransport.__init__` treat a missing configuration (`cfg=None`) as an explicit, loud error instead of a silent authentication-off switch, so a mis-constructed HTTP MCP transport cannot quietly send unauthenticated calls to an endpoint that requires a bearer token.

## Scope

- Modify `scripts/shared/http_transport.py`: add a fail-loud guard in `HttpTransport.__init__` when `cfg is None` and no usable credential exists; preserve the `cfg`-provided path byte-for-byte.

## Assumptions

- The single production constructor (`ToolTransportInvoker`) always passes `cfg`; confirmed by caller audit.
- Making `cfg=None` loud affects no production path (zero production `cfg=None` constructions).
- The `cfg`-with-empty-token branch remains valid because a `cfg` was explicitly supplied (distinct from missing config).
- No external consumer relies on `cfg=None` (UNK-02 resolution: fail-closed is correct default).

## Design decisions

- Default to **fail-loud (raise)** rather than adding an explicit opt-out flag. An opt-out flag would widen the public interface and escalate this Plan to Path B; it is documented as a deferred follow-up since no production consumer needs an unauthenticated transport.
- Raise a `ValueError` (not a custom exception) — the condition is a programming error (missing required config), not a runtime failure.

## Alternatives considered

- Add an explicit `authenticated=True` constructor parameter: rejected because it widens the public API and escalates to Path B; no production consumer needs an unauthenticated transport.
- Return a sentinel object instead of raising: rejected because it preserves the fail-open pattern and shifts the burden to callers to check for a sentinel.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
In `HttpTransport.__init__`, after resolving whether a usable credential exists, raise when the transport is built without one (`cfg is None` and no provided token), instead of assigning `""`. Preserve the happy path where `cfg` is provided (including the existing `cfg` with an empty-token branch, which is an explicit config choice, not a missing-config case).

### Method
1. In `HttpTransport.__init__` (line ~51): replace the conditional assignment `self._auth_token: str = cfg.auth_token if cfg is not None else ""` with a guard that raises when `cfg is None` and no token is available.
2. Keep the `register_secret` call unchanged for the non-empty token path.

### Details
**Change — `HttpTransport.__init__` (lines 43–51):**

Before:
```python
self._auth_token: str = cfg.auth_token if cfg is not None else ""
if self._auth_token:
    register_secret(self._auth_token)
```

After:
```python
if cfg is None:
    raise ValueError(
        "HttpTransport requires a non-None 'cfg' argument; "
        "a transport without credentials silently disables auth"
    )
self._auth_token: str = cfg.auth_token
if self._auth_token:
    register_secret(self._auth_token)
```

## Compatibility considerations

- The `__init__` signature is unchanged — only its internal guard changes. Callers that currently pass `cfg=None` will now receive a `ValueError` instead of silently succeeding.
- Production callers are unaffected (they always pass `cfg`).
- Test fixtures must be updated to carry explicit configuration.

## Security considerations

- This change eliminates a fail-open footgun: a mis-constructed transport can no longer silently bypass authentication.
- Raising `ValueError` ensures the error propagates immediately at construction time, before any request is made.

## Rollback considerations

- Revert the guard addition in `__init__` to restore the original behavior.
- If a test depends on the silent-off behavior, revert only that test adjustment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/http_transport.py | Static: format, lint, type, security | `uv run ruff format` / `ruff check` / `uv run mypy` / `uv run bandit` on the file | Clean; no new errors or high/medium findings |
| tests/shared/test_tool_executor.py | Unit (behavior lock + cfg additions) | `uv run pytest tests/shared/test_tool_executor.py -v` | Passes before and after; new fail-loud case present |
| tests/shared/test_tool_executor_routing.py | Unit (behavior lock + rewrite) | `uv run pytest tests/shared/test_tool_executor_routing.py -v` | Passes; rewritten fail-loud case passes |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- [ ] `HttpTransport.__init__` raises `ValueError` when constructed with `cfg=None` and no usable credential.
- [ ] A `cfg`-provided transport with a non-empty token sends the `Authorization: Bearer` header identically to before.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.
- [ ] `mypy` passes on the modified file.
- [ ] `bandit` reports no new high/medium findings on the modified file.
- [ ] All affected integration tests pass.

## Out of scope

- Changing `call()`, retry/backoff, response parsing, or session-id injection.
- Altering how `ToolTransportInvoker` builds transports (it already passes `cfg`).
- Adding new env/loader variables or touching any other module's auth policy.
- Adding an explicit opt-out flag for deliberately unauthenticated transports (deferred follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20261004-065813_mcp004_httptransport-silently-sends-unauthenticated-calls-when-constructed-with-cfg-none.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-094856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-072753
- **Related target files**: scripts/shared/http_transport.py