# Classify tool-level statuses in `HttpTransport.call`

## Goal

In `scripts/shared/http_transport.py`, classify the agreed tool-level status set inside `call()`
so a tool-level outcome returns a `ToolCallResult(is_error=True, error_type="tool")` through the
success path instead of raising `TransportError` and tripping the health circuit (Plan REQ-001
tool-level statuses return, REQ-003 transport set unchanged, REQ-004 fail-closed gate preserved).

## Scope

- Add `_TOOL_LEVEL_STATUSES: frozenset[int] = frozenset({400, 403, 404, 409, 422})` (new) as a
  class constant next to `_RETRYABLE_STATUS` (:144; re-verified 2026-11-02, cited as :145 at plan
  time).
- Add a classification branch in `call()` after the retryable-status block and BEFORE
  `resp.raise_for_status()` (:245): when `resp.status_code in _TOOL_LEVEL_STATUSES`, build and
  return the tool error result.
- Add `_tool_error_result(resp)` (new) static helper for tolerant body parsing.
- Unchanged: retry loop, `_RETRYABLE_STATUS` handling, the `_WRITE_TOOLS` x
  `_AMBIGUOUS_RETRY_STATUSES` fail-closed raise (REQ-004), all `except` branches, exhaustion
  path, idempotency-key logic, `_parse_http_response`, `mcp_health.py` (Plan Decision: registry
  untouched), and — because UNK-01 was decided Option A — the Option B rows (`dispatch.py`,
  `test_mcp_dispatch.py`) receive no changes.

## Assumptions

- Adopted contract (UNK-01 Option A, UNK-02 set, recorded in the plan 2026-11-02): tool-level =
  `{400, 403, 404, 409, 422}`; transport = `401` + all `5xx` + timeouts + malformed bodies +
  retry exhaustion (REQ-003).
- Verified 20261102: today `resp.raise_for_status()` (:245) turns every non-retryable non-2xx —
  including file servers' `403/404/422` — into `HTTPStatusError` → `TransportError` →
  `ToolTransportInvoker` `record_failure` (:245 invoker) → cooldown; `ToolCallResult` carries
  `error_type` as a plain field (`transport_dto.py:39`), so `from_transport` must be replaced with
  `error_type="tool"` explicitly.
- Server bodies at these statuses are FastAPI `{"detail": ...}` (file/shell/web_search/github
  handlers) or normal `{"result": ...}` — the inventory behind REQ-005; both are handled, and a
  body that is neither (or not JSON) falls back to raw text without raising.
- `401` deliberately stays transport so a wrong token remains visible (Plan Decision, UNK-02).

## Design decisions

- Placement before `raise_for_status()` (Plan Option A text): the classification is a status test,
  not an exception round-trip; the existing `HTTPStatusError` branch then only sees `401`/`5xx`.
- Tolerant parsing (Plan Option A risk mitigation): `_tool_error_result` (new) catches any parse failure
  and uses the first 512 chars of `resp.text` as the reason — a malformed body at a tool-level
  status must NOT re-enter the transport path (REQ-003's malformed-body rule applies to 2xx bodies
  via `_parse_http_response`, which stays untouched).
- Reason precedence: `detail` → `result` → raw text; the server's reason reaches the LLM as tool
  output (REQ-001 "output carrying the server's reason").

## Alternatives considered

