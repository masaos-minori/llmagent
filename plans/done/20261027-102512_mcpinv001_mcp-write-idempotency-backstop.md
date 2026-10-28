# Plan: Client-side fail-closed retry gate for side-effecting MCP tool calls

## Goal
- Make `HttpTransport.call()` fail closed when a transport failure for a side-effecting
  (write/delete/execute/API-write) MCP tool call leaves the server-side execution outcome
  ambiguous, so a client-side retry cannot re-dispatch a write that may already have
  executed. Preserve the existing retry resilience for pre-send connection failures and for
  all read tools.

## Priority
Medium

## Scope
- **In-Scope**:
  - Failure classification in `HttpTransport.call()`'s `httpx.RequestError` handler: side-effecting
    tools (name in the module-level `_WRITE_TOOLS` set) are not re-dispatched on post-send
    ambiguous request errors; pre-send connection errors keep retrying for every tool.
  - Retryable-status gating: side-effecting tools are not retried on the ambiguous retryable
    statuses 502/503/504; 429 keeps its current retry behavior for all tools.
  - Comment updates: the stale `_WRITE_TOOLS` module comment (still describes a removed gate)
    and the REQ-006 handler comment ("No client-side backstop exists").
  - Unit tests in `tests/shared/test_http_transport.py`, including a pin that
    `http_transport._WRITE_TOOLS` mirrors `dispatch._write_tools`.
  - Documentation update of the idempotency/retry section of the MCP transport doc.
