# Plan for healthcascade001 — Tool-level "not found" and "forbidden" results trip the MCP server health circuit

## Goal
Stop ordinary tool outcomes reported by MCP servers as HTTP 4xx (`404` file-not-found, `403` path-outside-allowed-directory, and related) from counting as server-health failures, so that a model probing nonexistent or disallowed paths no longer self-inflicts a 30-second cooldown that blocks every read tool of that server.

## Priority
High

## Scope
- **In-Scope**:
  - Define which `/v1/call_tool` HTTP statuses are tool-level outcomes and which are transport/health failures, and implement that classification on one side consistently (Option A: client `HttpTransport.call`; Option B: server `dispatch_tool`).
  - Route a tool-level outcome to the health registry success path (`record_success`) with `error_type="tool"` and a message carrying the server's reason, and stop writing a transport-failure diagnostic for it.
  - Keep `401`, timeouts, malformed responses, retry exhaustion, and `5xx` as transport/health failures.
  - Inventory every other MCP server's non-2xx usage and fold it into the same documented contract.
  - Update `docs/22_mcp/mcp_03_03_transport-and-health.md` to state the HTTP-status contract.
  - Add tests proving three consecutive tool-level outcomes leave the server `HEALTHY` and a following valid call is sent, and that `401`/timeout/`5xx` still count as failures.
- **Out-of-Scope**:
  - Changing `McpServerHealthRegistry` failure threshold (`3`) or half-open cooldown (`30s`) — `scripts/shared/mcp_health.py` is not modified under either option.
  - Re-classifying HTTP `200` responses carrying `is_error=true` (resolved in archived issue `issues/done/20261005-121408_trn001_...`).
  - Retry, idempotency, or dedup behavior.
  - The fail-closed write-tool guard on ambiguous `502/503/504` statuses (`scripts/shared/http_transport.py::_WRITE_TOOLS` gate).
- **Dependencies**: `N/A: none`. The archived `trn001` issue is background only. No open issue or plan targets `scripts/shared/http_transport.py` or `scripts/shared/mcp_health.py` for this behavior.

## Background
The file MCP servers map domain exceptions to HTTP error statuses through FastAPI exception handlers registered in `scripts/mcp_servers/file/common.py`: `_on_auth_error` → `403` (`FileAuthorizationError`, raised when a path is outside the allowed directories), `_on_not_found` → `404` (`FileNotFoundError`, raised when a target does not exist), `_on_validation_error` → `422` (`FileValidationError`). `read_server.py`, `write_server.py`, and `delete_server.py` register these three handlers identically (checked in Step 3).

On the client, `HttpTransport.call()` in `scripts/shared/http_transport.py` calls `resp.raise_for_status()` for any status outside the retryable set `{429, 502, 503, 504}` and converts the resulting `httpx.HTTPStatusError` unconditionally into a `TransportError` (checked in Step 2). `ToolTransportInvoker._invoke_and_record` catches `TransportError` and calls `_record_transport_error`, which invokes `McpServerHealthRegistry.record_failure` (threshold `3`, cooldown `30s`). Three such results mark the server `UNAVAILABLE`; while unavailable, `_check_health` rejects the call before any HTTP request and returns an availability hint (`retry_after_seconds=30`).

`dispatch_tool` in `scripts/mcp_servers/dispatch.py` converts only `ValueError` handler exceptions into a `200` response with `is_error=true` (line 434); `FileNotFoundError` (`OSError`) and `FileAuthorizationError` (`RuntimeError`) are re-raised by its generic `except Exception` (line 450-460) and therefore reach the FastAPI handlers as `404`/`403`. (`FileValidationError` is a `ValueError`, so it is answered first with `200`; its `422` handler is effectively unreachable for tool calls.)

The related archived issue `issues/done/20261005-121408_trn001_...` fixed the classification of HTTP `200` responses carrying `is_error=true` (that path already yields `error_type="tool"` and calls `record_success` per `scripts/shared/transport_dto.py::from_transport` and `ToolTransportInvoker._record_success`). This issue is the same principle for tool outcomes the server signals with a `4xx` status, which that fix did not cover.

