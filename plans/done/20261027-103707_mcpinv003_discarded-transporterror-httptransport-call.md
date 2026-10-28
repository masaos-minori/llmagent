# Plan: Explicit retry control flow and preserved cause in `HttpTransport.call()`'s RequestError handler

## Goal
- Replace the implicit fall-through in `HttpTransport.call()`'s `httpx.RequestError` handler with
  a declared control-flow statement, and make the specific request-error cause reach the caller in
  the retry-exhaustion message instead of being logged only, without changing which errors retry
  or how many attempts occur.

## Priority
Low

## Scope
- **In-Scope**:
  - Explicit `continue` after the request-error logging call in the `RequestError` handler.
  - Capturing the last request-error detail (exception class name and message) in loop state and
    appending it to the retry-exhaustion message built by `_build_exhaustion_message()`.
  - Updating the REQ-006 handler comment to state the explicit `continue` and the surfaced cause.
  - New unit tests: exhaustion cause present in the raised message; RequestError-then-success
    returns the successful result.
  - Documentation sync for the message-shape descriptions in `mcp_03_03` and the security doc's
    error-message template.
- **Out-of-Scope**:
  - Changing which transport errors are retried (carried from the Issue).
  - Changing `_RETRY_MAX`, per-attempt backoff, or the `/health` suffix behavior of other
    handlers (carried from the Issue).
  - Raising the built `TransportError` mid-loop on the final attempt (rejected option — see
    Design; the exhaustion surface stays uniform).
  - Read-vs-write retry asymmetry — governed by the sibling mcpinv001 Plan, not this one.
- **Dependencies**:
  - Sibling issue `issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md` targets the
    same `RequestError` handler. Implementation order: **mcpinv003 first**, then mcpinv001 (both
    Plans record the overlap as Compatible: this Plan makes the handler's control flow explicit;
    mcpinv001 then adds the fail-closed gate on top of it).

## Background
- `HttpTransport.call()` wraps the POST in a `_RETRY_MAX` (=3) attempt loop. The
  `except httpx.RequestError` handler calls `self._transport_error(name, error_type_tag, str(e))`
  and discards the returned `TransportError`; because the `except` block is the last statement of
  the loop body, the retry happens by implicit fall-through rather than a declared `continue`.
  Sibling handlers fail fast (`TimeoutException` breaks; `HTTPStatusError` and `ValueError` raise
  `self._transport_error(...)`).
- `_transport_error()` builds the message, logs a warning, and returns the exception (raising only
  with `break_flag=True`); the discarded call is therefore a logging side effect whose constructed
  message never reaches the caller.
- On exhaustion the caller receives `_build_exhaustion_message()`'s generic text
  `[Retry exhausted] tool=<name> [status=<n>] after 3 attempts`, which does not distinguish
  request-error exhaustion from retryable-status exhaustion.

## Problem
- After three request errors the caller sees only the generic exhaustion text; the type tag, the
  underlying httpx exception message, and the `/health` hint are logged but not propagated
  (verified: `_build_exhaustion_message()` includes the status field only when a retryable HTTP
  status was seen; a pure RequestError sequence produces no cause at all).
- Correctness depends on the `except` block being the loop body's last statement; adding or
  reordering any statement after it silently changes retry behavior with no lint or type signal.
