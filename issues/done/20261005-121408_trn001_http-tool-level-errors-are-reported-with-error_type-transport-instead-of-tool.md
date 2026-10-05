# HTTP tool-level errors are reported with error_type "transport" instead of "tool"

## Priority
High

## Summary
`ToolCallResult.from_transport()` now labels every error result as `error_type="transport"`. Its only caller, `HttpTransport._parse_http_response()`, uses it for HTTP 200 responses whose body carries `is_error: true`, which are tool-level errors. As a result `ToolTransportInvoker._record_success()` no longer increments `stat_tool_errors`, and callers see the wrong error classification. Restore the documented `"tool"` classification for these results.

## Background
- Commit 3526dcc44 changed `scripts/shared/transport_dto.py`, `ToolCallResult.from_transport()`, from `error_type="tool" if is_error else ""` to `error_type="transport" if is_error else ""` (`git show 3526dcc44 -- scripts/shared/transport_dto.py` shows a one-line change).
- The change originated from `issues/done/20261003-152247_transport_dto_default_server_key.md` and the procedure `implementations/done/20261003-180548_01_scripts_shared_transport_dto_py.md`. The procedure states that `from_transport()` "is specifically for transport-layer results, so `transport` is the correct default" and that callers needing `tool` can override via `dataclasses.replace()`. That premise is wrong (see Evidence). No caller was updated to override.
- The `ToolCallResult.error_type` field comment in `scripts/shared/transport_dto.py` documents the vocabulary: "transport" | "tool" | "" (empty on success).
- `docs/22_mcp/mcp_03_03_transport-and-health.md` states that tool-level errors (`error_type == "tool"`) are treated as successful transport calls, trigger `record_success()` and increment `stat_tool_errors`, and that transport errors are converted to `ToolCallResult(error_type="transport")` by the transport error handlers.
- Adversarial verification (performed 20261005 against current source, tests, docs, and git history; every claim was treated as unverified):
  - Confirmed: `git show 3526dcc44 -- scripts/shared/transport_dto.py` is exactly a one-line change in `from_transport()` (`"tool"` to `"transport"`); `git log` shows 3526dcc44 is the latest commit touching that file. The commit message (gate-chain unification, HTTP hardening) does not mention this change; it was bundled into a large commit.
  - Confirmed: exactly one caller (`scripts/shared/http_transport.py:77`); grep over scripts/, tests/, tools/ finds no aliased, dynamic (`getattr`), or test use. Only `implementations/done/` documents mention it.
  - Confirmed by execution: the three tests fail, each on an `error_type` assertion with actual value `'transport'` and expected `'tool'` (test_3b2 at test_robustness_chaos.py:236, test_3b3 at :278, test_a05 at test_agent_mcp_integration.py, the `result.error_type == "tool"` assertion near line 130). In test_3b2 the same test also asserts `r1.error_type == "transport"` for a 504 retry-exhaustion path (line 235), which passes and is unaffected by Option A.
  - Corrected: the original constraint said the `server_key` override in `HttpTransport.call()` was "introduced by commit 3526dcc44"; it was not. `dataclasses.replace(parsed, server_key=...)` predates it (introduced in a5e02a7f8). 3526dcc44 changed only `error_type` in this file.
  - Corrected: the done issue `issues/done/20261003-152247_transport_dto_default_server_key.md` is titled and framed around the `server_key` default, but its Problem item 2 also asserted that `error_type` "should be `transport`" for transport-level errors. Its acceptance criteria asked for `server_key`/`error_type` parameters or a rename; the procedure instead rejected adding a parameter and only flipped `error_type`. The `server_key` default was not changed (still `""`, overridden by the caller). So the original `server_key` intent is unaffected by this issue and by Option A; only the `error_type` part of that issue is reverted. The procedure's UNK-01 step ("check `tests/shared/test_transport_dto.py`") refers to a file that does not exist, so the existing `error_type` expectations were never checked against the integration tests.
  - Corrected (side effect, previously missing): `scripts/agent/tool_runner.py:157-166` calls `ctx.diagnostics.save_transport_failure(...)` when `result.error_type == "transport"`. Since 3526dcc44, every HTTP tool-level error also writes a bogus "transport failure" diagnostic record. Option A removes this; Option B also removes it. `tool_runner.py:152` writes `result.error_type` into the `tool_exec` audit log, so audit logs and the doc-described grep recipes (`mcp_06_07`, `mcp_06_08`, `mcp_06_13`) currently misclassify these errors.
  - Confirmed: `_record_success()` increments `stat_tool_errors` only for `error_type == "tool"`; `_record_transport_error()` is the only increment site of `stat_transport_errors` and is reached only via `TransportError`. HTTP tool errors are therefore counted nowhere. Health: `_record_success()` still calls `record_success()` regardless of `error_type`, so health state is NOT affected by the regression (only the counter, audit, and diagnostics are).
  - Confirmed: docs agree with `"tool"` for this case (`mcp_03_03` line 35, `mcp_03_04` lines 45-56 table, `mcp_06_09`, `mcp_06_13` line 102, `mcp_06_08` line 75, `shared_03_03` line 20). No doc states that tool-level HTTP 200 errors are `"transport"`. Docs that show `"transport"` (mcp_02_03 line 53, mcp_03_04 line 32) describe `TransportError` conversion, consistent with Option A.
  - Other `error_type` consumers: only `tool_runner.py` (audit and diagnostics) and `ToolTransportInvoker._record_success()` read it in scripts/agent and scripts/shared; `tool_cache.py:63` recomputes `"tool"` for cached errors (so a cache-replayed HTTP error already says `"tool"`, which is inconsistent with the live result under the regression). No retry logic, scheduler, or health registry reads `error_type`. MCP-server-side and eventbus `error_type` fields are unrelated vocabularies.
  - Tests that pin `"transport"` (test_tool_executor.py, test_tool_executor_order.py, test_tool_transport_invoker.py, test_mcp_transport_crash.py, test_agent_mcp_integration.py lines 72-251, test_robustness_chaos.py:235/423) all use `TransportError`, lifecycle, or health-gate paths and do not go through `from_transport()`. No test depends on `"transport"` for an HTTP 200 `is_error: true` response, so Option A breaks nothing existing (unit-level confirmation of the regression command is part of Acceptance Criteria; the full suite was not re-run during this verification).

