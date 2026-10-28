## Goal

Replace the implicit fall-through in `HttpTransport.call()`'s `httpx.RequestError`
handler with a declared `continue`, and propagate the specific request-error cause to
the retry-exhaustion message built by `_build_exhaustion_message()`, without changing
which errors retry or how many attempts occur (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

- Add an explicit `continue` after the logging call in the `except httpx.RequestError`
  handler and capture the last request-error detail in loop state.
- Extend `_build_exhaustion_message()` to append a `last_error=<class>: <message>` part
  when a request error was recorded.
- Update the REQ-006 handler comment to state the explicit `continue` and the surfaced
  cause.
- Tests live in `tests/shared/test_http_transport.py` (this document); doc updates live
  in `docs/22_mcp/mcp_03_03_transport-and-health.md` and
  `docs/91_security/security_01_architecture-and-trust-boundaries.md` (separate
  documents).
- Out-of-Scope: changing the retryable set, `_RETRY_MAX`, per-attempt backoff, handler
  ordering, other handlers' `/health` behavior, or raising `TransportError` mid-loop on
  the final attempt.

## Assumptions

- The caller-visible channel for exhaustion is the `TransportError` message text only:
  `scripts/shared/tool_transport_invoker.py::call_via_transport` catches the
  `TransportError` and classifies by exception type, not by message text (verified).
- Appending the cause after the existing parts satisfies AC-2 without breaking the two
  `"Retry exhausted"` substring assertions in `tests/shared/test_tool_executor.py`
  (lines 80, 455) or the attempt-count tests in this test file.
- Status-only exhaustion sequences are unaffected: no request error occurs on those
  paths, so `last_request_error` (new) stays unset and no `last_error=` part is appended; the
  `[Retry exhausted] tool=<name> status=<n> after 3 attempts` shape is preserved.
- Overlap with sibling plan `plans/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md`
  on `scripts/shared/http_transport.py` and `tests/shared/test_http_transport.py` is
  Compatible and sequenced: this Plan implements first (declared control flow + cause),
  and mcpinv001 then adds its fail-closed gate on top. Both Plans mark the overlap
  Compatible.
- Overlap with sibling plan
  `plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md` on
  `docs/22_mcp/mcp_03_03_transport-and-health.md` is Compatible and sequenced: this
  Plan edits the "**Retries**" bullet (line 28); mcpcompat001 corrects the re-export
  statement at line 35. Disjoint regions; the later implementer rebases.

## Design decisions

- **Cause as an appended optional part**: `_build_exhaustion_message()` gains
  `last_error=` alongside the existing optional `status=`; order is fixed as
  `tool=`, `status=` (if any), `last_error=` (if any), `after <N> attempts` for
  parse-stability and to preserve the documented message contract.
- **Declared flow over cleverness**: the explicit `continue` costs one statement and
  removes the loop-body-position dependency the Issue flags as the regression hazard.

## Alternatives considered

- **Raise the built `TransportError` mid-loop on the final attempt** (rejected): would
  introduce a second failure-message shape for the most frequent failure class. All
  retry-exhausted paths keep surfacing one `[Retry exhausted] ...` `TransportError`;
  only its parts describe the cause.

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

1. In `call()`, initialize the new loop-local state next to `last_retryable_status`
   (line 162): add `last_request_error: str | None = None`.
2. In the `except httpx.RequestError as e:` handler (lines 212-220), after the existing
   discarded `self._transport_error(...)` call, record the cause and `continue`
   explicitly.
3. Extend `_build_exhaustion_message()` (lines 134-141) to accept the captured cause and
   append the `last_error=` part when present.
4. Pass `last_request_error` (new) at the call site (line 221).
5. Update the REQ-006 handler comment (lines 213-219) to state the explicit `continue`
   and the surfaced cause.

### Method

Before (current handler, lines 212-220):

```python
            except httpx.RequestError as e:
                # REQ-006: writes are always retried on a non-timeout
                # httpx.RequestError (this handler), exactly like read tools.
                # Safety against double execution rests on the always-active
                # server-side _duplicate_cache (dispatch.py), which deduplicates
                # every write keyed on the X-Idempotency-Key emitted once per
                # logical call (lines 153/159). No client-side backstop exists:
                # the key is always present, so a key-presence gate is impossible.
                self._transport_error(name, f"[{type(e).__name__}]", str(e))
```

After:

```python
            except httpx.RequestError as e:
                # REQ-006: writes are always retried on a non-timeout
                # httpx.RequestError (this handler), exactly like read tools.
                # Retry is an explicit `continue` below (was implicit fall-through);
                # the request-error cause is captured for the exhaustion message.
                # Safety against double execution rests on the always-active
                # server-side _duplicate_cache (dispatch.py), which deduplicates
                # every write keyed on the X-Idempotency-Key emitted once per
                # logical call (lines 153/159). No client-side backstop exists:
                # the key is always present, so a key-presence gate is impossible.
                self._transport_error(name, f"[{type(e).__name__}]", str(e))
                last_request_error = f"{type(e).__name__}: {e}"
                continue
```

Before (`_build_exhaustion_message`, lines 134-141):

```python
    def _build_exhaustion_message(
        self, tool_name: str, last_retryable_status: int | None
    ) -> str:
        """Build a safe retry-exhaustion diagnostic without exposing raw response bodies."""
        parts = [f"[Retry exhausted] tool={tool_name}"]
        if last_retryable_status is not None:
            parts.append(f"status={last_retryable_status}")
        return " ".join(parts) + f" after {self._RETRY_MAX} attempts"
```

After:

```python
    def _build_exhaustion_message(
        self,
        tool_name: str,
        last_retryable_status: int | None,
        last_request_error: str | None = None,
    ) -> str:
        """Build a safe retry-exhaustion diagnostic without exposing raw response bodies."""
        parts = [f"[Retry exhausted] tool={tool_name}"]
        if last_retryable_status is not None:
            parts.append(f"status={last_retryable_status}")
        if last_request_error is not None:
            parts.append(f"last_error={last_request_error}")
        return " ".join(parts) + f" after {self._RETRY_MAX} attempts"
```

Update the call site (line 221) to pass the new argument:

```python
        msg = self._build_exhaustion_message(
            name, last_retryable_status, last_request_error
        )
```

### Details

- `last_request_error` (new) holds `f"{type(e).__name__}: {e}"` (e.g. `ConnectError: boom`),
  i.e. the exception class name and its string message — connection/protocol text, never
  a raw response body.
- The explicit `continue` inside the `except` block continues the enclosing `for` loop
  (lines 169-220), equivalent to the prior implicit fall-through but position-independent.
- Message shape for a pure request-error sequence (AC-2):
  `[Retry exhausted] tool=<name> last_error=ConnectError: boom after 3 attempts`.
- `_build_exhaustion_message()` gains an optional keyword parameter with a `None`
  default, so any other callers (none currently) keep working and the status-only path
  is unchanged.

## Compatibility considerations

- The added parameter to `_build_exhaustion_message()` is keyword/optional with a `None`
  default; the public contract of `call()` (raises `TransportError`, returns
  `ToolCallResult`) is unchanged.
- Existing substring assertions (`"Retry exhausted"` in `tests/shared/test_tool_executor.py`;
  attempt-count assertions in `tests/shared/test_http_transport.py`) stay valid because
  the prefix and suffix shapes are frozen (AC-3).

## Security considerations

- The appended `last_error=` carries only the exception class name and `str(e)`
  (connection/protocol text), never a raw response body — consistent with the doc rule
  "raw response bodies are not included" and the method's own docstring.

## Rollback considerations

- Revert the commit; the change is a single logical unit (handler + message builder +
  comment).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Unit (injected fakes) | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor.py` | New cause/continue tests pass; all pre-existing tests pass unmodified |
| `scripts/shared/http_transport.py` | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; `shared` leaf contract preserved |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Docs consistency (22_mcp) | `rules/toolchain.md` documentation consistency check | Message description matches implemented shape |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Docs consistency (91_security) | `rules/toolchain.md` documentation consistency check | Template includes the request-error cause variant |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New branches covered |

## Completion criteria

- Reading `call()`'s loop body shows an explicit `continue` in the `RequestError` handler
  and no reliance on the `except` block being last (AC-1).
- Three consecutive `httpx.ConnectError` responses raise `TransportError` whose message
  contains both `[Retry exhausted] tool=<name>` and the cause (`ConnectError` + injected
  text); a status-only sequence produces the current shape unchanged (AC-2).
- A request error followed by a 200 returns the parsed `ToolCallResult` (AC-4).
- Existing retry/backoff and `"Retry exhausted"` substring tests pass unmodified (AC-3).
- The REQ-006 comment and both doc descriptions match the implemented behavior (AC-5).

## Out of Scope

- Changing the retryable set, `_RETRY_MAX`, per-attempt backoff, or handler ordering.
- Raising `TransportError` mid-loop on the final attempt.
- The read-vs-write retry asymmetry governed by sibling plan mcpinv001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the explicit `continue` + `last_request_error` (new) state in the `RequestError` handler | Completed | 20261028-100936 | 20261028-100936 |  |
| 2 | Extend `_build_exhaustion_message()` with the `last_error=` cause part; update the REQ-006 comment | Completed | 20261028-100936 | 20261028-100936 |  |
| 3 | Add or update tests per Validation plan | Completed | 20261028-101844 | 20261028-101844 |  |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-101844 | 20261028-101844 |  |

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
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-224722
- **Related target files**: scripts/shared/http_transport.py