## Problem
A model that guesses file paths produces ordinary `404`/`403` responses; each is classified as a transport failure and counted toward the health circuit. Consequences:
- Normal probing blocks all read tools of the server for the `30s` cooldown, including reads of valid files.
- Each result also writes a transport-failure diagnostic (`tool_runner.py` `save_transport_failure` fires for `error_type="transport"`), and counts toward the per-server unavailable-repeat guard (`scripts/agent/tool_loop_guard.py::scan_unavailable_repeat`, gated by `tool_empty_result_max_repeats`, default `0` = disabled).
- Parallel reads in one round can reach three failures within a single round.

Reproduction is reachable by unit test: an `HttpTransport` backed by an `httpx.MockTransport` that answers a missing-path read with `404` and everything else with a normal `200` result drives three `TransportError` (`error_type="transport"`) results and a subsequent `UNAVAILABLE` rejection with zero HTTP requests. Verified by code trace in Step 2; the real servers were not started.

## Reason for Change
The health circuit exists to detect a sick server. Here it is driven by the model's own mistakes against a healthy server, producing a self-inflicted outage of the read tools for `30s` at a time. This is a normal-use runtime failure, not an edge case, and it degrades a working server based on client-side evidence that the server itself is fine.

## Implementation Intent
Separate "the server is unhealthy" from "the server answered that this request is not possible." Two mutually exclusive approaches; implement exactly one (see Design):
- **Option A (client-side)**: In `HttpTransport.call()`, recognize a defined set of tool-level statuses and, instead of raising `TransportError`, parse the response body into a `ToolCallResult` with `is_error=True`, `error_type="tool"`, and the server's reason, returning it through the success path (`record_success`). Everything else stays `TransportError`.
- **Option B (server-side)**: Make `dispatch_tool` convert the file-domain outcome exceptions (`FileNotFoundError`, `FileAuthorizationError`, `FileValidationError`) into `DispatchResult(is_error=true)` (HTTP `200`), so the client already-classifies them as tool errors post-`trn001`. The client is unchanged.

Both options require the same documented contract on which statuses are tool-level vs transport, and both leave `mcp_health.py` untouched.

