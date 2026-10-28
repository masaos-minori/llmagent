## Goal

Add a fail-closed failure-classification gate to `HttpTransport.call()` in
`scripts/shared/http_transport.py` so a side-effecting tool call is never re-dispatched when
the server-side execution outcome is ambiguous, and correct the two stale comments that still
describe the removed key-presence gate (REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006).

## Scope

- `httpx.RequestError` handler (current code L212-223): raise `TransportError` for
  `name in _WRITE_TOOLS` on every `RequestError` that is NOT in the safe pre-send set
  {httpx.ConnectError, httpx.ProxyError}; pre-send errors keep the current retry path for
  all tools.
- Retryable-status branch (current code L176-191): for `name in _WRITE_TOOLS`, abort on
  502/503/504; 429 keeps the current retry behavior for all tools.
- Comments: the `_WRITE_TOOLS` module comment (L31-33, still claims "the idempotency retry gate
  in `call()`") and the REQ-006 handler comment (L213-221, "No client-side backstop exists")
  are rewritten to describe the classification gate.
- New module-level constants: `_PRESEND_SAFE_ERRORS` (new) frozenset of the two pre-send
  exception classes and `_AMBIGUOUS_RETRY_STATUSES` (new) frozenset {502, 503, 504}.

## Assumptions

- mcpinv003 (plan `plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md`)
  lands FIRST per its own plan; this procedure is written against the mcpinv003-applied handler
  state (explicit `continue` and `last_request_error` loop state present). The gate `raise`
  statements are inserted before the retry decision, so they compose with mcpinv003's restored
  error-propagation semantics (the gate raises on the live exception, not on a discarded one).
- httpx 0.28.1 hierarchy verified in the plan session: all timeout classes derive from
  `TimeoutException` (handled first, breaks without retry — untouched here); ConnectError and
  ProxyError are connection-establishment errors; ReadError, WriteError, RemoteProtocolError,
  LocalProtocolError are post-send ambiguous.
- `_WRITE_TOOLS` completeness is enforced at startup by `check_write_classification()`
  (ADR-003 INV-03) in `scripts/agent/tool_policy.py`; no runtime registry lookup is added.

## Design decisions

- Whitelist (safe set) classification, default-ambiguous: only the two pre-send classes retry
  for side-effecting tools; any other `RequestError` subclass — including future httpx
  additions — fails closed. The gate therefore errs on the safe side if the httpx hierarchy
  shifts.
- Status split rather than blanket status gate: 502/503/504 are ambiguous because repo servers
  emit 502/503 from post-dispatch exception handlers (`github/exception_handlers.py`,
  `rag_pipeline/rag_pipeline_server.py`) and 504 is gateway-class; 429 has no post-dispatch
  emitter in the repo and semantically precedes fulfillment, so it stays retryable for all
  tools (REQ-002).
- No new state, no config, no signature change: classification derives from the current
  attempt's error class/status and `name in _WRITE_TOOLS` only. The sent-key record and config
  toggle proposed by the issue were rejected with evidence in the plan Scope.

## Alternatives considered

- Client-side sent-key record (issue mechanism): rejected — conflicts with the per-logical-call
  key invariant (handler comment "the key is always present, so a key-presence gate is
  impossible") and would silently disable all write retries; recorded in plan Scope.
- Default-safe classification (blacklist of ambiguous errors): rejected — a future httpx
  `RequestError` subclass would default to retry (fail-open); the whitelist inverts the default.
- Gate in `scripts/shared/tool_transport_invoker.py`: rejected — the invoker sees logical calls,
  not attempts; only the transport observes per-attempt errors (plan Design, gate placement).

## Implementation

### Target file

`scripts/shared/http_transport.py`

### Procedure

1. Add module-level constants after `_WRITE_TOOLS`:
   - `_PRESEND_SAFE_ERRORS: frozenset[type[BaseException]] = frozenset({httpx.ConnectError, httpx.ProxyError})` (new)
   - `_AMBIGUOUS_RETRY_STATUSES: frozenset[int] = frozenset({502, 503, 504})` (new)
2. Rewrite the `_WRITE_TOOLS` module comment (L31-33) so it states the set now feeds the
   classification gate in `call()` and still mirrors `scripts/mcp_servers/dispatch.py`'s
   `_write_tools` (keep the ADR-004 reference). Remove the "idempotency retry gate" phrasing.
3. In the `except httpx.RequestError as exc:` handler, immediately after the `TimeoutException`
   branch (which stays first and unchanged), insert the gate before the retry decision:
   ```python
   if name in _WRITE_TOOLS and not isinstance(exc, _PRESEND_SAFE_ERRORS):
       raise TransportError(
           f"Transport failed for write tool '{name}' after attempt {attempt} "
           f"({type(exc).__name__}: {exc}); server-side execution outcome is ambiguous "
           "and client-side retry is suppressed (fail-closed, ADR-004)"
       ) from exc
   ```
   (REQ-001: message names the tool, the exception class, and the attempt number.)
4. Rewrite the REQ-006 handler comment block (current L213-221) to describe the classification
   gate and its relationship to the server-side `_duplicate_cache`: pre-send retries are safe
   because nothing executed upstream; the client gate covers the window the server cache cannot
   (first attempt errored/in-flight with no cache entry, since dispatch never caches errors).
5. In the retryable-status branch (`if resp.status_code in self._RETRYABLE_STATUS:`), before the
   `if attempt < self._RETRY_MAX - 1:` continue, insert:
   ```python
   if name in _WRITE_TOOLS and resp.status_code in _AMBIGUOUS_RETRY_STATUSES:
       raise TransportError(
           f"Transport returned {resp.status_code} for write tool '{name}' on attempt "
           f"{attempt}; dispatch may already have executed, retry suppressed "
           "(fail-closed, ADR-004)"
       )
   ```
   429 is not in `_AMBIGUOUS_RETRY_STATUSES` (new), so 429 and all read-tool statuses take the
   existing path unchanged (REQ-002, REQ-004).

### Method

Direct in-file edit; membership checks against existing frozensets; no new imports beyond the
already-present `httpx`; keep insertion points compatible with the mcpinv003-applied handler.

### Details

- `TimeoutException` handling (break_flag pattern) is untouched; timeouts never retry today, so
  they are already fail-closed for writes.
- Exhaustion path (`_build_exhaustion_message` raise after `_RETRY_MAX` attempts) is untouched:
  pre-send write retries and all read-tool retries still end in the same
  `TransportError("Tool '...' failed after 3 attempts...")` shape consumed by
  `test_tool_executor.py` substring assertions.
- `X-Idempotency-Key` emission (L161) and the per-logical-call key invariant are untouched.
- Line numbers cited are pre-mcpinv003; after mcpinv003 lands, locate the handler by structure
  (`except httpx.RequestError as exc:`), not by line number.

## Compatibility considerations

- Sequencing (plan Dependencies): mcpinv003's procedures
  (`implementations/20261028-*_scripts_shared_http_transport.py.md` from plan
  `20261027-103707`) must be implemented BEFORE this document's steps 3-5 — both edit the same
  `RequestError` handler region. If implemented in the reverse order, rebase this document's
  insertions onto the mcpinv003 result.
- Existing regression tests pin pre-send retry at `_RETRY_MAX`
  (`test_request_error_retried_three_times_for_write_and_read_tool`,
  `test_write_and_read_retry_call_counts`, `test_retry_reuses_single_idempotency_key`): the safe
  set keeps them green without modification (AC-3).
- Read-tool behavior is byte-for-byte unchanged (REQ-004).
- No signature, config, or `deploy/` change (AC-6); `shared` import-leaf contract preserved —
  only `httpx` and existing same-package imports are used (lint-imports gate).

## Security considerations

- Fail-closed default closes the client-side double-dispatch window for writes that the
  server-side `_duplicate_cache` cannot cover (post-send ambiguous failure with no cached
  result), consistent with ADR-004.
- Gate messages include tool name, error class, attempt number, and status only — no secrets,
  consistent with the module's redaction filter (`attach_redaction_filter`).

## Rollback considerations

- Single-file revert: `git checkout -- scripts/shared/http_transport.py` restores the
  always-retry policy. Tests document `20261028-004925_02` must be reverted in the same commit
  (its gate tests fail against the reverted transport); the docs document
  `20261028-004925_03` comment/doc pairing reverts with it.
- No data or config migration is involved; rollback is stateless.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor_routing.py`
  — new gate tests pass; all pre-existing tests pass unmodified.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
  — clean; `shared` leaf contract preserved.
- Full suite `uv run pytest tests/` and `rules/toolchain.md` diff-cover step per plan Validation
  plan.

## Completion criteria

- REQ-001/REQ-002 gate raises present in the handler and status branch respectively;
  REQ-003/REQ-004 paths demonstrably unchanged.
- Both comments (module + handler) describe the classification gate; no "key-presence gate is
  impossible"/"No client-side backstop" residue remains (AC-5 pairs with the docs document).
- All commands in Validation plan pass; no new config key or signature change (AC-6).

## Out of Scope

- `scripts/mcp_servers/dispatch.py` `_duplicate_cache` semantics (unchanged).
- `scripts/shared/tool_transport_invoker.py` (verified no change needed).
- `X-Idempotency-Key` emission and reuse behavior.
- Tests and docs edits — covered by `20261028-004925_02` and `20261028-004925_03`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-103200 | 20261028-110204 | Both gates present; REQ-006 comment rewritten; `_PRESEND_SAFE_ERRORS` realized as a tuple (deviation: `isinstance()` arg-2 must be a class tuple, not a frozenset — documented in code comment) |
| 2 | Add or update tests per Validation plan | Completed | 20261028-103200 | 20261028-110204 | See 20261028-004925_02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-103400 | 20261028-110204 | ruff/mypy/bandit/lint-imports green; targeted suites green; full suite rerun after legacy-test fix |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-103200 | 20261028-110204 | See 20261028-004925_03 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Procedure prescribed `_PRESEND_SAFE_ERRORS` as `frozenset`; `isinstance(exc, frozenset)` raises TypeError | Yes — implemented as `tuple[type[BaseException], ...]` with in-code comment; gate semantics identical | 20261028-103400 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004925
- **Related target files**: scripts/shared/http_transport.py