- The Issue's Documentation Impact ("comment only") is incomplete: repository evidence shows two
  docs document the message shape — `docs/22_mcp/mcp_03_03_transport-and-health.md` ("The
  `TransportError` message (`\"[Retry exhausted] ...\"`) includes the tool name, the last retryable
  HTTP status (if any), and the attempt count") and
  `docs/91_security/security_01_architecture-and-trust-boundaries.md` (message template
  `[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts>
  attempts`). Adding the cause field without updating them makes both stale.

## Reason for Change
- The Issue (python-code-review generated) classifies this as a maintainability/robustness defect,
  not a runtime bug: a discarded return value relied upon by accident invites a future silent
  regression, and the lost diagnostic detail degrades observability of the most common MCP failure
  class (connection errors).

## Implementation Intent
- Declare the retry: keep the existing warning log, then `continue` explicitly.
- Preserve the cause: record each request error's class name and message in a loop-local variable
  (`last_request_error`), and extend `_build_exhaustion_message()` to append a
  `last_error=<class>: <message>` part when one was recorded. The `[Retry exhausted] tool=...`
  prefix, the `status=` part, and the `after <N> attempts` suffix keep their current shape so the
  documented message contract and the existing substring assertions stay valid.

## Requirements
- `REQ-001`: The `except httpx.RequestError` handler must end with an explicit `continue` after
  the logging call; no implicit fall-through path may remain.
- `REQ-002`: When the loop exhausts after at least one request error, the raised `TransportError`
  message must include the last request-error cause (exception class name and its message) in
  addition to the existing `[Retry exhausted] tool=<name>` and `after <N> attempts` parts; the
  `/health` hint convention of `_transport_error()` messages is not duplicated into the exhaustion
  message (the cause field carries the diagnostic instead).
- `REQ-003`: The retryable set, `_RETRY_MAX`, per-attempt backoff, handler ordering
  (`TimeoutException` before `RequestError`), and the status-exhaustion message shape for
  status-only sequences are unchanged.
- `REQ-004`: The REQ-006 handler comment states the retry is an explicit `continue` and that the
  final exhaustion message carries the last request-error cause.
- `REQ-005`: `docs/22_mcp/mcp_03_03_transport-and-health.md` and the message template in
  `docs/91_security/security_01_architecture-and-trust-boundaries.md` describe the exhaustion
  message including the request-error cause variant.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/http_transport.py | Add explicit `continue` and `last_request_error` state to the `RequestError` handler; extend `_build_exhaustion_message()` with the cause part; update the REQ-006 comment | The handler and the exhaustion-message builder are the only places the discarded detail and the implicit flow exist | REQ-001, REQ-002, REQ-003, REQ-004 | `except httpx.RequestError` handler ends with a discarded `self._transport_error(...)` call; `_build_exhaustion_message()` has no cause parameter | tests/shared/test_http_transport.py; tests/shared/test_tool_executor.py (message-substring tests, unmodified) | Verified |
| tests/shared/test_http_transport.py | Add the cause-in-message test and the RequestError-then-success test | Issue Testing Expectations; no RequestError-then-success test exists today (verified: only 429/502/503/504 success-after-error tests exist in `test_tool_executor.py`) | REQ-002, REQ-003 | Existing RequestError exhaustion tests assert attempt counts only (`test_request_error_retried_three_times_for_write_and_read_tool`) | the file itself | Verified |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Update the retry-message bullet to include the request-error cause part | The bullet enumerates the message contents and becomes stale once the cause is added | REQ-005 | "Retries" bullet: message "includes the tool name, the last retryable HTTP status (if any), and the attempt count" | N/A: documentation file | Verified |
| docs/91_security/security_01_architecture-and-trust-boundaries.md | Add the request-error cause variant to the documented `[Retry exhausted]` message template | The template shows only the status variant and becomes incomplete after the change | REQ-005 | Template line `[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts> attempts` | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/http_transport.py `_transport_error()` | Message-building and logging conventions to reuse for the cause part (no duplicate `/health` suffix) | scripts/shared/http_transport.py; REQ-002 |
| tests/shared/test_tool_executor.py | Substring assertions on `"Retry exhausted"` (`test_retries_exhausted`-style tests at the 429 and 503 paths) pin the message prefix that must stay stable | REQ-003 |
| tests/shared/test_http_transport.py | Existing RequestError/TimeoutException discrimination tests that must stay green | REQ-003 |
| scripts/shared/tool_transport_invoker.py | Confirms the exhaustion `TransportError` is caught and counted by the invoker (`call_via_transport`), so message text is the only caller-visible channel | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): The handler contains an explicit `continue`; reading the loop body shows no
  reliance on the block being last.
- `AC-2` (REQ-002): A sequence of three request errors raises `TransportError` whose message
  contains both `[Retry exhausted] tool=<name>` and the request-error cause (e.g. `ConnectError`
  and the injected detail text); a status-only sequence produces the current message shape
  unchanged.
- `AC-3` (REQ-003): Existing retry/backoff tests pass unmodified, including the
  `"Retry exhausted"` substring assertions in `tests/shared/test_tool_executor.py` and the
  attempt-count tests in `tests/shared/test_http_transport.py`.
- `AC-4` (REQ-002): A request error followed by a successful response returns the successful
  `ToolCallResult` (retry semantics intact).