## Requirements
- `REQ-001`: A `/v1/call_tool` response whose status is in the agreed tool-level set MUST NOT raise `TransportError`; it MUST return a `ToolCallResult` with `is_error=True`, `error_type="tool"`, and output carrying the server's reason.
- `REQ-002`: A tool-level outcome MUST advance the health registry via the success path (`record_success`) and MUST NOT call `record_failure` or increment `stat_transport_errors`.
- `REQ-003`: `401`, timeouts (`httpx.TimeoutException`), malformed responses (`ValueError` in body parsing), retry exhaustion, and `5xx` MUST continue to raise `TransportError` and advance `record_failure`.
- `REQ-004`: The fail-closed write-tool guard on ambiguous `502/503/504` statuses MUST be preserved unchanged.
- `REQ-005`: Every MCP server's non-2xx usage MUST be inventoried and reconciled with the contract; servers that emit a tool-level status outside the agreed set MUST be covered by the same classification.
- `REQ-006`: `docs/22_mcp/mcp_03_03_transport-and-health.md` MUST state the HTTP-status contract (which statuses are tool-level vs transport) and why.
- `REQ-007`: Tests MUST prove three consecutive tool-level outcomes leave the server `HEALTHY` and a following valid call is sent, and that `401`/timeout/`5xx` still produce transport/health failures.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified` under `issue-to-plan` Step 8's Implementation Target Files Validation — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)). Both option groups below are mutually exclusive (see Unknowns `UNK-01` and the Design section): exactly one option is implemented; the unselected option's rows exist and require modification but are NOT modified. `mcp_health.py` is intentionally absent (health registry untouched under both options).

This table is the canonical, frozen source of implementation scope for this Plan. Only **ONE** of Option A or Option B is implemented; the owner selects one at the plan-to-implementation-procedure gate (see Unknowns `UNK-01` and the Design section). Rows are grouped by option; the unselected option's rows are not modified.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/http_transport.py` | Modify (Option A) | Classify tool-level statuses in `call()`; parse body into a tool error result instead of raising `TransportError` for the agreed statuses; preserve the write-tool `502/503/504` gate. | REQ-001, REQ-003, REQ-004 | `raise_for_status()` + `HTTPStatusError`→`TransportError` path at the non-retryable branch; `_WRITE_TOOLS` ambiguous-status gate; `_RETRYABLE_STATUS={429,502,503,504}` | `tests/shared/test_http_transport.py` | Verified (checked in Step 3) |
| `tests/shared/test_http_transport.py` | Modify (Option A) | Add cases for `403`/`404`/`422` returning a tool error result (not `TransportError`); keep existing `5xx` `TransportError` assertions. | REQ-001, REQ-007 | Existing `test_ambiguous_status_not_retried_for_write_tool` parametrizes `{502,503,504}` and asserts `TransportError` — unaffected by a 4xx-only change | `tests/shared/test_http_transport.py` | Verified (checked in Step 3) |
| `tests/shared/test_tool_transport_invoker.py` | Modify (Option A) | Add a case: three tool-level outcomes leave the registry `HEALTHY` and a subsequent valid call is dispatched; `401`/`5xx` still call `record_failure`. | REQ-002, REQ-007 | `_record_transport_error`→`record_failure`; `_record_success`→`record_success`; threshold/cooldown in `mcp_health.py` | `tests/shared/test_tool_transport_invoker.py` | Verified (checked in Step 3) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify (both) | State the HTTP-status contract (tool-level set vs transport set) and the record_success/record_failure routing. | REQ-006 | Line 26 currently states "non-2xx HTTP ... raise a TransportError"; line 31 defines tool-vs-transport health routing | `docs/22_mcp/mcp_03_03_transport-and-health.md` | Verified (checked in Step 2) |
| `scripts/mcp_servers/dispatch.py` | Modify (Option B) | Convert `FileNotFoundError`/`FileAuthorizationError`/`FileValidationError` handler exceptions to `DispatchResult(is_error=true)` before the generic re-raise; keep all other exceptions propagating. | REQ-001, REQ-003 | `except ValueError` → `200 is_error=true` (line 434); `except Exception` re-raises (line 450-460); docstring documents "raises for non-ValueError" | `tests/mcp_servers/test_mcp_dispatch.py` | Verified (checked in Step 3) |
| `tests/mcp_servers/test_mcp_dispatch.py` | Modify (Option B) | Assert file-domain outcome exceptions become `is_error=true` dispatch results rather than propagating. | REQ-001, REQ-007 | Referenced by `dispatch.py` docstring as the owning test | `tests/mcp_servers/test_mcp_dispatch.py` | Verified (checked in Step 3) |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. No directory, glob, component, file group, or vague phrase appears as a row.
- `mcp_health.py` is intentionally absent: no row modifies the health registry (Constraints; REQ-000-negation).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/tool_transport_invoker.py` | `_record_success`/`_record_transport_error` define the success/failure routing the change must respect; `_check_health` defines the unavailable gate | REQ-002, REQ-003 |
| `scripts/shared/mcp_health.py` | Confirms threshold=`3`, cooldown=`30s`, and that `record_success`/`record_failure` are the only state transitions — must stay untouched | Constraints, REQ-003 |
| `scripts/shared/transport_dto.py` | `from_transport()` already yields `error_type="tool"` for HTTP `200 is_error=true` (the `trn001` fix); `ToolCallResult` shape to reuse for Option A | REQ-001 |
| `scripts/mcp_servers/file/common.py` | Defines the `403`/`404`/`422` handlers and the file-domain exception types | REQ-005 |
| `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py` | Confirm identical handler registration across the three file servers | REQ-005 |
| `scripts/agent/tool_loop_guard.py` | `scan_unavailable_repeat` and the `tool_empty_result_max_repeats` guard — to document the secondary consequence | Problem |
| `scripts/mcp_servers/github/exception_handlers.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/cicd/exception_handlers.py`, `scripts/mcp_servers/mdq/mdq_server.py` | Inventory each server's non-2xx usage for the contract (REQ-005) | REQ-005 |

## Acceptance Criteria
- **AC-001** (REQ-001, REQ-006): Three consecutive file-not-found or outside-allowed-directory results do not change the server's health state and do not block the next valid call.
- **AC-002** (REQ-001): Tool-level outcomes are reported to the model as tool errors (`error_type="tool"`) with a message carrying the server's reason.
- **AC-003** (REQ-003): A `401`, a timeout, a malformed response, and a `5xx` still produce transport failures and health failures.
- **AC-004** (REQ-006): The documentation states the HTTP-status contract between the servers and the client.
- **AC-005** (REQ-007): The new tests fail on the current code and pass after the change.

## Tests
- Unit test for `HttpTransport.call` (Option A) / `dispatch_tool` (Option B) with `httpx.MockTransport` and a real `McpServerHealthRegistry`, proving the tool-level/transport split (`REQ-001`, `REQ-007`).
- Invoker-level test: three consecutive tool-level outcomes leave the registry `HEALTHY`; a subsequent valid call is dispatched; `401`/`5xx` still call `record_failure` (`REQ-002`, `REQ-007`).
- Server-side test (Option B only): a missing file and an outside-directory path produce an `is_error=true` dispatch result using the app's test client with a temporary allowed directory.
- Regression: run `tests/shared`, `tests/mcp_servers`, and the MCP integration tests; run `ruff` and `mypy --no-namespace-packages` on touched files (`REQ-007`).
- Existing `tests/shared/test_http_transport.py::test_ambiguous_status_not_retried_for_write_tool` (parametrized `{502,503,504}`) must keep passing; it asserts `TransportError` for `5xx` only, so a 4xx-only change does not break it (`Confirmed by repository evidence`, checked in Step 3).

## Documentation Impact
Update `docs/22_mcp/mcp_03_03_transport-and-health.md` to state which `/v1/call_tool` statuses are tool-level outcomes and which are transport failures, and why (maps to `REQ-006`). Name the target via `docs/00_index.md` Document References by Task / `routing.md` Docs mapping. Describe the policy and its consequences only; do not copy concrete thresholds (`skills/DESIGN.md` No concrete configuration values). Any other page repeating "non-2xx is a transport failure" must be reconciled.

## Assumptions
- The standard HTTP semantic boundary holds: `4xx` (except `401`) indicates a client/tool-level problem the server handled correctly, while `5xx` indicates server illness. This is the basis of the status classification and is falsifiable by a server that returns `4xx` for a genuine server fault.
- The client is the single consumer that feeds the health registry, so classifying on one side yields one observable behavior for all servers.
- `403` denotes "forbidden / outside allowed directory" (tool-level) across the file, github, web_search, and shell servers, distinct from `401` auth failures (transport). Falsifiable if any server uses `403` for an auth fault.
- Option A does not need to touch the write-tool fail-closed guard because that guard concerns ambiguous `502/503/504` (`6xx`-class post-send ambiguity), not `4xx` outcomes where nothing executed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which side owns the classification: client (`HttpTransport.call`, Option A) or server (`dispatch_tool`, Option B)? The issue leaves this to the owner; both options are fully specified below. | Decided by product preference, not missing evidence. | Owner reviews the Design section (both options + recommendation) and selects at the plan-to-implementation-procedure gate; only the selected option's rows are modified. | False |
| UNK-02 | Exact tool-level status set and whether any server uses a listed status for a genuine server fault. Evidence: file servers emit `403/404/422`; github `400/403/404/409/500/502`; git `500`; web_search `403/422/502`; shell `403/422`; rag_pipeline `503`; cicd/mdq use a dynamic `status_code`. | Per-status intent is server-specific; the contract fixes it by status, not by server. | Subsumed by UNK-01: the chosen option encodes the set (proposal: tool-level `{400,403,404,409,422}`, transport `401` + all `5xx`). | False |
| UNK-03 | Whether the per-server unavailable-repeat guard (`tool_empty_result_max_repeats`, default `0`) actually stops a turn in this case. | Guard exists (`tool_loop_guard.py::scan_unavailable_repeat`) but is disabled by default config. | Documented: with the default the guard is off, so the primary harm is the cooldown self-outage, not the guard. No code change required. | False |

Unknown status updates (plan-to-implementation-procedure gate, 2026-11-02):
- UNK-01 resolved by owner decision 2026-11-02: **Option A** selected — classification lives in
  `scripts/shared/http_transport.py`'s `call()`. Evidence: one shared-module change against the
  Plan's own blast-radius table; the validation matrix already names the `httpx.MockTransport`
  harness for Option A; Option B would alter the shared dispatcher used by every MCP server.
  Resulting behavior: Option B rows (`scripts/mcp_servers/dispatch.py`,
  `tests/mcp_servers/test_mcp_dispatch.py`) are NOT modified and receive no procedure documents.
- UNK-02 resolved with the same decision, adopting the Plan's proposed contract: tool-level
  statuses `{400, 403, 404, 409, 422}`; transport/health failures = `401` + all `5xx` +
  timeouts + malformed responses + retry exhaustion. Evidence: the REQ-005 server inventory
  shows file servers emit `403/404/422` only for file-domain outcomes; no surveyed server uses
  `400`/`409`/`422` for a genuine transport fault (github `400/409` are API misuse outcomes).

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/http_transport.py` | Modify | Medium — two consumers (`ToolTransportInvoker`, `tool_runner.py`) and all MCP servers' reads/writes route through it | High (9 commits / 30d) | Shared leaf layer; multiple owners | not applicable (rsynced) |
| `scripts/shared/tool_transport_invoker.py` | Reference only (not modified) | — | High (9 commits / 30d) | Shared leaf layer | not applicable (rsynced) |
| `scripts/mcp_servers/dispatch.py` | Modify (Option B only) | Medium — shared dispatcher for every MCP server | Moderate (9 commits / 90d) | Multiple server owners | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Low — documentation only | N/A | N/A | not applicable (rsynced) |

