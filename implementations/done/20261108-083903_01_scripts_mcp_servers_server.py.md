## Goal

Make the test-only accept-all intent of `attach_auth_middleware()` in `scripts/mcp_servers/server.py` explicit in its public signature rather than living only in a docstring, so that `require_auth_token()` remains the single production enforcement point every server routes through (`REQ-001`/`REQ-002`/`REQ-003`). Preserve the import-time empty-token `RuntimeError` and the WARNING posture-check severity already decided in the plan.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The plan's open mechanism decision resolves to approach (a): the six inline guards are replaced by calls through `require_auth_token()`, and a structural test asserts every `*_server.py` routes through it (`UNK-01`/`REQ-001`/`REQ-002`).
- `require_auth_token(label, env_var, token)` at `scripts/mcp_servers/server.py` `L137-151` is already the shared enforcement point used by `git`, `cicd`, `rag_pipeline`, and `web_search`; this document does not change its body.
- The implementer decides UNK-01 (whether `attach_auth_middleware()` gains an explicit opt-in argument for the accept-all default). If the explicit-argument route is chosen, tests calling the middleware with an empty token must pass the opt-in explicitly.

## Design decisions
- **Keep `require_auth_token` unchanged as the enforcement point.** It raises `RuntimeError(f"{label}: auth_token is empty; set {env_var} ...")` and returns the token otherwise; the six consolidated servers call it with their own label/env var so messages stay identical to the current inline guards.
- **Make the accept-all intent explicit in the API (UNK-01, recommended).** In `_is_authorized` (`scripts/mcp_servers/server.py` `L116-120`), the `if not token: return True` branch is the test-only fallback. Surface it as an explicit, documented opt-in on `attach_auth_middleware` (for example `accept_all_for_tests: bool = False`) so the default is fail-closed on an empty token and the test-only path is opt-in, not an implicit module-level behavior. Record the UNK-01 choice here.
- **Preserve import-time refusal.** Because all ten servers call `require_auth_token()` before `attach_auth_middleware()`, an empty token never reaches the middleware in production; the import-time `RuntimeError` is unchanged (`REQ-003`).

## Alternatives considered
- **Leave the docstring-only accept-all unchanged.** Rejected — the accept-all remains an implicit default that a future eleventh server could inherit without a failing test (`REQ-001`/`REQ-002`).
- **Remove the accept-all entirely.** Rejected — it exists for the middleware's standalone unit tests; removing it breaks those tests. Prefer an explicit opt-in that keeps the tests working while making the intent visible in the signature.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Confirm `require_auth_token()` (`L137-151`) is the shared enforcement point and leave its body unchanged.
2. Under UNK-01, add an explicit opt-in parameter to `attach_auth_middleware()` controlling the empty-token accept-all branch (`L116-119`); default it to fail-closed so the test-only path is opt-in.
3. Update the docstring of `attach_auth_middleware()` to describe the opt-in argument instead of an implicit default.
4. Update every existing test that relied on the implicit accept-all default to pass the new opt-in explicitly (`REQ-004`).

### Method
Edit only the `attach_auth_middleware()` / `_is_authorized()` region (`L104-135`) and the tests that call the middleware with an empty token; do not touch `require_auth_token()` or the posture-check severity.

### Details
Current `_is_authorized` accept-all branch, `scripts/mcp_servers/server.py` `L116-120`:
```python
    def _is_authorized(request: Request, token: str) -> bool:
        """Return True when no token is required or the Bearer header matches."""
        if not token:
            return True
        presented = request.headers.get("Authorization", "")
        return hmac.compare_digest(
            presented.encode("utf-8"), f"Bearer {token}".encode()
        )
```
Under UNK-01, thread an explicit `accept_all_for_tests: bool = False` through `attach_auth_middleware(...)` into the `_is_authorized` closure and change the branch to `if not token: return accept_all_for_tests`. Keep the docstring's statement that the fallback exists for standalone testability, but now tied to the named opt-in. If UNK-01 instead keeps the implicit default, leave this branch as-is and rely solely on the structural test (`test_require_auth_token.py`) plus the six-server consolidation; record the choice.

## Compatibility considerations
- `require_auth_token()` keeps its signature and return value; callers (`git`, `cicd`, `rag_pipeline`, `web_search`) are unaffected.
- If UNK-01 adds the opt-in, any caller of `attach_auth_middleware()` with an empty token now fails closed by default — all ten production servers pass a non-empty token via `require_auth_token()`, so only direct-test callers are affected (`REQ-004`).

## Security considerations
- Defaulting the accept-all to fail-closed tightens the middleware: an empty token yields `401 Unauthorized` instead of unrestricted access. This is the intended direction and matches the import-time refusal the servers already enforce.

## Rollback considerations
- Revert the commit; the change is confined to `attach_auth_middleware()`/`_is_authorized()` and the handful of tests that called the middleware with an empty token.

## Validation plan
- `uv run pytest tests/mcp_servers/test_require_auth_token.py` — helper + ten-server import refusals pass.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.
- `uv run ruff check scripts/ tests/` — clean.
- Baseline (Step 5): radon `attach_auth_middleware` A(1), `require_auth_token` A(2); `bandit -ll` no high/medium; `lint-imports` 6 kept / 0 broken.

## Completion criteria
- `REQ-001`/`REQ-002`: a structural test in `test_require_auth_token.py` fails when a `*_server.py` module attaches the middleware without routing through `require_auth_token()`.
- `REQ-003`: importing any of the ten servers with an empty token still raises `RuntimeError` naming the server and environment variable.
- `REQ-004`: existing auth tests pass, or are updated only where they relied on the implicit accept-all default.

## Out of Scope
- Changing which servers exist or adding an eleventh server.
- Changing authentication semantics, the `hmac.compare_digest` comparison, or the posture-check severity (kept at WARNING by the Plan).
- Token sourcing, rotation, or storage; Agent-side startup validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-170747 | 20261108-170747 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261108-170747 | 20261108-170747 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-170747 | 20261108-170747 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261108-170747 | 20261108-170747 | — |

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
- **Requirement ID**: `REQ-001` (shared enforcement point), `REQ-002` (unvalidated attach fails the structural test), `REQ-003` (import-time empty-token refusal preserved)
- **Source issue**: `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-214719_mcpstartup003_auth-guard-single-point.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-083903
- **Related target files**: `scripts/mcp_servers/server.py`