- **Out-of-Scope**:
  - Changes to server-side `_duplicate_cache` semantics in `scripts/mcp_servers/dispatch.py`
    (carried from the Issue).
  - Any change to read-tool retry behavior (carried from the Issue).
  - Dropping or altering the `X-Idempotency-Key` (carried from the Issue).
  - **Scope amendment (Issue mechanism rejected)**: the Issue's proposed client-side sent-key
    record ("skip re-sending an identical write on a retry") is NOT implemented. The transport
    intentionally reuses one key per logical call across all retries, the handler comment states
    "the key is always present, so a key-presence gate is impossible", and the existing
    regression tests pin write retries at `_RETRY_MAX` attempts on pre-send errors — a sent-key
    skip would silently disable all write retries. Defense-in-depth is delivered instead by
    failure classification (REQ-001/REQ-002), which needs no new state.
  - **Scope amendment (no config toggle)**: the Issue gates the toggle on the guard "risk[ing]
    changing current pass behavior". The adopted classification gate provably does not change
    any currently-passing test's behavior (the existing write-retry tests inject
    `httpx.ConnectError`, a pre-send error that keeps retrying), so the Issue's own condition
    for always-on is satisfied. A default-off toggle for a safety guard is rejected.
  - `scripts/shared/tool_transport_invoker.py` (listed in the Issue's Target Files) requires no
    modification: the retry loop is internal to `HttpTransport.call()` and the pre-call gate
    chain runs exactly once per logical call. Moved to Reference Files.
- **Dependencies**:
  - Sibling issue `issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md`
    targets the same `httpx.RequestError` handler region of `HttpTransport.call()`.
    Implementation order: mcpinv003 before mcpinv001 (or one coordinated edit pass), so the
    restored error-propagation semantics are in place before the gate raises on them. Both
    Plans record the overlap as Compatible (disjoint semantics, sequenced).

## Background
- The idempotency design was built by the idem01 work (`c433c3c68` "fix(mcp): idempotency
  cache and retry-key coupling"): `HttpTransport.call()` emits one `uuid4` key per logical
  call and `dispatch.py`'s `_duplicate_cache` deduplicates side-effecting calls keyed on it.
- `HttpTransport.call()` previously carried a client-side gate (`if name in _WRITE_TOOLS and
  not idempotency_key: raise`). Because the transport always emits a key, the gate was
  unreachable and was removed in `6e9e79798` ("document always-retry policy"), which recorded
  the policy that "writes are always retried on a non-timeout `httpx.RequestError` … Safety
  against double execution rests on the always-active server-side `_duplicate_cache` … No
  client-side backstop exists".
- The removal left behind: (a) the module-level `_WRITE_TOOLS` frozenset in
  `scripts/shared/http_transport.py`, now referenced nowhere in the file, whose comment still
  says it exists "so the idempotency retry gate in `call()` covers exactly the tools the
  dispatch layer deduplicates. See ADR-004 (fail-closed on writes)"; and (b) a stale doc claim
  in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` ("Write-tool retry … gated on
  idempotency-key presence") describing the removed gate.
- The Issue (python-code-review generated) flags the resulting single-layer dependency on the
  server cache and asks whether a client-side guard is warranted. The design choice was put to
  the user on 2026-10-27; the user delegated the decision ("consider a recommended approach").
  The recommended approach — failure classification with no new state — is adopted here.

## Problem
- Verified real window: when attempt 1 of a side-effecting call fails with a **post-send**
  error (the request likely reached the server; the response was lost or the server raised an
  exception mid-handler), no `_duplicate_cache` entry exists, because `dispatch.py` only caches
  successful completed results ("Error and dry-run results are never cached"). The client then
  re-sends the same logical call and the server executes the write a second time, while
  attempt 1's execution may still be in flight. Repository evidence:
  - `HttpTransport.call()`'s `httpx.RequestError` handler retries without delay (no backoff)
    for every tool, including writes.
  - `502`/`503` are actively emitted by MCP servers **after dispatch has started**:
    `scripts/mcp_servers/github/exception_handlers.py` returns 502 for `GitHubUpstreamError`
    (a mutation may already have been executed against the upstream API),
    `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` returns 503 for
    `RagPipelineServiceError`, and `scripts/mcp_servers/web_search/web_search_server.py`
    returns 502 for `WebSearchUpstreamError` (read-only tool, unaffected by gating).
  - `TimeoutException` (including `ConnectTimeout`/`ReadTimeout`/`PoolTimeout`) already
    breaks immediately without retry, so the Issue's timeout-then-retry acceptance scenario is
    untestable against current code; the corrected testable scenarios are the RequestError and
    ambiguous-status windows.
- The Issue's bypass premises (multi-replica/load-balancer deployment, header-stripping proxy)
  have no repository evidence: each MCP service runs as a single process per
  `deploy/setup_services.sh`, and no proxy/LB layer appears in `deploy/` or `config/`. They are
  recorded as hypothetical; the adopted client-side gate is topology-independent regardless.

## Reason for Change
- Writes are the highest-stakes calls in the invocation path and the repo's own transport
  comment cites ADR-004 (fail-closed on writes). Retrying an ambiguous write is fail-open
  behavior at the exact boundary ADR-004 is meant to protect. The fix is confined to the
  transport's error handling and hardens the boundary without touching the working
  server-side dedup.

## Implementation Intent
- Keep the existing per-logical-call key contract and retry loop intact. Add a classification
  decision inside `HttpTransport.call()`'s error handlers: a tool name membership check against
  the already-present `_WRITE_TOOLS` set plus a request-error-ambiguity check decide whether an
  attempt is safe to repeat. Safe (pre-send) failures keep retrying exactly as today; ambiguous
  (post-send) failures for side-effecting tools abort with `TransportError` instead of
  re-dispatching. No new state, no config, no signature change.

## Requirements
- `REQ-001`: `HttpTransport.call()` must NOT re-dispatch a side-effecting tool (`name in
  _WRITE_TOOLS`) on a post-send ambiguous `httpx.RequestError` — every `RequestError` that is
  not in the safe pre-send set {`httpx.ConnectError`, `httpx.ProxyError`}; it must raise
  `TransportError` naming the tool, the exception class, and the attempt number.
- `REQ-002`: `HttpTransport.call()` must NOT retry a side-effecting tool on the ambiguous
  retryable statuses 502/503/504 (repository evidence shows servers emit 502/503 from
  post-dispatch exception handlers; 504 is gateway-class and ambiguous by construction). 429
  keeps its current retry behavior for all tools: no MCP server in the repo emits 429
  post-dispatch, and 429 semantically means the request was rejected before fulfillment.
- `REQ-003`: Pre-send request failures (`httpx.ConnectError`, `httpx.ProxyError`) keep the
  current retry behavior (up to `_RETRY_MAX`) for every tool, including side-effecting ones —
  the request never reached the server, so no execution ambiguity exists. This preserves
  server-down resilience and keeps the existing regression tests passing unchanged.
- `REQ-004`: Read-tool retry behavior (RequestError retry, retryable-status retry, timeout
  break) is unchanged for every failure class.
- `REQ-005`: The stale comments are corrected: the `_WRITE_TOOLS` module comment no longer
  refers to a "key-presence"-style gate, and the REQ-006 handler comment describes the
  classification gate and its relationship to the server-side `_duplicate_cache` (client gate
  covers the window the server cache cannot: ambiguous-failure re-dispatch while the first
  execution is in flight or errored without a cached result).
- `REQ-006`: The guard adds no client-side key record, no new state, no configuration keys, and
  no change to `HttpTransport.call()`'s signature; classification reuses the existing
  `_WRITE_TOOLS` set, whose completeness against the live registry is enforced by ADR-003
  INV-03 (`check_write_classification()` in `scripts/agent/tool_policy.py`).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/http_transport.py | Add pre-send/post-send classification to the `httpx.RequestError` handler and ambiguity gating to the retryable-status branch of `HttpTransport.call()`; correct the `_WRITE_TOOLS` and REQ-006 comments | The retry loop is the only place a client-side duplicate dispatch can originate; classification closes the ambiguous-failure window with no new state | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 | `HttpTransport.call()` retry loop, `_WRITE_TOOLS` frozenset, and the `except httpx.RequestError` handler (current comment: "No client-side backstop exists") | tests/shared/test_http_transport.py; tests/shared/test_tool_executor_routing.py (regression, unmodified) | Verified |
| tests/shared/test_http_transport.py | Add unit tests for the classification gate (ambiguous RequestError, ambiguous statuses, 429 boundary, pre-send retry) and a pin that `_WRITE_TOOLS` mirrors `dispatch._write_tools` | New behavior requires regression coverage; existing ConnectError-based tests must stay green unchanged | REQ-001, REQ-002, REQ-003, REQ-006 | Existing tests `test_request_error_retried_three_times_for_write_and_read_tool` and the `write_file` call path in the file | the file itself | Verified |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Update the "Idempotency and retry" section: replace the stale "gated on idempotency-key presence" claim with the classification gate and the corrected always-retry scope | The doc currently describes a gate that was removed in 2026-10-13; the new layer must be documented alongside the server cache | REQ-005 | "Idempotency and retry" section bullet "Write-tool retry … gated on idempotency-key presence" is stale vs current code | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/tool_constants.py | Canonical write-classification frozensets feeding `_WRITE_TOOLS`; read-only (shared-leaf contract) | scripts/shared/http_transport.py; REQ-001, REQ-006 |
| scripts/mcp_servers/dispatch.py | Server-side `_write_tools` mirror and `_duplicate_cache` semantics that must not change; confirms errors are never cached | scripts/shared/http_transport.py; REQ-001, REQ-002 |
| scripts/shared/tool_transport_invoker.py | Confirm the pre-call gate chain runs once per logical call and needs no change | Scope (issue target file dismissed) |
| tests/shared/test_tool_executor_routing.py | Existing retry/key-reuse regression tests (`test_retry_reuses_single_idempotency_key`, `test_write_and_read_retry_call_counts`) must pass unchanged | REQ-003, REQ-004 |
| scripts/mcp_servers/github/exception_handlers.py | Evidence that 502 is emitted after dispatch starts (post-mutation ambiguity) | REQ-002 |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Evidence that 503 is emitted from a post-dispatch exception handler | REQ-002 |
| scripts/agent/tool_policy.py | ADR-003 INV-03 static/live write-classification consistency check backing `_WRITE_TOOLS` completeness | REQ-006 |

## Acceptance Criteria
- `AC-1` (REQ-001): A side-effecting tool call whose post-send ambiguous `RequestError` fires on
  the first attempt results in exactly one HTTP POST and a raised `TransportError`; no second
  dispatch occurs.
- `AC-2` (REQ-002): A side-effecting tool call receiving 502/503/504 is not retried and raises
  `TransportError`; a side-effecting tool call receiving 429 continues to retry up to
  `_RETRY_MAX` as today.
- `AC-3` (REQ-003): `test_request_error_retried_three_times_for_write_and_read_tool` and
  `test_write_and_read_retry_call_counts` (which inject `httpx.ConnectError`, a pre-send error)
  pass without modification, asserting `_RETRY_MAX` attempts for both write and read tools.
- `AC-4` (REQ-004): Read tools show unchanged attempt counts for ambiguous RequestErrors and
  for every retryable status.
- `AC-5` (REQ-005): The `_WRITE_TOOLS` comment, the REQ-006 handler comment, and the doc's
  "Idempotency and retry" section describe the same classification behavior; the stale
  key-presence claim no longer appears.
- `AC-6` (REQ-006): No new config key appears in `config/*.toml`, `HttpTransport.call()`'s
  signature is unchanged, and the import-linter contract (`shared` leaf) is preserved.
- Corrected Issue criteria: the Issue's "timeout then retry" criterion is replaced by AC-1/AC-3
  (timeouts never retry in `HttpTransport.call()` today); the Issue's "client-side record is
  bounded" criterion is satisfied vacuously because no record is added (Scope amendment, with
  evidence).

## Tests
- `REQ-001`: Unit — `write_file` with `httpx.ReadError` / `httpx.RemoteProtocolError` injected
  on the first attempt → 1 POST call, `TransportError` raised.
- `REQ-002`: Unit — `write_file` with 503/502/504 responses → 1 POST call, `TransportError`;
  `write_file` with 429 → `_RETRY_MAX` POST calls then `TransportError` (429 boundary pinned).
- `REQ-003`: Existing unit tests pass unchanged (ConnectError → `_RETRY_MAX` for write and read).
- `REQ-004`: Unit — read tool with `ReadError`/`RemoteProtocolError` and with 503 → unchanged
  attempt counts (`_RETRY_MAX`).
- `REQ-006`: Unit — mirror pin: `http_transport._WRITE_TOOLS == dispatch._write_tools`
  (the transport comment already claims this mirror; pin it so the client gate and server dedup
  cannot drift).
- Regression scope: `tests/shared/` plus the full suite; the two existing idempotency tests
  (`test_retry_reuses_single_idempotency_key`, `test_write_and_read_retry_call_counts`) must
  pass without edits.

## Documentation Impact
- Required: the "Idempotency and retry" section of the MCP transport/dispatch doc named by
  `docs/00_index.md`'s "Document References by Task" mapping for the MCP transport task
  (`22_mcp/mcp_03_01_dispatch-and-routing.md`) must describe the classification gate
  (REQ-001/REQ-002) and correct the stale key-presence claim. Driven by REQ-005.

## Assumptions
- Design decision approved by the user on 2026-10-27 (user delegated the choice: "consider a
  recommended approach"): failure-classification gate adopted; sent-key record and config
  toggle rejected, with repository evidence recorded in Scope.
- The static classification sets are complete for every registered side-effecting tool
  (enforced by `check_write_classification()`, ADR-003 INV-03); a tool missing from both the
  static sets and the registry would fail open, which the INV-03 check prevents at startup.
- Deployment topology is single-process per MCP service (`deploy/setup_services.sh`); the
  Issue's multi-replica/header-strip bypass scenarios are hypothetical. The adopted gate works
  under either topology.
- httpx 0.28.1 exception hierarchy as verified in this session: every timeout class
  (`ConnectTimeout`, `ReadTimeout`, `WriteTimeout`, `PoolTimeout`) derives from
  `TimeoutException` (already handled first, breaks without retry); `ConnectError` and
  `ProxyError` are connection-establishment (pre-send) errors; `ReadError`, `WriteError`,
  `RemoteProtocolError`, `LocalProtocolError` are post-send ambiguous.
- The `shared` import-leaf contract is preserved because classification uses only
  `httpx` and the same-package `tool_constants` imports that `http_transport.py` already has.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (False/True) |
|---|---|---|---|---|
| UNK-01 | Whether a future deployment runs MCP dispatch behind replicas or a load balancer (the Issue's premise) | No LB/replica config or deploy evidence in `deploy/` or `config/` | Not required for this Plan: the adopted gate is stateless and topology-independent; revisit only if shared-state server dedup is ever planned | False |
| UNK-02 | Whether real-world proxies ever inject 429 mid-execution upstream | No such layer exists in the current topology | Pin 429 retry behavior with the boundary test; revisit if a gateway is ever introduced | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/http_transport.py | Error-handler classification in `call()` + comments | All MCP tool calls routed through `HttpTransport` (single production consumer: `ToolTransportInvoker`) | 5 | High (single author, 100%) | None: no new module, no config change |
| tests/shared/test_http_transport.py | New unit tests | Test suite only | 1 | High (single author, 100%) | None |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Idempotency/retry section update | Docs domain 22_mcp | 24 (high churn — coordinate with sibling mcpinv plans) | High (single author, 100%) | None |

## Design
- **Gate placement**: classification lives inside `HttpTransport.call()`'s error handling, not
  in the invoker or agent layers. The transport is the only component that observes individual
  attempts; the invoker's gate chain already runs once per logical call (verified) and must
  stay that way.
- **Safe set (whitelist), default-ambiguous**: only `httpx.ConnectError` and `httpx.ProxyError`
  are classified pre-send-safe and keep retrying for every tool. Any other `RequestError`
  subclass — including future httpx additions — is treated as post-send ambiguous and fails
  closed for side-effecting tools. This default makes the gate fail on the safe side if the
  exception hierarchy shifts.
- **Status split**: 502/503/504 are ambiguous for side-effecting tools because the repo's
  servers emit 502/503 from post-dispatch exception handlers (execution already started) and
  504 is a gateway-class timeout. 429 is a pre-fulfillment rejection with no post-dispatch
  emitter in the repo, so it stays retryable for all tools. Rationale recorded in REQ-002.
- **No new state**: the rejected sent-key record would conflict with the per-logical-call key
  invariant (handler comment: "the key is always present, so a key-presence gate is impossible")
  and would disable all write retries. The classification gate derives its decision from the
  current attempt's error class only.
- **Relationship to server cache**: the server-side `_duplicate_cache` remains the authority
  for post-completion duplicate dispatch (pre-send retries are safe precisely because nothing
  executed upstream); the client gate covers the complementary window the cache cannot see
  (first attempt errored/in-flight, no cache entry). The two layers are disjoint in coverage —
  recorded in the updated REQ-006 comment (REQ-005).
- **Overlap with sibling plans**: `http_transport.py`'s `RequestError` handler is also the
  target of the mcpinv003 issue (discarded `TransportError`). Compatible (different semantics),
  but sequenced: mcpinv003 lands first so the handler's error-propagation semantics are restored
  before the gate raises on them.

## Implementation steps
1. **Phase 1: Preparation / characterization baseline**
   - [ ] Run `tests/shared/test_http_transport.py` and `tests/shared/test_tool_executor_routing.py`
     unchanged to record the pre-change baseline (REQ-003, REQ-004;
     `scripts/shared/http_transport.py`, `tests/shared/test_http_transport.py`).
2. **Phase 2: Core classification gate**
   - [ ] Add the pre-send-safe whitelist and the ambiguity check to the `httpx.RequestError`
     handler, raising `TransportError` for side-effecting tools on ambiguous errors
     (REQ-001, REQ-003; `scripts/shared/http_transport.py`).
   - [ ] Gate the retryable-status branch: side-effecting tools abort on 502/503/504, 429 and
     read tools unchanged (REQ-002, REQ-004; `scripts/shared/http_transport.py`).
   - [ ] Correct the `_WRITE_TOOLS` module comment and the REQ-006 handler comment
     (REQ-005; `scripts/shared/http_transport.py`).
3. **Phase 3: Tests, docs, deployment check, and verification**
   - [ ] Add the gate unit tests and the `_WRITE_TOOLS` ↔ `dispatch._write_tools` mirror pin
     (REQ-001, REQ-002, REQ-006; `tests/shared/test_http_transport.py`).
   - [ ] Update the "Idempotency and retry" section to remove the stale key-presence claim and
     describe the classification gate (REQ-005;
     `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`).
   - [ ] Deployment validation/scripts check: confirm no new module and no config key, so
     `deploy.sh` and `config/*.toml` require no change (REQ-006;
     `scripts/shared/http_transport.py`).
   - [ ] Run the full `rules/toolchain.md` validation sequence (targeted tests, full suite,
     ruff, mypy, import-linter, bandit, diff-cover) (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/http_transport.py | Unit (injection of error classes and status responses) | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor_routing.py` | New gate tests pass; all pre-existing tests pass without modification |
| scripts/shared/http_transport.py | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; `shared` leaf contract preserved |
| tests/shared/test_http_transport.py | Regression | `uv run pytest tests/` | Full suite green; mirror pin holds |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Documentation consistency | `rules/toolchain.md` documentation consistency check (22_mcp domain) | Doc matches code behavior; stale claim removed |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New gate branches covered |

## Risks
- **Risk**: fail-closed gating removes retry resilience for side-effecting calls on ambiguous
  failures, turning previously-recovered transient write failures into surfaced
  `TransportError`s → **Mitigation**: this is the ADR-004 fail-closed stance the transport
  comment already cites; pre-send connection failures (`ConnectError`/`ProxyError`) — the common
  server-down case — keep full retry; the error message names the ambiguity cause and the
  existing transport-error counters/health registry continue to record the failure.
- **Risk**: `_WRITE_TOOLS` drifting out of sync with `dispatch._write_tools` would gate the
  wrong tool set → **Mitigation**: mirror pin test (Tests, REQ-006) plus startup
  `check_write_classification()` (ADR-003 INV-03).
- **Risk**: same-handler-region conflict with the mcpinv003 fix (discarded `TransportError`) →
  **Mitigation**: sequenced implementation (mcpinv003 first, then this Plan's Phase 2); overlap
  recorded as Compatible in both Plans.
- **Risk**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` is high-churn (24 commits/30d) and
  also a candidate edit target of sibling mcpinv plans → **Mitigation**: keep the edit scoped to
  the "Idempotency and retry" section; rebase before implementing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | — | 20261028-110204 |  |
| 2 | Phase 2: core classification gate | Completed | — | 20261028-110204 |  |
| 3 | Phase 3: tests, docs, deployment check, verification | Completed | — | 20261028-110204 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-004925_01_scripts_shared_http_transport.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-004925_02_tests_shared_test_http_transport.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-004925_03_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-001245_mcpinv001_mcp-write-idempotency-backstop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-102512
- **Related target files**: scripts/shared/http_transport.py, tests/shared/test_http_transport.py, docs/22_mcp/mcp_03_01_dispatch-and-routing.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (post-send ambiguous retry window); verified against `HttpTransport.call()` error handlers | scripts/shared/http_transport.py | Phase 2 | AC-1 | Ambiguous-RequestError unit tests | Confirmed by repository evidence |
| REQ-002 | Problem; server 502/503 post-dispatch emitters | scripts/shared/http_transport.py | Phase 2 | AC-2 | Status-gate and 429-boundary unit tests | Confirmed by repository evidence |
| REQ-003 | Constraints ("common case" preservation); existing ConnectError-based tests | scripts/shared/http_transport.py | Phase 2 | AC-3 | Existing tests pass unchanged | Confirmed by repository evidence |
| REQ-004 | Out of Scope (read tools); Issue AC "Read tools are unaffected" | scripts/shared/http_transport.py | Phase 2 | AC-4 | Read-tool unit tests | Confirmed by repository evidence |
| REQ-005 | Documentation Impact (REQ-006 comment block); stale doc bullet | scripts/shared/http_transport.py | Phase 2 | AC-5 | Comment/doc consistency review | Confirmed by repository evidence |
| REQ-005 | Documentation Impact; stale "Idempotency and retry" bullet | docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Phase 3 | AC-5 | 22_mcp documentation consistency check | Confirmed by repository evidence |
| REQ-006 | Scope amendments (no sent-key record, no toggle); handler comment invariant | scripts/shared/http_transport.py | Phase 2 | AC-6 | Mirror pin test + lint-imports | Derived from confirmed evidence |
| REQ-006 | Testing Expectations extended with mirror pin | tests/shared/test_http_transport.py | Phase 3 | AC-6 | Mirror pin unit test | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-004925 -->