`Churn (30d)` and `Bus Factor` for `dispatch.py` are partial (90d shown; 30d historical analysis did not isolate it above). `tool_transport_invoker.py` is a Reference File, not a target, so it appears here only for context.

## Design
This is a cross-boundary contract between the client transport layer (`shared`) and the MCP servers (`mcp_servers`). The `shared` layer is a leaf (must not import `agent`/`mcp_servers`/`rag`/`db`; `.importlinter` contract `shared-is-leaf`, verified `KEPT` by `lint-imports`), so a client-side change stays within one layer and touches no import contract. Both options were analyzed; only one is implemented.

### Decision: which side owns the classification (UNK-01)
**Recommendation: Option A (client-side).**

- **Option A — client classification (`HttpTransport.call`)**
  - *What changes*: Before `raise_for_status()`, test whether `resp.status_code` is in the agreed tool-level set. If yes, parse the body (`{"detail": ...}` for server error handlers; `{"result": ...}` for normal results) into a `ToolCallResult(is_error=True, error_type="tool", output=<reason>)` and return it through the existing success path. If no, keep the current `raise_for_status()` → `TransportError` path.
  - *Compatibility impact*: Single-file change in the `shared` leaf layer. Does not alter `dispatch_tool`'s documented "raises for non-ValueError" contract, so other servers' `4xx`/`5xx` semantics (github `409`, git `500`, etc.) are preserved for any other consumer (e.g. `/mcp status`, audit). Preserves the write-tool `502/503/504` fail-closed gate. Risk: the client now trusts the contract that these statuses mean tool-level; a genuine server returning `404` for an internal fault would be misread as tool-level — mitigated by the standard `4xx`/`5xx` boundary assumption. Body parsing must handle a missing/invalid `detail`/`result` field without raising (currently `_parse_http_response` raises `ValueError` on a missing `result`, which would otherwise re-enter the transport path).
  - *Blast radius*: `tool_runner.py` (audit/diagnostics) and `ToolTransportInvoker` both consume `HttpTransport`; a tool-level result flows through `record_success`, so no bogus transport-failure diagnostic is written.