## Problem
Evidence (re-verified against current source and by running the tests):
- Explicit in code: `rg "from_transport"` over the repository (excluding `.venv` and markdown) returns exactly two hits: the definition in `scripts/shared/transport_dto.py` and one call in `scripts/shared/http_transport.py`, `HttpTransport._parse_http_response()`. No test calls `from_transport` directly.
- Explicit in code: `_parse_http_response()` calls `parse_http_json(resp)`, requires `result` to be `str` and `is_error` to be `bool`, then calls `ToolCallResult.from_transport(output=result_val, is_error=is_error_val, request_id=...)`. A `ValueError` raised by it is handled in `HttpTransport.call()` as a transport error. So the `from_transport()` result with `is_error=True` is always a well-formed HTTP 200 body reporting a tool failure. `HttpTransport.call()` then applies `dataclasses.replace(parsed, server_key=self._server_key)`, which does not touch `error_type`.
- Explicit in code: real transport failures (timeouts, HTTP status errors, retry exhaustion, lifecycle failures) never go through `from_transport()`. They raise `TransportError`, which `ToolTransportInvoker._record_transport_error()` converts via `_error_result(..., error_type="transport")`; `_handle_lifecycle_error()` also uses `"transport"`. So the `"transport"` value in `from_transport()` is redundant for real transport errors and wrong for tool errors.
- Explicit in code: `ToolTransportInvoker._record_success()` increments `stat_tool_errors` only when `result.is_error and result.error_type == "tool"`. With `"transport"` the counter is never incremented for HTTP tool errors, and `stat_transport_errors` is also not incremented (that happens only in `_record_transport_error()`), so these errors are counted nowhere.
- Verified by test: running `.venv/bin/python -m pytest tests/integration/test_robustness_chaos.py tests/integration/test_agent_mcp_integration.py -q -p no:cacheprovider -p no:randomly -k "a05 or 3b2 or 3b3"` fails 3 tests with `assert 'transport' == 'tool'`:
  - tests/integration/test_agent_mcp_integration.py::test_a05_http_tool_error_increments_stat
  - tests/integration/test_robustness_chaos.py::TestErrorInjectionChaos::test_3b2_multiple_error_types_in_same_turn (the tool-failure result has `error_type='transport'`)
  - tests/integration/test_robustness_chaos.py::TestErrorInjectionChaos::test_3b3_partial_batch_failure
- Caller enumeration summary: the single caller (HTTP 200, `is_error` true) expects `"tool"` according to the docs, the invoker counter and the three tests. No caller expects `"transport"` from `from_transport()`.

## Reason for Change
Correctness and observability regression: tool-level errors are misclassified, `stat_tool_errors` is no longer incremented, and the code contradicts `docs/22_mcp/mcp_03_03_transport-and-health.md`. Downstream consumers of `error_type` also see the wrong value: the `tool_exec` audit log (`scripts/agent/tool_runner.py:152`) and `save_transport_failure` diagnostics (`tool_runner.py:157-166`, which now fire for tool errors). Health state is not affected. Three integration tests fail on master.

## Implementation Intent
Two options were considered:
- Option A: restore `error_type="tool" if is_error else ""` in `ToolCallResult.from_transport()` and fix its docstring so it states that the result represents a tool-level result parsed from a successful transport response (and that transport failures are built by the invoker, not here). One-line behavioral change; the single caller needs no change.
- Option B: keep `"transport"` as the `from_transport()` default and override in `HttpTransport._parse_http_response()` (or `call()`) with `dataclasses.replace(..., error_type="tool" if is_error else "")`. This keeps the previous issue's intent (default is transport) but leaves a constructor whose default is wrong for its only use, and adds an override that every future caller must remember.

