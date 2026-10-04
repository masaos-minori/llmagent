# Implementation Procedure — `scripts/shared/http_transport.py`

## Goal

Harden `HttpTransport.call()` so a persistently malformed `/v1/call_tool` response fails after a single attempt instead of three, and remove the unreachable trailing `raise` so every exit path is explicit (`REQ-001`, `REQ-002`). Retryable-status looping, backoff, and the retry-exhaustion message are preserved unchanged (`REQ-003`).

## Scope

- **In-Scope**: Rewrite `call()`'s exception handling so `ValueError` from `_parse_http_response()` fails fast (raises `TransportError`); split it from `httpx.RequestError`, which keeps its current retry-via-exhaustion behavior; remove the unreachable trailing `raise last_exc or TransportError(...)`; collapse the `for...else` into an explicit post-loop exhaustion raise; delete the confirmed-dead `HTTPStatusError` retryable check (`break_flag=` conditional at L156 and the `if status in _RETRYABLE_STATUS` block at L159-160); drop the now-dead `last_exc` variable.
- **Out-of-Scope**: Changing `_RETRYABLE_STATUS` ({429,502,503,504}), `_RETRY_MAX` (3), the `2**attempt` backoff, or the exhaustion-message wording; making `httpx.RequestError` fail fast (UNK-01 deliberately out of scope); touching any other method in this file.

## Assumptions

- `_parse_http_response()` (L54-71) raises plain built-in `ValueError`; `httpx.RequestError` is disjoint from `ValueError` (neither is a subclass of the other), so splitting the combined handler is safe and order-independent.
- `resp.raise_for_status()` (L142) is only reached when `resp.status_code` is NOT in `_RETRYABLE_STATUS` (L128-141 `continue`s retryable statuses first). Therefore any `httpx.HTTPStatusError` caught at L149 carries a **non-retryable** status, so `break_flag=e.response.status_code not in self._RETRYABLE_STATUS` (L156) is always `True`, and the `if e.response.status_code in self._RETRYABLE_STATUS:` guard (L159-160) is always `False` — both are provably dead and removing them changes nothing.
- `stat_transport_errors` is incremented downstream in `ToolTransportInvoker._record_transport_error`, not here; the single `TransportError` raised by any non-retryable/fail-fast path propagates once, so the existing `stat_transport_errors == 1` assertion in `test_malformed_response_is_transport_error` continues to hold.
- `_transport_error(..., break_flag=True)` raises inside the call (L91-92); assigning its result to a variable is therefore never observed — the value can be `raise`d directly.
- Redaction/logging is via `attach_redaction_filter(logger)` (L17); messages carry structured fields (`tool=`, `url=`, `status=`, `request_id=`) plus `str(e)` for parsing errors, never raw response bodies or secrets. This must stay true (`REQ-004`).

## Design decisions

- **Split the combined handler into two.** Replace `except (httpx.RequestError, ValueError) as e:` (L161) with:
  - `except ValueError as e:` → `raise self._transport_error(name, f"[{type(e).__name__}]", str(e), break_flag=True)` — fail fast; a malformed body cannot succeed on retry.
  - `except httpx.RequestError as e:` → `self._transport_error(name, f"[{type(e).__name__}]", str(e))` — a returning handler that logs and lets the loop continue, preserving retry-via-exhaustion for potentially-transient network errors.
  Put `except ValueError` before `except httpx.RequestError` for readability (disjoint types make ordering non-functional).
- **Collapse `for...else` into a post-loop exhaustion raise.** Dedent the exhaustion block out of the `for` and place it after the loop body (replacing the old `else:` + trailing `raise`). Every non-retryable path now raises inside its own `except`; retryable statuses `continue`; `httpx.RequestError` logs and continues; success `return`s. Reaching past the loop therefore means all attempts were retryable or `RequestError`, i.e. genuine exhaustion — the single post-loop `raise TransportError(_build_exhaustion_message(...))` is the sole exhaustion exit. This structure is also what lets `mypy` see a guaranteed exit without a dangling fallback `raise`.
- **Remove `last_exc` entirely.** It was overwritten each iteration and never read before exhaustion raised (the exhaustion message, not `last_exc`, is what surfaces). Deleting it removes the footgun the Plan's Risks section flags.
- **Hardcode `HTTPStatusError` `break_flag=True`.** With the dead conditional removed, the handler always raises; simplify to `raise self._transport_error(name, "[HTTPStatusError]", detail, break_flag=True, health_check=False)`.
- **Preserve message shape.** Keep `health_check=True` (default) on the new `ValueError` raise so its suffix matches the prior `" — check <base_url>/health"` wording the combined handler produced; keep `health_check=False` on the `[HTTPStatusError]` raise as before.

## Alternatives considered

- **Retain the `for...else`, only split the handler and delete the trailing `raise`.** Acceptable as a smaller diff, but leaves the fragile `for...else` the Plan explicitly calls a footgun, and `mypy` still needs a guaranteed post-loop exit — pushing toward the same dedented structure. Chosen against in favor of the explicit collapse.
- **Fail fast on `httpx.RequestError` too.** Rejected — out of scope (UNK-01); transient network errors may legitimately succeed on retry, and the issue names only `ValueError`.

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

Rewrite the `try/except` region of `call()` (L121-167) as follows, preserving everything above it (the `post` call at L122-127, the retryable-status `continue` block at L128-141, and `resp.raise_for_status()` + parse + return at L142-144):