- **Option B — server classification (`dispatch_tool`)**
  - *What changes*: In `dispatch_tool`, add an `except` branch for the file-domain outcome exceptions (`FileNotFoundError`, `FileAuthorizationError`, `FileValidationError`) that returns `DispatchResult(is_error=true)` instead of re-raising. The client is unchanged and already maps `200 is_error=true` → `error_type="tool"` → `record_success` (post-`trn001`).
  - *Compatibility impact*: Broader. `dispatch_tool` is shared by every MCP server; changing its exception contract ("raises for non-ValueError") affects github/git/etc., which currently rely on exceptions propagating to their own `4xx`/`5xx` handlers. Must scope the new branch to the file-domain exception types only, and must keep the durable-dedup `record_failed` bookkeeping for the converted outcome. Higher refactor risk; requires the file-domain exception classes to be importable into `dispatch.py` (crossing within the `mcp_servers` layer, allowed).
  - *Blast radius*: All servers sharing `dispatch_tool`; the client needs no change.

- *Why A over B*: contained to one `shared` file, no change to the shared dispatcher's documented contract, each server keeps its own status semantics, and the health registry is fed correctly through the existing success path. B is acceptable only if the owner prefers the classification to live at the source of the outcome; it costs a broader, higher-risk change to `dispatch.py`.

