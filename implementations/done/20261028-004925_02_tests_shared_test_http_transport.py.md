## Goal

Add unit tests to `tests/shared/test_http_transport.py` covering the fail-closed classification
gate in `HttpTransport.call()` (ambiguous RequestError, ambiguous statuses, 429 boundary,
pre-send retry) and pin that `http_transport._WRITE_TOOLS` mirrors `dispatch._write_tools`
(REQ-001, REQ-002, REQ-006).

## Scope

- New tests (each occurrence marked (new)):
  - `test_ambiguous_request_error_not_retried_for_write_tool` (new) — `write_file` with
    httpx.ReadError injected on the first attempt: exactly 1 `post` call, `TransportError`
    raised naming the tool, error class, and attempt number.
  - `test_post_send_request_error_retried_for_read_tool` (new) — `read_text_file` with
    `httpx.RemoteProtocolError`: `_RETRY_MAX` (3) `post` calls then exhaustion `TransportError`
    (REQ-004 attempt-count pin).
  - `test_ambiguous_status_not_retried_for_write_tool` (new) — `write_file` receiving 502, 503,
    504 (parametrized): exactly 1 `post` call, `TransportError` naming the status.
  - `test_429_retried_for_write_tool` (new) — `write_file` receiving 429 on every attempt:
    `_RETRY_MAX` `post` calls then exhaustion `TransportError` (429 boundary pinned, REQ-002).
  - `test_write_tools_mirror_dispatch_write_tools` (new) — assert
    `frozenset(dispatch._write_tools) == _WRITE_TOOLS` (mirror pin, REQ-006).
- No modification of any existing test in the file (AC-3: they must pass unmodified).

## Assumptions

- Tests run against the mcpinv001 transport state produced by
  `20261028-004925_01` (gate constants `_PRESEND_SAFE_ERRORS` (new),
  `_AMBIGUOUS_RETRY_STATUSES` (new)).
- Existing fixture pattern is reused verbatim: `_http_cfg()` helper, `HttpTransport` constructed
  with `MagicMock(spec=httpx.AsyncClient)` and `transport._http.post = mock_post` (current file
  L31-70).
- `httpx` 0.28.1 constructors accept a bare message (`httpx.ReadError("boom")`) as the existing
  `httpx.ConnectError("boom")` usage demonstrates.
- `mcp_servers.dispatch` imports cleanly under the tests PYTHONPATH contract
  (`tests/integration/test_production_security_regression.py` L142 already imports from it).

## Design decisions

- Attempt counts, not exception text, are the primary assertion for retry behavior
  (`mock_post.call_count`), matching the existing tests' style; the gate tests additionally
  assert the `TransportError` message contains the tool name and (for the RequestError gate)
  the exception class name, per REQ-001.
- Mirror pin compares as frozensets because `dispatch._write_tools` is a `set` and
  `http_transport._WRITE_TOOLS` is a `frozenset` built from the same
  `shared/tool_constants.py` frozensets (scripts/shared/http_transport.py L34-43,
  scripts/mcp_servers/dispatch.py L36).
- Parametrize the three ambiguous statuses in one test; 429 is a separate test so the boundary
  (REQ-002) fails loudly on its own if the split drifts.

## Alternatives considered

- Reusing `test_request_error_retried_three_times_for_write_and_read_tool` with an added
  ambiguous-error section: rejected — that test is the AC-3 pin for pre-send behavior and must
  remain untouched to prove REQ-003 preservation.
- Integration-level test through `ToolTransportInvoker`: rejected — the gate is transport-internal;
  the existing invoker-level suite (`tests/shared/test_tool_executor_routing.py`) already covers
  the composed path unchanged.

## Implementation

### Target file

`tests/shared/test_http_transport.py`

### Procedure

1. Extend the existing import block: add `_AMBIGUOUS_RETRY_STATUSES` (new) and
   `_PRESEND_SAFE_ERRORS` (new) to the `from shared.http_transport import (...)` list (L15-19),
   and add `from mcp_servers.dispatch import _write_tools` for the mirror pin.