1. Remove `last_exc: Exception | None = None` (L118); keep `last_retryable_status: int | None = None` (L119).
2. In the `except httpx.TimeoutException as e:` handler, change `last_exc = self._transport_error(name, "[TimeoutException]", str(e), break_flag=True)` to `raise self._transport_error(name, "[TimeoutException]", str(e), break_flag=True)`.
3. In the `except httpx.HTTPStatusError as e:` handler, replace the body with:
   ```python
   req_id = e.response.headers.get("x-request-id", "")
   detail = f"status={e.response.status_code} request_id={req_id!r}"
   raise self._transport_error(
       name, "[HTTPStatusError]", detail, break_flag=True, health_check=False
   )
   ```
   Delete the `if e.response.status_code in self._RETRYABLE_STATUS:` / `last_retryable_status = e.response.status_code` block (L159-160).
4. Replace the `except (httpx.RequestError, ValueError) as e:` handler (L161-162) with two handlers:
   ```python
   except ValueError as e:
       raise self._transport_error(name, f"[{type(e).__name__}]", str(e), break_flag=True)
   except httpx.RequestError as e:
       self._transport_error(name, f"[{type(e).__name__}]", str(e))
   ```
5. Replace the `else:` clause (L163-166) and the trailing `raise last_exc or TransportError(...)` (L167) with a single dedented post-loop block at function-body indentation:
   ```python
   msg = self._build_exhaustion_message(name, last_retryable_status)
   logger.error(msg)
   raise TransportError(msg)
   ```

### Method

Read-only reference: `_transport_error` (L76-93, `break_flag` semantics), `_build_exhaustion_message` (L95-102), `_RETRYABLE_STATUS`/`_RETRY_MAX` (L73-74). Confirm `ValueError` is not a subclass of `httpx.RequestError` before relying on handler disjointness.

### Details

- Keep line length ≤ 88 (`ruff format`); the two new one-line handlers may need wrapping.
- Do not add imports; no new symbols.
- Verify no other method referenced `call()`'s internal `last_exc`/`for...else` contract (it is private; nothing external depends on it).

## Compatibility considerations

- `call()`'s signature and return/raise contract are unchanged: still returns `ToolCallResult` on success, raises `TransportError` on transport-level failures. Callers (`ToolExecutor._raw_execute` → `ToolTransportInvoker`) see the same `TransportError` surface.
- Behavioral delta is confined to persistently malformed bodies: 3 `post` calls → 1, with an identical `TransportError` (same `[ValueError]` prefix, same health-check suffix). Retryable/non-retryable/timeout/`RequestError` outcomes are byte-for-behaviorally identical.
- No `docs/*.md` documents retry/backoff policy (Plan Documentation Impact = N/A); verify none appears and update only if it drifts.

## Security considerations

No change to redaction. Parsing-error messages expose only the structural failure (`missing 'result' str field`, `is_error must be bool, got <type>`), never response payloads or the auth token. The `RequestError` handler logs `str(e)` exactly as before.

## Rollback considerations

Contained to `call()`. Restoring the original L118-167 region (combined handler, `for...else`, trailing `raise`) fully reverts. No config/schema/deploy impact.

## Validation plan

| Target File/Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Unit: `TestHttpTransportRetry` + `TestHttpTransportErrors` unchanged | `uv run pytest tests/shared/test_tool_executor.py tests/shared/test_tool_executor_routing.py` | Retryable exhausts 3× then raises exhaustion message; non-retryable raises `[HTTPStatusError]`; timeouts raise; all pass |
| `scripts/shared/http_transport.py` | Unit: existing malformed test still holds | `uv run pytest tests/shared/test_tool_executor.py::TestHttpTransportErrors::test_malformed_response_is_transport_error -k malformed` | `stat_transport_errors == 1` per parametrized case |
| `scripts/shared/http_transport.py` | Static: lint/type/security | `uv run ruff check scripts/shared/http_transport.py`, `uv run mypy scripts/shared/http_transport.py`, `uv run bandit -r scripts/shared/http_transport.py -c pyproject.toml` | Zero findings |

## Completion criteria

- `ValueError` from `_parse_http_response()` raises `TransportError` after a single attempt; `httpx.RequestError` still retries via exhaustion.
- No unreachable code remains; `last_exc` and the dead `HTTPStatusError` retryable check are gone; every non-retryable path has exactly one explicit failure exit.
- `_RETRYABLE_STATUS`, `_RETRY_MAX`, `2**attempt` backoff, and exhaustion-message wording are unchanged.
- `TestHttpTransportRetry` and `TestHttpTransportErrors` pass unchanged; `ruff`, `mypy`, and `bandit` report zero findings.

## Out of scope

Making `httpx.RequestError` fail fast (UNK-01), changing retry counts/statuses/backoff, other methods in `http_transport.py`, and production callers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Split handler; collapse for..else; remove dead code |
| 2 | Add or update tests per Validation plan | Done | — | — | Row 2 adds the malformed post-count regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | pytest + ruff/mypy OK |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | N/A: no docs document retry/backoff policy |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261003-154654_invoc002_harden-httptransport-call-retry-control-flow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261003-165320_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-183931
- **Related target files**: `scripts/shared/http_transport.py`