### Decision: the tool-level status set (UNK-02)
Proposal (record in the plan/issue before editing, per the issue's AI Implementation Instruction): tool-level = `{400, 403, 404, 409, 422}`; transport = `401` plus all `5xx` (`500/502/503/504`), timeouts, malformed bodies, and retry exhaustion. This matches the standard client-error vs server-error boundary and covers every status observed in the server inventory. `401` stays transport so a wrong token remains visible. If the owner selects Option B, the set governs which server-side outcomes convert to `200 is_error=true`; statuses outside the set keep their current handler.

### Decision: health registry untouched
Neither option modifies `scripts/shared/mcp_health.py`. Option A routes tool-level outcomes through `record_success` (existing method); Option B leaves the client and registry unchanged. This satisfies the issue constraint and the AI Implementation Instruction to stop and report if a registry change were required (it is not).

## Implementation steps
Each step cites the exact file path(s) it touches by referencing rows of `Implementation Target Files` above. **Select exactly one option (UNK-01); implement only that option's steps.**

1. **Phase 1: Contract decision and signature (UNK-01, UNK-02 resolved by owner)**
   - [ ] Record the selected option and the tool-level status set in the issue/plan; document the contract in `docs/22_mcp/mcp_03_03_transport-and-health.md` skeleton (REQ-006).
2. **Phase 2: Core logic (per selected option)**
   - Option A:
     - [ ] `scripts/shared/http_transport.py`: add the tool-level status check before `raise_for_status()`; parse body into a tool error result; keep `401`/`5xx`/timeout/malformed as `TransportError`; preserve the write-tool `502/503/504` gate (`REQ-001`, `REQ-003`, `REQ-004`).
     - [ ] Add body-parsing safety for missing/invalid `detail`/`result` so a tool-level response never re-enters the transport path (`REQ-001`).
   - Option B:
     - [ ] `scripts/mcp_servers/dispatch.py`: add an `except` branch converting `FileNotFoundError`/`FileAuthorizationError`/`FileValidationError` to `DispatchResult(is_error=true)`, preserving dedup `record_failed` bookkeeping and keeping all other exceptions propagating (`REQ-001`).
3. **Phase 3: Tests**
   - [ ] `tests/shared/test_http_transport.py` (Option A) / `tests/mcp_servers/test_mcp_dispatch.py` (Option B): assert the tool-level/transport split (`REQ-001`).
   - [ ] `tests/shared/test_tool_transport_invoker.py`: three tool-level outcomes leave the registry `HEALTHY`; a valid call is dispatched; `401`/`5xx` still call `record_failure` (`REQ-002`, `REQ-007`).
4. **Phase 4: Documentation**
   - [ ] `docs/22_mcp/mcp_03_03_transport-and-health.md`: state the HTTP-status contract and the `record_success`/`record_failure` routing (`REQ-006`).
5. **Phase 5: Server inventory reconciliation (REQ-005)**
   - [ ] Confirm every other MCP server's non-2xx usage falls inside the agreed contract; if a server emits a tool-level status outside the set, extend the documented contract (no per-server code change needed under Option A; under Option B, confirm the server's dispatch path converts it).
6. **Phase 6: Deployment & Verification**
   - [ ] Run `ruff` and `mypy --no-namespace-packages` on touched files; run `tests/shared`, `tests/mcp_servers`, and the MCP integration tests; confirm `lint-imports` still `KEPT` (`REQ-007`).
   - [ ] Hand-off to `skills/deploy/SKILL.md`: the change is committed and pushed first; deploying is the user's decision (approval gate). `scripts/` changes are rsynced (`deploy.sh Impact: not applicable (rsynced)`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/http_transport.py` (Option A) | Unit with `httpx.MockTransport` | `uv run pytest tests/shared/test_http_transport.py -q -p no:cacheprovider` | `403`/`404`/`422` return a tool error result; `5xx`/`401` raise `TransportError`; `test_ambiguous_status_not_retried_for_write_tool` passes |
