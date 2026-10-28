## Goal

Replace the implicit fall-through in `HttpTransport.call()`'s `except httpx.RequestError` handler
with an explicit `continue`, and make the last request-error cause reach the caller inside the
retry-exhaustion message instead of being logged only (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

- `except httpx.RequestError as e:` handler (current code L212-220): record the error's class name
  and message in new loop state `last_request_error` (new), keep the existing
  `self._transport_error(...)` warning call, then end the handler with an explicit `continue`
  (REQ-001).
- `_build_exhaustion_message()` (current code L134-141): gain an optional `last_error` (new) parameter
  (new) that appends a `last_error=<class>: <message>` part when provided, ordered
  `tool=`, `status=` (if any), `last_error=` (if any), `after <N> attempts` (REQ-002).
- The exhaustion call site (current code L221): pass the recorded `last_request_error` (new) to
  `_build_exhaustion_message()`.
- The REQ-006 handler comment (current code L213-219): rewritten to state the retry is an explicit
  `continue` and that the final exhaustion message carries the last request-error cause (REQ-004).

## Assumptions

- Implementation order (plan Dependencies): this plan lands BEFORE the sibling mcpinv001 plan
  (`plans/done/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md`, procedures
  `implementations/20261028-004925_01..03`). mcpinv001's procedures are written against this
  document's applied handler state; its fail-closed `raise` for ambiguous write errors is inserted
  before this document's capture/`continue`, so ambiguous post-send write errors terminate the loop
  early and never reach the exhaustion path, while pre-send write errors and all read-tool errors
  take the capture + `continue` path defined here.
- Overlap on `tests/shared/test_http_transport.py` with mcpinv001 (`20261028-004925_02`): both
  plans add disjoint tests to the same file; the existing
  `test_request_error_retried_three_times_for_write_and_read_tool` stays green in both because the
  safe-error set mcpinv001 gates on includes `httpx.ConnectError` used by that test.
- The exhaustion `TransportError` is raised at the uniform site (current code L223) outside the
  loop; the cause reaches the caller through message text only. `raise ... from last_request_error`
  chaining is optional and not asserted by any test (the caller-visible channel is the message).
- Only consumers of the message text are the two `"Retry exhausted"` substring assertions in
  `tests/shared/test_tool_executor.py` and the two documentation descriptions (plan Assumptions);
  appending a part after `status=` satisfies AC-2 without breaking them.

## Design decisions

- Uniform exhaustion surface (plan Design): no mid-loop raise on the final attempt; status-based
  and request-error-based exhaustion keep surfacing one `[Retry exhausted] ...` `TransportError`
  whose parts describe the cause.
- Cause as an appended optional part mirroring the existing optional `status=` part; fixed part
  order for parse-stability.
- Logging unchanged: the existing `_transport_error(...)` warning call stays (per-attempt detail in
  logs); the `/health` suffix it appends to the warning is not duplicated into the exhaustion
  message (REQ-002).
- Explicit `continue` costs one statement and removes the loop-body-position dependency the issue
  flags as the regression hazard.

## Alternatives considered

- Raise the built `TransportError` mid-loop on the final attempt (issue question): rejected in plan
  Design — creates a second failure-message shape for the most frequent failure class and would
  bypass the uniform `[Retry exhausted]` contract pinned by tests and docs.
- Raising the discarded `_transport_error(...)` return value from the handler: rejected — changes
  which errors retry (out-of-scope per plan Scope) and drops the attempt-count/backoff semantics.

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

1. At the loop-state declaration (`last_retryable_status: int | None = None`, current L162), add:
   ```python
   last_request_error: str | None = None  # (new) last RequestError "<class>: <message>"
   ```
2. In `_build_exhaustion_message()`, extend the signature (current L134-141):
   ```python
   def _build_exhaustion_message(
       self,
       tool_name: str,
       last_retryable_status: int | None,
       last_error: str | None = None,
   ) -> str:
   ```
   After the existing `status=` append, append:
   ```python
   if last_error is not None:
       parts.append(f"last_error={last_error}")
   ```
   Keep the docstring's "no raw response bodies" contract and the `return " ".join(parts) +
   f" after {self._RETRY_MAX} attempts"` suffix unchanged.
3. In the `except httpx.RequestError as e:` handler, after the existing
   `self._transport_error(name, f"[{type(e).__name__}]", str(e))` call (REQ-001):
   ```python
   last_request_error = f"{type(e).__name__}: {e}"  # (new) cause capture
   continue  # (new) explicit retry; no reliance on the handler being the loop body's last block
   ```
4. At the exhaustion call site (current L221), pass the cause:
   ```python
   msg = self._build_exhaustion_message(name, last_retryable_status, last_request_error)
   ```
5. Rewrite the REQ-006 handler comment (current L213-219) so it states:
   - writes and reads alike are retried on non-timeout `httpx.RequestError` via an explicit
     `continue` (REQ-006 carried forward);
   - server-side `_duplicate_cache` keyed on the once-per-logical-call `X-Idempotency-Key` remains
     the double-execution guard;
   - the last request-error cause is recorded in `last_request_error` (new) and surfaces in the
     final exhaustion message via `last_error=` (REQ-004).

### Method

Direct in-file edit; no new imports (`httpx` already imported); existing frozensets, backoff
(`wait_sec = 2**attempt`), `_RETRY_MAX`, handler ordering (`httpx.TimeoutException` before
`httpx.RequestError`), and the retryable-status branch (current L177-190) untouched (REQ-003).

### Details

- `last_request_error` (new) holds the formatted string `f"{type(e).__name__}: {e}"` (e.g.
  `ConnectError: boom`), not the exception object; httpx request-error messages are
  connection/protocol text, not response bodies (plan Assumptions).
- Status-only sequences produce `last_request_error = None`, so the message shape is byte-for-byte
  the current one for them (REQ-003, AC-2 second half).
- A mixed sequence (e.g. 503 then ConnectError) produces `tool=`, `status=503`,
  `last_error=ConnectError: ...`, `after 3 attempts` in that fixed order.
- The warning logged per request-error attempt (via `_transport_error`, `/health` suffix included
  in the log only) stays exactly as today.
- Line numbers cited are current-shipped-code positions; if mcpinv001 is implemented first
  against plan order, locate regions by structure (`except httpx.RequestError as e:`), not by line
  number — plan sequencing says mcpinv003 first, so line drift is limited to this document's own
  insertions.

## Compatibility considerations

- Message prefix `[Retry exhausted] tool=` and suffix `after <N> attempts` are frozen; the two
  substring assertions in `tests/shared/test_tool_executor.py` (the 429 path test pinning the
  prefix at its assertion around L80 and the 503 exhaustion test pinning `"Retry exhausted"` and
  `after 3 attempts` around L455) pass unmodified (AC-3).
- The two existing tests in `tests/shared/test_http_transport.py`
  (`test_request_error_retried_three_times_for_write_and_read_tool`,
  `test_timeout_exception_retried_once`) pass unmodified; attempt counts (3 and 1) are unchanged
  (AC-3).
- Sequencing with mcpinv001 (`20261028-004925_01`): implement this document first; mcpinv001's
  gate insertion points (RequestError handler, retryable-status branch) compose with the
  `continue`/capture added here. Reverse order works too — rebase step 3's capture + `continue`
  after mcpinv001's gate `raise`.
- Docs row pair: the message-shape descriptions in `docs/22_mcp/mcp_03_03_transport-and-health.md`
  and `docs/91_security/security_01_architecture-and-trust-boundaries.md` must be updated in the
  same change set by documents `20261028-010601_03` and `20261028-010601_04` (REQ-005), otherwise
  both go stale.

## Security considerations

- No raw response bodies, secrets, headers, or request args in the cause text — class name plus
  httpx's own connection-error message only, consistent with the module's redaction posture.
- Behavior change is diagnostic only: which errors retry, how many attempts, and the fail-open/
  fail-closed posture are unchanged (REQ-003).

## Rollback considerations

- Single-file revert: `git checkout -- scripts/shared/http_transport.py` restores the implicit
  fall-through and cause-less exhaustion message. The two new tests from
  `20261028-010601_02` and the two docs updates (`20261028-010601_03`, `20261028-010601_04`) must
  be reverted in the same commit — the cause-in-message test fails against the reverted transport,
  and the docs would then describe the newer shape.
- No data, config, or deploy change is involved; rollback is stateless.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor.py` — all
  pre-existing tests pass unmodified; new tests from `20261028-010601_02` pass (plan Validation
  plan).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` —
  clean; `shared` leaf contract preserved.
- Full suite `uv run pytest tests/` and `rules/toolchain.md` diff-cover step: new `last_error` (new)
  branch covered.

## Completion criteria

- Handler ends with an explicit `continue`; reading the loop body shows no reliance on the block
  being last (AC-1).
- Three request errors raise `TransportError` whose message contains `[Retry exhausted] tool=`,
  the request-error class name, the injected error text, and `after 3 attempts`; a status-only
  sequence produces the current message shape unchanged (AC-2).
- Request-error-then-success returns the successful result (covered by `20261028-010601_02`;
  AC-4).
- REQ-006 comment describes the explicit `continue` and the surfaced cause (AC-5).

## Out of Scope

- Changing the retryable set, `_RETRY_MAX`, backoff, handler ordering, or `/health` suffix
  behavior of other handlers (plan Scope).
- Mid-loop raise on the final attempt (plan Design, rejected).
- Read-vs-write retry asymmetry — governed by mcpinv001 (`20261028-004925_01`).
- Tests and docs edits — covered by `20261028-010601_02`, `20261028-010601_03`,
  `20261028-010601_04`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 20261028-100140 | Sequence before 20261028-004925_01 |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-28 | 20261028-100140 | See 20261028-010601_02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 20261028-100140 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-28 | 20261028-100140 | See 20261028-010601_03/_04 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-010601
- **Related target files**: scripts/shared/http_transport.py