- `AC-5` (REQ-004, REQ-005): The REQ-006 comment and both documentation descriptions match the
  implemented behavior.

## Tests
- `REQ-002`: Unit — three consecutive `httpx.ConnectError` responses (injected fake) raise
  `TransportError`; assert the message contains `Retry exhausted`, `ConnectError`, and the injected
  error text.
- `REQ-002`: Unit — `httpx.ConnectError` on the first attempt followed by a valid 200 response
  returns the parsed `ToolCallResult` (2 attempts).
- `REQ-003`: Regression — status-exhaustion tests (`test_retries_on_429`/`503` paths in
  `tests/shared/test_tool_executor.py`) and the RequestError attempt-count tests in
  `tests/shared/test_http_transport.py` pass without edits.

## Documentation Impact
- Required: the retry-message bullet in `docs/22_mcp/mcp_03_03_transport-and-health.md` and the
  error-message template in `docs/91_security/security_01_architecture-and-trust-boundaries.md`
  must reflect the new cause part (REQ-005), in addition to the Issue's REQ-006 comment update
  (REQ-004). The MCP transport task maps to the 22_mcp docs domain in `docs/00_index.md`'s
  "Document References by Task"; the security doc is edited only for the message-template line it
  already contains.

## Assumptions
- No higher-level caller parses the exhaustion message beyond substring matching (verified: the
  only repository consumers are the two `tests/shared/test_tool_executor.py` substring assertions
  and the two documentation descriptions; the invoker classifies by exception type, not text).
  Appending the cause after the existing parts satisfies AC-2 without breaking them.
- The cause text (`<exception class>: <str(e)>`) carries no raw response body, consistent with the
  doc rule "raw response bodies are not included"; httpx request-error messages are connection/
  protocol text, not bodies.