| `scripts/mcp_servers/dispatch.py` (Option B) | Unit with app test client + temporary allowed dir | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -q -p no:cacheprovider` | Missing/outside paths yield `is_error=true` dispatch results; other exceptions still propagate |
| `scripts/shared/tool_transport_invoker.py` routing | Unit with real `McpServerHealthRegistry` | `uv run pytest tests/shared/test_tool_transport_invoker.py -q -p no:cacheprovider` | Three tool-level outcomes → `HEALTHY`; `401`/`5xx` → `record_failure` |
| Full regression | Integration | `uv run pytest tests/shared tests/mcp_servers tests/integration -q -p no:cacheprovider -p no:randomly` | No new failures vs baseline |
| Static | Lint / type | `uv run ruff check <touched>`, `uv run mypy --no-namespace-packages <touched>` | Clean on touched files |

## Risks
- **Risk**: Option A masks a genuine server that returns `4xx` for an internal fault as a tool-level outcome, hiding a real problem. → **Mitigation**: restrict the tool-level set to the standard client-error statuses (`400/403/404/409/422`) and keep all `5xx` as transport; document the `4xx`/`5xx` boundary assumption so a future server violating it is caught by the transport path.
- **Risk**: Option A body parsing raises on an unexpected body shape and re-enters the transport path. → **Mitigation**: parse defensively (default output to the raw detail string when `detail`/`result` is absent or non-string); cover with a test for a malformed tool-level body.
- **Risk**: Option B changes `dispatch_tool`'s documented "raises for non-ValueError" contract and affects every shared server. → **Mitigation**: scope the new branch to the file-domain exception types only; verify github/git/etc. still reach their own handlers for statuses outside the converted set; prefer Option A unless the owner explicitly prefers server-side.
- **Risk**: `scripts/shared/http_transport.py` and `scripts/shared/tool_transport_invoker.py` are high-churn (9 commits / 30d); merge conflict surface. → **Mitigation**: small, independently revertable phases; rebase onto upstream before merging; `lint-imports` re-check.
- **Risk**: An existing test pins a `4xx` to `TransportError`. → **Mitigation**: Step 3 confirmed the only parametrized `TransportError` status test uses `{502,503,504}` (`5xx`); scan all `tests/shared` and `tests/integration` for a `4xx` assertion before finalizing and update only if a legitimate pin exists.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Contract decision and signature (option + status set) | Pending | — | — | Blocked on owner selection (UNK-01/UNK-02); non-blocking, recorded here |
| 2 | Core logic (Option A `http_transport.py` or Option B `dispatch.py`) | In Progress | — | — | One option only |
| 3 | Tests for the tool-level/transport split and health routing | In Progress | — | — |  |
| 4 | Documentation of the HTTP-status contract | In Progress | — | — |  |
| 5 | Server inventory reconciliation | Pending | — | — |  |
| 6 | Deployment & verification (ruff/mypy/regression) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132712_01_scripts_shared_http_transport.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-132712_02_tests_shared_test_http_transport.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-132712_03_tests_shared_test_tool_transport_invoker.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-132712_04_docs_22_mcp_mcp_03_03_transport-and-health.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261101-073450_healthcascade001_tool-4xx-trips-circuit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-141054
- **Related target files**: scripts/shared/http_transport.py, tests/shared/test_http_transport.py, tests/shared/test_tool_transport_invoker.py, docs/22_mcp/mcp_03_03_transport-and-health.md, scripts/mcp_servers/dispatch.py, tests/mcp_servers/test_mcp_dispatch.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary, Implementation Intent, Required Changes | `scripts/shared/http_transport.py` (Option A) / `scripts/mcp_servers/dispatch.py` (Option B) | Step 2 | AC-001, AC-002 | Unit split test | Confirmed by repository evidence |
| REQ-002 | Problem, Required Changes | `scripts/shared/tool_transport_invoker.py` (reference) | Step 2/3 | AC-001 | Invoker health-routing test | Confirmed by repository evidence |
| REQ-003 | Constraints, Acceptance Criteria | `scripts/shared/http_transport.py` (Option A) | Step 2 | AC-003 | `401`/timeout/`5xx` test; existing `5xx` assertion | Confirmed by repository evidence |
| REQ-004 | Constraints | `scripts/shared/http_transport.py` | Step 2 | AC-003 | write-tool ambiguous-status test unchanged | Confirmed by repository evidence |
| REQ-005 | Unresolved Questions, Required Changes | Reference Files (other servers) | Step 5 | — | Server inventory | Derived from confirmed evidence |
| REQ-006 | Documentation Impact | `docs/22_mcp/mcp_03_03_transport-and-health.md` | Step 4 | AC-004 | Doc review | Confirmed by repository evidence |
| REQ-007 | Testing Expectations, Acceptance Criteria | all touched files | Step 6 | AC-005 | Full regression + ruff/mypy | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132712 -->