- Option B server-side classification in `dispatch_tool` — rejected by owner decision 2026-11-02
  (broader blast radius on the shared dispatcher; recorded in the plan's Unknowns section).

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
Two additions inside `HttpTransport`: the frozenset constant and the branch/helper.

### Method
```python
    _TOOL_LEVEL_STATUSES: frozenset[int] = frozenset({400, 403, 404, 409, 422})

    @staticmethod
    def _tool_error_result(resp: httpx.Response) -> ToolCallResult:
        """Build a tool-level error result from a tool-level status response body."""
        try:
            data = parse_http_json(resp)
            reason = data.get("detail") or data.get("result") or ""
            if not isinstance(reason, str) or not reason:
                reason = resp.text[:512]
        except ValueError:
            reason = resp.text[:512]
        return ToolCallResult.from_transport(
            output=str(reason),
            is_error=True,
            request_id=resp.headers.get("x-request-id", ""),
        )
```
In `call()`, immediately before `resp.raise_for_status()`:
```python
                if resp.status_code in self._TOOL_LEVEL_STATUSES:
                    result = self._tool_error_result(resp)
                    return dataclasses.replace(
                        result, server_key=self._server_key, error_type="tool"
                    )
```

### Details
- `parse_http_json` is already imported for `_parse_http_response` (verify and reuse; raises
  `ValueError` on non-JSON — caught above).
- The write-tool fail-closed gate for `502/503/504` sits earlier in the loop and is untouched
  (REQ-004 / AC preserved).
- No logging changes: tool-level outcomes are normal results; no new warnings (the invoker's
  `stat_tool_errors` counter records them at `tool_transport_invoker.py:238`).

## Compatibility considerations

- Blast radius (Plan): `tool_runner` audit/diagnostics and `ToolTransportInvoker` now see
  `is_error=True, error_type="tool"` results → `record_success` path (REQ-002), so no bogus
  transport-failure diagnostic rows and no cooldown.
- Servers keep their own status semantics (Option A property); `429` retry behavior unchanged;
  `dispatch.py`/`test_mcp_dispatch.py` untouched (Option B rows out by decision).
- Risk accepted (Plan Option A): a genuine server fault emitted as `404` would read as
  tool-level — mitigated by the standard 4xx/5xx boundary and the REQ-005 inventory.

## Security considerations

- `401` stays a transport failure (auth problems remain loud, REQ-003).
- Server `detail` text is passed through as tool output only; no masking change (secrets masking
  is owned by the secmask/diagmask batch).

## Rollback considerations

- Revert the single commit; behavior returns to raise-on-4xx. Revert alone, no dependent rows in
  this Plan's Option A set besides tests.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py` — new cases (row 02) are red before this row
  lands.
- `uv run pytest tests/shared/test_tool_transport_invoker.py` — invoker-level HEALTHY pin (row 03).
- Regression: `uv run pytest tests/shared tests/mcp_servers` plus the MCP integration tests
  unchanged (Plan validation plan).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages` on the touched
  file, `uv run lint-imports` (`shared-is-leaf` KEPT — no new imports), coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- `403`/`404`/`422`/`400`/`409` responses return `ToolCallResult(is_error=True,
  error_type="tool", output=<server reason>)` with `request_id` carried; `401`/`5xx`/timeouts/
  malformed-2xx bodies/retry exhaustion still raise `TransportError`; the write-tool ambiguous
  `502/503/504` gate still suppresses retry.

## Out of Scope

- `mcp_health.py` (unchanged by decision); Option B rows (`dispatch.py`,
  `tests/mcp_servers/test_mcp_dispatch.py` — not modified, per the recorded UNK-01 decision);
  tests (rows 02-03); docs (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_TOOL_LEVEL_STATUSES` (new), `_tool_error_result` (new) and the classification branch | Completed | 20261102-180955 | 20261102-190915 | After rows 02-03's red tests land _TOOL_LEVEL_STATUSES + _tool_error_result + classification branch added before raise_for_status; targeted 91 tests green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-180955 | 20261102-190915 | ruff/mypy/lint-imports/bandit -ll/check_module_size pass; full suite 11366 passed; diff-cover 100%; deviation: pinned old 400 behavior in tests/shared/test_tool_executor.py and tests/integration/test_agent_mcp_integration.py (TC-A15) migrated to the REQ-001 contract - both files outside the frozen target table, evidence gap recorded |

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
- **Requirement ID**: REQ-001 (tool-level statuses return tool results), REQ-003 (transport set unchanged), REQ-004 (fail-closed 5xx gate preserved), REQ-005 (contract covers inventoried statuses)
- **Source issue**: issues/20261101-073450_healthcascade001_tool-4xx-trips-circuit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141054_healthcascade001_tool-4xx-trips-circuit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132712
- **Related target files**: scripts/shared/http_transport.py