- Overlap with the mcpinv001 Plan on the same handler is Compatible and sequenced (mcpinv001's
  fail-closed raise for ambiguous post-send errors terminates the loop early; this Plan's changes
  govern the retry path and the exhaustion path that mcpinv001's safe-error branch still reaches).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | No blocking unknowns. The Issue's two unresolved questions are answered by repository evidence: raise-on-final-attempt is not adopted (Design, uniform exhaustion surface), and message-text consumers are only the two test substrings plus two doc descriptions (Assumptions). | — | — | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/http_transport.py | Explicit `continue` + cause capture + exhaustion-message extension | All MCP tool calls routed through `HttpTransport`; message-text consumers are tests and docs only | 5 | High (single author, 100%) | None: no new module, no config change |
| tests/shared/test_http_transport.py | Two new unit tests | Test suite only | 1 | High (single author, 100%) | None |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Retry-message bullet update | Docs domain 22_mcp | 9 | High (single author, 100%) | None |
| docs/91_security/security_01_architecture-and-trust-boundaries.md | Message-template line update | Docs domain 91_security | 28 (high churn — rebase before editing) | High (single author, 100%) | None |

## Design
- **Uniform exhaustion surface (Issue question answered)**: the specific error is not raised
  mid-loop on the final attempt. All retry-exhausted paths — status-based and request-error-based —
  keep surfacing one `[Retry exhausted] ...` `TransportError` whose parts describe the cause. This
  preserves the message contract documented in two docs and pinned by test substrings, and avoids a
  second failure-message shape for the most frequent failure class.
- **Cause as an appended optional part**: `_build_exhaustion_message()` gains the last-error detail
  alongside the existing optional `status=` part; order fixed as
  `tool=`, `status=` (if any), `last_error=` (if any), `after <N> attempts` for parse-stability.
- **Declared flow over cleverness**: the explicit `continue` costs one statement and removes the
  loop-body-position dependency that the Issue flags as the regression hazard.
- **Logging unchanged**: the existing `_transport_error(...)` warning stays, so operators keep the
  per-attempt detail in logs while the caller gains the final-cause summary.
- **Overlap handling**: this Plan edits the handler before mcpinv001 adds its classification gate;
  implement this Plan first so mcpinv001's gate builds on the declared control flow.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/shared/test_http_transport.py` and `tests/shared/test_tool_executor.py`
     unchanged to pin current attempt counts and message substrings (REQ-003;
     `scripts/shared/http_transport.py`).
2. **Phase 2: Handler and message changes**
   - [ ] Add `last_request_error` loop state and the explicit `continue` in the `RequestError`
     handler (REQ-001, REQ-002; `scripts/shared/http_transport.py`).
   - [ ] Extend `_build_exhaustion_message()` to append the `last_error=` cause part (REQ-002;
     `scripts/shared/http_transport.py`).
   - [ ] Update the REQ-006 handler comment (REQ-004; `scripts/shared/http_transport.py`).
3. **Phase 3: Tests, docs, and verification**
   - [ ] Add the cause-in-message and error-then-success unit tests (REQ-002;
     `tests/shared/test_http_transport.py`).
   - [ ] Update the retry-message bullet (REQ-005; `docs/22_mcp/mcp_03_03_transport-and-health.md`)
     and the message template (REQ-005;
     `docs/91_security/security_01_architecture-and-trust-boundaries.md`).
   - [ ] Deployment validation/scripts check: no new module or config key, so `deploy.sh` and
     configs are unchanged (REQ-003).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/http_transport.py | Unit (injected fakes) | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor.py` | New cause/continue tests pass; all pre-existing tests pass unmodified |
| scripts/shared/http_transport.py | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; `shared` leaf contract preserved |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Documentation consistency (22_mcp domain) | `rules/toolchain.md` documentation consistency check | Message description matches implemented shape |
| docs/91_security/security_01_architecture-and-trust-boundaries.md | Documentation consistency (91_security domain) | `rules/toolchain.md` documentation consistency check | Template includes the request-error cause variant |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New handler branches covered |

## Risks
- **Risk**: appending the cause changes a message some consumer substring-matches → **Mitigation**:
  verified consumers are only the two `"Retry exhausted"` substring assertions and two doc
  descriptions; the prefix and suffix shapes are frozen by AC-3.
- **Risk**: handler-region conflict with the mcpinv001 Plan → **Mitigation**: sequencing recorded
  in Dependencies (this Plan first); both Plans mark the overlap Compatible.
- **Risk**: `security_01` is high-churn (28 commits/30d) → **Mitigation**: single-line template
  edit; rebase immediately before implementing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | — | 20261028-100140 | all 4 procedures completed 2026-10-28 |
| 2 | Phase 2: handler and message changes | Completed | — | 20261028-100140 | all 4 procedures completed 2026-10-28 |
| 3 | Phase 3: tests, docs, verification | Completed | — | 20261028-100140 | all 4 procedures completed 2026-10-28 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-010601_01_scripts_shared_http_transport.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-010601_02_tests_shared_test_http_transport.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-010601_03_docs_22_mcp_mcp_03_03_transport-and-health.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-010601_04_docs_91_security_security_01_architecture-and-trust-boundaries.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-103707
- **Related target files**: scripts/shared/http_transport.py, tests/shared/test_http_transport.py, docs/22_mcp/mcp_03_03_transport-and-health.md, docs/91_security/security_01_architecture-and-trust-boundaries.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem ("no explicit `continue`"); handler verified | scripts/shared/http_transport.py | Phase 2 | AC-1 | Code review of handler + existing retry tests | Confirmed by repository evidence |
| REQ-002 | Problem (detail never propagated); Issue AC 2 | scripts/shared/http_transport.py | Phase 2 | AC-2, AC-4 | Cause-in-message and error-then-success unit tests | Confirmed by repository evidence |
| REQ-003 | Constraints (retry set, `_RETRY_MAX`, ordering) | scripts/shared/http_transport.py | Phase 2 | AC-3 | Existing retry/backoff tests unmodified | Confirmed by repository evidence |
| REQ-004 | Issue Documentation Impact (REQ-006 comment) | scripts/shared/http_transport.py | Phase 2 | AC-5 | Comment review | Confirmed by repository evidence |
| REQ-005 | Verified doc claims in `mcp_03_03` and `security_01` | docs/22_mcp/mcp_03_03_transport-and-health.md | Phase 3 | AC-5 | 22_mcp documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Verified template line in `security_01` | docs/91_security/security_01_architecture-and-trust-boundaries.md | Phase 3 | AC-5 | 91_security documentation consistency check | Confirmed by repository evidence |
| REQ-002 | Issue Testing Expectations | tests/shared/test_http_transport.py | Phase 3 | AC-2, AC-4 | New unit tests | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-010601 -->