Side-effect comparison (verified): both options restore `"tool"` for the HTTP path and therefore yield identical runtime behavior for the audit log, diagnostics, and `stat_tool_errors`. They differ only in where the classification lives (A: in the DTO constructor; B: in the caller). No retry, health, or scheduler logic reads `error_type`, so neither option has additional side effects. Option A also restores the pre-3526dcc44 state, which is the state the docs and tests were written against.

Recommendation (survives verification): Option A. The caller enumeration shows one caller, and it always needs `"tool"`; there is no caller that needs `"transport"`, so a default that every caller must override is a trap. Option B is acceptable only if the owner wants to rename or re-scope `from_transport()` as a generic constructor; in that case prefer an explicit `error_type` parameter instead of a post-hoc replace. The owner decides.

Tests must not be changed; the three failing tests already encode the expected behavior.

## Target Files or Areas
- scripts/shared/transport_dto.py (`ToolCallResult.from_transport`)
- scripts/shared/http_transport.py (`HttpTransport._parse_http_response`; only for Option B)
- scripts/shared/tool_transport_invoker.py (`ToolTransportInvoker._record_success`; read-only reference)
- tests/integration/test_robustness_chaos.py, tests/integration/test_agent_mcp_integration.py (read-only; must not be changed)

## Required Changes
- Option A (recommended): change the `error_type` expression in `ToolCallResult.from_transport()` back to `"tool"` for `is_error=True`, and update its docstring.
- Option B: keep the default and override `error_type` in the HTTP parsing path.
- Do not change `_error_result(..., error_type="transport")` or `_record_transport_error()`.

## Constraints
- Do not change the `error_type` vocabulary ("transport" | "tool" | "").
- Do not change the `server_key` handling: `from_transport()` keeps `server_key=""` and the `dataclasses.replace(parsed, server_key=self._server_key)` override in `HttpTransport.call()` stays (it predates 3526dcc44; that commit changed only `error_type`).
- Do not modify the tests listed above.

## Acceptance Criteria
- tests/integration/test_agent_mcp_integration.py::test_a05_http_tool_error_increments_stat passes.
- tests/integration/test_robustness_chaos.py::TestErrorInjectionChaos::test_3b2_multiple_error_types_in_same_turn passes.
- tests/integration/test_robustness_chaos.py::TestErrorInjectionChaos::test_3b3_partial_batch_failure passes.
- An HTTP 200 response with `is_error: true` yields `error_type == "tool"` and increments `stat_tool_errors`; a transport failure still yields `error_type == "transport"` and increments `stat_transport_errors`.
- `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` shows no new failures compared with the current baseline (the 7 failures tracked by the stp001 and apr001 issues may remain until those are fixed).

## Testing Expectations
- Run the three listed tests and the regression command above.
- Recommended: add a unit test (new file, for example tests/shared/test_transport_dto.py, which does not exist today) for `ToolCallResult.from_transport()` pinning `is_error=True` to `"tool"`, `is_error=False` to `""`, `source == "mcp"`, and `server_key == ""`. The three integration tests cover the behavior only indirectly through HTTP mocks and are the reason this regression slipped past the unit level. This is an addition, not a change of existing tests.
- Optionally add a test that `ctx.diagnostics.save_transport_failure` is not called for an HTTP tool-level error in the tool_runner path.
- Run ruff and mypy on the changed files.

## Documentation Impact
- docs/22_mcp/mcp_03_03_transport-and-health.md already describes the intended behavior ("tool" for tool-level errors); no edit is expected under Option A. Under Option B no edit is expected either.
- docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md lists `error_type` values `"tool"`, `"transport"`, `""`; unchanged.
- No docs/ statement referencing `from_transport` was found.

## Out of Scope
- Redesigning `ToolCallResult` or renaming `from_transport`.
- Changes to retry logic or health tracking in `HttpTransport`/`ToolTransportInvoker`.
- Any change to tests or docs.

## Dependencies
N/A: none (independent of the stp001 and apr001 issues).

## Unresolved Questions
- Does the owner prefer Option A or Option B? Recommendation is A.
- Whether the intended meaning of the done issue (`issues/done/20261003-152247_...`) for `error_type` was a deliberate decision by the owner or a mistaken premise: the issue text and procedure are internally inconsistent (title is about `server_key`); the owner's intent beyond the written text is unknown.
- Whether the full regression command (`tests/agent tests/shared tests/integration`) has other failures attributable to 3526dcc44: not re-run during this verification; only the three listed tests were executed.
- Whether any persisted audit logs or diagnostic records written since 3526dcc44 (HTTP tool errors labeled `transport`) need correction: unknown; no data was inspected.
- Whether other readers of `error_type` outside scripts/ (for example audit tooling) were adapted to the `"transport"` value after commit 3526dcc44: unknown; no such consumer was found in scripts/.

## AI Implementation Instruction
Keep the change minimal (one expression and docstring under Option A). Do not edit tests or docs. Do not touch the transport error path. Run the three listed tests and the regression command, and report results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure (originating procedure for the regression: implementations/done/20261003-180548_01_scripts_shared_transport_dto_py.md)
- **Generated at**: 20261005-121408
- **Related target files**: scripts/shared/transport_dto.py, scripts/shared/http_transport.py, scripts/shared/tool_transport_invoker.py