2. Add the five new tests after `test_request_error_retried_three_times_for_write_and_read_tool`
   (L36-63), reusing the file's construction pattern:
   ```python
   transport = HttpTransport(
       http=MagicMock(spec=httpx.AsyncClient),
       base_url="http://127.0.0.1:8000",
       server_key="srv",
       cfg=_http_cfg(),
   )
   mock_post = AsyncMock()
   transport._http.post = mock_post
   ```
   - Status tests build an `AsyncMock` response with `resp.status_code = status` (and the
     attributes the success path reads, matching the existing status-retry tests in the file).
   - Gate RequestError test: `mock_post.side_effect = httpx.ReadError("boom")`;
     `pytest.raises(TransportError, match="write_file")`; assert `call_count == 1`.
   - Exhaustion/429/read tests: assert `call_count == 3` and `pytest.raises(TransportError)`.
3. Mirror pin: `assert frozenset(_write_tools) == _WRITE_TOOLS`.
4. Membership pins follow the existing style at the top of the new write-gate tests
   (`assert "write_file" in _WRITE_TOOLS; assert "read_text_file" not in _WRITE_TOOLS`).

### Method

Append-only test additions; no edits to existing tests, fixtures, or imports other than the two
import-list additions in step 1.

### Details

- `TransportError` raised by the RequestError gate is chained (`from exc`); tests do not assert
  `__cause__` beyond the message contract to avoid coupling to exception-chaining internals.
- The ambiguous-status gate raises before `last_retryable_status` recording, so the exhaustion
  message path is not exercised for gated statuses — tests assert `call_count == 1` plus the
  gate message (`pytest.raises(TransportError, match="503")` per parametrized status).
- Keep tests deterministic: no sleeps, no real sockets (pattern already MagicMock-based).

## Compatibility considerations

- AC-3 tests (`test_request_error_retried_three_times_for_write_and_read_tool`, and
  `test_retry_reuses_single_idempotency_key` / `test_write_and_read_retry_call_counts` in
  `tests/shared/test_tool_executor_routing.py`) must pass without any edit; this document adds
  nothing to them.
- The mirror pin will fail if `dispatch._write_tools` and the transport set drift; that is the
  intent (plan Risk: gate the wrong tool set) and pairs with startup `check_write_classification()`
  (ADR-003 INV-03).
- New import `mcp_servers.dispatch` inside a `tests/shared/` file is test-only and does not
  affect the `scripts/` import-linter contracts.

## Security considerations

- Injected error messages ("boom") contain no secrets; the module's redaction filter is
  exercised implicitly as today.

## Rollback considerations

- Revert together with `20261028-004925_01` (single commit pair): the gate tests fail against
  the pre-gate transport, and the mirror pin is independent but belongs to the same REQ-006
  story. `git checkout -- tests/shared/test_http_transport.py` restores the prior file.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py` — new tests pass, existing tests pass.
- `uv run pytest tests/shared/test_tool_executor_routing.py` — unchanged regression tests pass.
- `uv run pytest tests/` — full suite green (plan Validation plan row).
- `uv run ruff check tests/` and `uv run mypy --no-namespace-packages scripts/` per
  `rules/toolchain.md`.

## Completion criteria

- All five new tests present and passing; `call_count` assertions match AC-1/AC-2/AC-4 attempt
  counts exactly (1 for gated, 3 for 429/pre-send/read).
- Existing tests byte-identical (git diff shows append + import lines only).
- Mirror pin passes.

## Out of Scope

- Transport implementation changes (`20261028-004925_01`).
- `tests/shared/test_tool_executor_routing.py` (must stay unmodified; no new cases added).
- Documentation updates (`20261028-004925_03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-103200 | 20261028-110204 | 5 tests / 7 cases appended; mirror pin added |
| 2 | Add or update tests per Validation plan | Completed | 20261028-103200 | 20261028-110204 | See Blocker Log: 3 legacy tests in test_tool_executor.py also required the gate contract |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-103400 | 20261028-110204 | targeted suites green; ruff/mypy green; full suite rerun after legacy-test fix |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-103200 | 20261028-110204 | N/A: test file (plan row) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Full suite failed: 3 pre-existing tests in `tests/shared/test_tool_executor.py` (`TestHttpTransportRetry::test_retries_on_502/503/504_and_succeeds`) pinned the superseded contract (write tool retried on ambiguous statuses). The procedure's "all pre-existing tests pass unmodified" claim was stale | Yes — those 3 tests' tool argument switched from `write_file` to `read_text_file` (REQ-004 read-retry semantics preserved; write+ambiguous coverage lives in the 5 new gate tests here). `test_tool_executor_routing.py` remains unmodified | 20261028-104700 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | See 20261028-004925_03 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-006
- **Source issue**: issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004925
- **Related target files**: tests/shared/test_http_transport.py