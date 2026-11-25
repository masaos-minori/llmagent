## Goal
- Carry the MCP dispatcher's `dedup_state` through the HTTP transport result (`ToolCallResult`) into the Agent `tool_exec` audit event, and add a `turn_id` field plus the workflow task id to the `tool_approval` and `tool_exec` audit events, so that request, session, workflow, task, turn, and logical call identifiers can be correlated directly. Verified by an end-to-end test over the Agent audit line and the MCP response body.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add an optional `dedup_state` field to `ToolCallResult` and parse it from successful responses, tool-level error responses (HTTP 200 with `is_error: true`), and tolerant tool-level-status bodies (400/403/404/409/422).
  - Pass `result.dedup_state` from the tool runner to `audit_tool_exec` (the audit writer already serializes it when non-empty; no caller passes it today).
  - Add `turn_id` to `ToolApprovalEvent` and `ToolExecEvent`, and populate the workflow task id (`ctx.workflow.current_task_id`) on both events, per the UNK-01 decision (option B, 20261125).
  - Add the logical call id, request id, task id, and turn id to the `transport_failure` diagnostic record (additive JSON keys only).
  - Extract the audit-write and diagnostics-write code out of `scripts/agent/tool_runner.py` into a new module, because the file is 23736 B against the 24576 B module size gate and the pending mcpai004/mcpai005 procedures add code to it (size re-measured at Step 8 re-run on 20261125).
  - Document the audit field definitions and the backward-compatibility note.
- **Out-of-Scope**:
  - Defining or changing the dedup state set, the dedup key, or the server-side dispatcher (atomic dedup state machine and logical idempotency key work are closed).
  - Changing the `tool_call_state` SQLite schema; no schema, DDL, or migration change is planned.
  - Redaction policy for the free-text `error` field of `transport_failure` diagnostics (existing behavior; see UNK-03).
  - The final design-docs sweep owned by the MCP design-docs-update issue (mcpai012); this Plan updates only the audit field definitions and the compatibility note.
  - Changing `turn_start` / `turn_end` / `workflow_start` / `stage_completed` events (see UNK-02).
- **Dependencies**: The dedup state machine (mcpai001), the logical idempotency key (mcpai004), and the approval-grant/intent-state work (mcpdl001) are closed (their Issues are archived). Related, not blocking: the GitHub write retry policy (mcpai006). Sequencing against pending implementation procedures of the structured execution context Plan (mcpai005) and the logical idempotency key Plan (mcpai004) is recorded in Assumptions.

## Background
The consolidated review backlog (Issue 7 of `memo-issue.md`) reported that the MCP response can carry a dedup state while the Agent audit cannot. Current code (checked in Step 2): `CallToolResponse.dedup_state` is defined in `scripts/mcp_servers/models.py` and set by `scripts/mcp_servers/dispatch.py` and `scripts/mcp_servers/dedup_gate.py`; `HttpTransport._parse_http_response` reads only `result` and `is_error`; `ToolCallResult` has no dedup field; `audit_tool_exec` accepts `dedup_state` but `tool_runner.execute_one_tool_call` never passes it.

## Problem
1. The HTTP transport drops `dedup_state`, so an operator cannot tell from the Agent audit whether a result was executed, replayed, duplicated, in progress, refused, or affected by a store error without reading server logs.
2. The `tool_approval` and `tool_exec` events place the turn id in `task_id` (`task_id=ctx.turn.current_turn_id`), and `task_linkage` on `tool_exec` is never populated, so the workflow task id is absent from both events.
3. The `transport_failure` diagnostic record carries no call identity, so it cannot be joined to the audit line or the `tool_call_state` row.

## Reason for Change
Operators correlate a call across audit, state, and server logs by hand. No time-sensitive trigger is known. The change is additive observability.

## Implementation Intent
Add fields additively, with defaults that keep older records and older server responses readable. Treat `dedup_state` as an opaque string in `shared` (an import-linter leaf must not import `mcp_servers`). Keep the writer's existing "serialize `dedup_state` only when non-empty" rule. Extract the audit bridge from `tool_runner.py` so the size gate holds.

## Requirements
- `REQ-001`: `ToolCallResult` MUST carry an optional `dedup_state: str = ""`, appended after the existing fields, and `ToolCallResult.from_transport` MUST accept it.
- `REQ-002`: `HttpTransport` MUST parse `dedup_state` from a successful 200 response, from a 200 response with `is_error: true`, and tolerantly from tool-level-status (400/403/404/409/422) bodies; a missing or non-string value MUST yield `""` and MUST NOT raise or change error classification. The transport MUST NOT validate the value against a vocabulary.
- `REQ-003`: The Agent MUST pass `result.dedup_state` to `audit_tool_exec` for every executed call, so a `tool_exec` event records `duplicate_hit`, `in_progress`, `replayed`, `store_error`, `reconciliation_required`, `outcome_unknown`, `replay_unavailable`, and `lease_conflict` when the server reports them.
- `REQ-004`: `ToolApprovalEvent` and `ToolExecEvent` MUST gain `turn_id` (the value of `ctx.turn.current_turn_id`, `""` when unset) and MUST record the workflow task id (`ctx.workflow.current_task_id`, `""` when unset) in `task_linkage`; `task_id` keeps its current value (the turn id) per the UNK-01 decision (option B, 20261125).
- `REQ-005`: The logical call id MUST be the same value in the approval event, the `tool_call_state` row, the `tool_exec` event, and the `transport_failure` diagnostic record; the diagnostic record MUST gain `call_id`, `request_id`, `task_id`, and `turn_id` keys, and no audit or diagnostic record gains raw arguments, credentials, signed URLs, or raw exceptions beyond what it records today.
- `REQ-006`: Every new field MUST be optional with a default, so records written before this change remain parseable; the compatibility rule MUST be documented.
- `REQ-007`: `scripts/agent/tool_runner.py` MUST stay under the 24576 B module size gate after the change, by moving the `tool_exec` audit call and the transport-failure diagnostics write into a new module.
- `REQ-008`: The audit field definitions (`dedup_state`, `turn_id`, `task_linkage`, `task_id`, `idempotency_key`) and the compatibility note MUST be documented, and the stale statements in the tracing document MUST be corrected.
- `REQ-009`: An end-to-end test MUST show request id, session id, logical call id, workflow task id, and turn id correlating between a real `HttpTransport` response and the resulting Agent audit lines.

## Implementation Target Files
**Freeze status**: Frozen (UNK-01 resolved on 20261125 by owner decision, option B; Step 8 re-run on 20261125)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/transport_dto.py` | Add `dedup_state` to `ToolCallResult` and `from_transport` | The result DTO has no dedup field; `from_transport` takes only output, is_error, request_id | REQ-001; AC-1, AC-2 | `ToolCallResult` fields end at `dispatch_stage` (`rg -n dedup_state scripts/shared` returns nothing) (checked in Step 3) | `tests/shared/test_transport_dto.py` | Verified |
| `scripts/shared/http_transport.py` | Parse `dedup_state` in `_parse_http_response` and `_tool_error_result` | Both parsers build the result from `result`/`is_error` only | REQ-002; AC-1, AC-2 | `_parse_http_response` reads `result`, `is_error`, header `x-request-id`; `_tool_error_result` reads `detail`/`result` (checked in Step 3) | `tests/shared/test_http_transport.py` | Verified |
| `scripts/agent/shared/models.py` | Add `turn_id` to `ToolApprovalEvent` and `ToolExecEvent`; add `task_linkage` to `ToolApprovalEvent` | Events have only `task_id` (turn id); approval event has no workflow task field | REQ-004, REQ-006; AC-3, AC-4 | `ToolApprovalEvent` (line 13) and `ToolExecEvent` (line 39) have no `turn_id`; `ToolExecEvent.task_linkage` exists (checked in Step 3) | `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py` | Verified |
| `scripts/agent/tool_audit.py` | Populate `turn_id` and `task_linkage` from context in `audit_approval` and `audit_tool_exec` | Writers set `task_id=ctx.turn.current_turn_id`; `task_linkage` stays empty | REQ-004, REQ-005; AC-3, AC-5 | `tool_audit.py:141` and `:277` set `task_id` from the turn; `:290` takes `task_linkage` from the caller; `:295` serializes `dedup_state` when non-empty (checked in Step 2) | `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py` | Verified |
| `scripts/agent/tool_runner.py` | Replace the inline `audit_tool_exec` call and `_record_transport_failure` with calls into the new module | File is 23736 B against the 24576 B module size gate (re-measured at Step 8 re-run on 20261125; was 24544 B at plan generation); the audit call omits `dedup_state` | REQ-003, REQ-007; AC-1, AC-6 | `tool_runner.py:344` calls `audit_tool_exec` without `dedup_state` (line shifted from 362; re-checked at Step 3a on 20261125); `wc -c` = 23736 (re-checked at Step 8 re-run) | `tests/agent/test_tool_runner.py` | Verified |
| `scripts/agent/tool_result_audit.py` | Create: `record_tool_exec(ctx, name, args, result, call_id)` and `record_transport_failure(ctx, name, result, call_id)` | Extraction target that keeps `tool_runner.py` under the size gate and carries `dedup_state` and ids | REQ-003, REQ-005, REQ-007; AC-1, AC-5, AC-6 | New file; `scripts/agent/` exists and imports `agent.tool_audit` and `agent.diagnostic_store` without a cycle (checked in Step 3) | `tests/agent/test_tool_runner.py`, `tests/agent/test_dedup_audit_correlation.py` | Verified |
| `scripts/agent/diagnostic_store.py` | Add optional `call_id`, `request_id`, `task_id`, `turn_id` keyword parameters to `save_transport_failure` | The diagnostic JSON has only tool_name, server_key, error | REQ-005; AC-5 | `save_transport_failure` (line 259) builds `{tool_name, server_key, error}` into the `content` JSON blob; no schema column change (checked in Step 3) | `tests/agent/test_diagnostic_store.py` | Verified |
| `tests/shared/test_transport_dto.py` | Add default and carry cases for `dedup_state` | Pin REQ-001 | REQ-001; AC-1 | File tests `ToolCallResult.from_transport` (checked in Step 3) | itself | Verified |
| `tests/shared/test_http_transport.py` | Parser tests for every dedup state, tool-level errors, missing and non-string values | Pin REQ-002 | REQ-002; AC-1, AC-2 | `test_tool_level_status_returns_tool_error_result` and `test_tool_level_status_with_malformed_body` exist at lines 426-455 (checked in Step 3) | itself | Verified |
| `tests/agent/test_tool_audit.py` | Update the field-set pin and INV-11 tests; add `turn_id`, `task_linkage`, `dedup_state` cases | The exact payload field set is pinned at lines 385-403 | REQ-004, REQ-006; AC-3, AC-4 | `assert set(payload) == expected \| {"execution_snapshot_json"}` (checked in Step 3) | itself | Verified |
| `tests/agent/test_audit_log_format.py` | Add the new fields to the approval and exec format contracts | Row-8 contract test pins approval serialization | REQ-004, REQ-006; AC-3, AC-4 | `test_approval_event_carries_idempotency_key_field` at line 551 (line shifted from 552; re-checked at Step 3a on 20261125) | itself | Verified |
| `tests/agent/test_tool_runner.py` | Assert `dedup_state` reaches the audit line and the diagnostics record carries the ids | Pin REQ-003, REQ-005, REQ-007 | REQ-003, REQ-005; AC-1, AC-5 | File patches `save_transport_failure` and exercises `execute_one_tool_call` (checked in Step 3) | itself | Verified |
| `tests/agent/test_diagnostic_store.py` | Cover the new optional keys and the old-call-shape compatibility | Pin REQ-005, REQ-006 | REQ-005, REQ-006; AC-4, AC-5 | File covers `save_transport_failure` (checked in Step 3) | itself | Verified |
| `tests/agent/test_dedup_audit_correlation.py` | Create: end-to-end correlation test | Pin REQ-009 | REQ-009; AC-7 | New file; `tests/agent/` exists (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Correct the `dedup_state` value list and the `idempotency_key` description; add the field definitions and compatibility note | Lines 51 and 53 are stale: the value list lacks `reconciliation_required`, `outcome_unknown`, `replay_unavailable`, `in_progress`, `lease_conflict`, lists non-existent `snapshot_mismatch`, `result_truncated`, `unreplayable`; `idempotency_key` (line 53) is described as a derived workflow:task:turn:call string, but it is the logical call id (`tool_runner._logical_call_id`) | REQ-006, REQ-008; AC-4 | `rg -n "snapshot_mismatch" scripts` has no match; `dedup_gate.py` emits the current values (checked in Step 2; line numbers re-checked at Step 8 re-run) | `uv run python tools/check_docs_consistency.py` (see Validation plan) | Verified |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Describe the `dedup_state` field of `ToolCallResult` | Section 6a does not list result fields | REQ-008; AC-4 | Section 6a (line 24) states only `source` semantics (checked in Step 3) | `uv run python tools/check_docs_consistency.py` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Regenerate for the new module and changed signatures | Generated reference lists `audit_tool_exec` and `save_transport_failure` signatures | REQ-008; AC-4 | Line 168 lists `audit_tool_exec`; fallout check flagged generated blocks (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/models.py` | Defines `CallToolResponse.dedup_state` (the wire contract) | REQ-001, REQ-002 |
| `scripts/mcp_servers/dedup_gate.py` | Source of the real dedup state values and `_OWNED_STATES` | REQ-003 |
| `scripts/mcp_servers/dispatch.py` | Builds `CallToolResponse` from `DispatchResult.dedup_state` | REQ-002 |
| `scripts/shared/tool_transport_invoker.py` | Merges results with `dataclasses.replace`, which preserves the new field | REQ-003 |
| `scripts/agent/context.py` | Defines `ctx.turn.current_turn_id` and `ctx.workflow.current_task_id` | REQ-004 |
| `scripts/agent/tool_approval.py` | Calls `audit_approval`; derives identifiers from context, so no call-site change | REQ-004 |
| `scripts/agent/audit_event_emitter.py` | Emits `turn_start`/`turn_end` with `task_id` = turn id (unchanged here) | REQ-004, UNK-02 |
| `scripts/agent/workflow/tool_call_state_ops.py` | `tool_call_state` rows carry `task_id` and the logical call id as `idempotency_key` | REQ-005 |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | ADR-001 item 10 / INV-11 define `task_id` as the turn id | REQ-004, UNK-01 |
| `docs/10_adr/adr_01_index.md` | Lists INV-11 as a Blocking, test-gated invariant | REQ-004, UNK-01 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002, REQ-003): The Agent `tool_exec` audit line records `dedup_state` for each of `duplicate_hit`, `in_progress`, `replayed`, `store_error`, `reconciliation_required`, `outcome_unknown`, `replay_unavailable`, `lease_conflict`; a call with no dedup branch has no `dedup_state` key.
- AC-2 (REQ-002): A tool-level error (200 with `is_error: true`) preserves `dedup_state`; a 4xx tool-level-status body with or without `dedup_state` still returns the same error result, with `""` when absent.
- AC-3 (REQ-004): `tool_approval` and `tool_exec` lines contain `turn_id` equal to the turn id and `task_linkage` equal to the workflow task id; `task_id` remains the turn id (UNK-01 resolved: option B).
- AC-4 (REQ-006, REQ-008): Records and responses without the new fields are still readable (defaults, tests); the compatibility note and field definitions are in the tracing document.
- AC-5 (REQ-005): The approval event, `tool_call_state` row, `tool_exec` line, and `transport_failure` record carry the same logical call id; none contains raw arguments, credentials, or signed URLs.
- AC-6 (REQ-007): `uv run python tools/check_module_size.py` passes with `scripts/agent/tool_runner.py` under 24576 B.
- AC-7 (REQ-009): The correlation test joins request id, session id, call id, task, and turn between the transport response and the audit lines.

## Tests
- Parser tests for each dedup state on success and on tool-level error, for a missing field, for a non-string value, and for a tool-level-status body (REQ-002).
- DTO default and carry tests (REQ-001).
- Audit serialization tests: `turn_id`, `task_linkage`, conditional `dedup_state`, the exact field set, and older-shape compatibility (REQ-004, REQ-006).
- Runner test: `dedup_state` from a `ToolCallResult` reaches the audit line (REQ-003); the transport-failure record carries ids (REQ-005).
- End-to-end correlation test using a real `HttpTransport` over `httpx.MockTransport` returning bodies built from `mcp_servers.models.CallToolResponse` (REQ-009).
- Run `ruff`, `mypy`, and the full test suite (`rules/toolchain.md`).

## Documentation Impact
Yes (REQ-006, REQ-008). Update the audit field definitions and the compatibility note in the tracing document under `docs/22_mcp/` (via `docs/00_index.md` "Document References by Task"), the `ToolCallResult` description under `docs/40_shared/`, and the generated agent reference under `docs/23_agent/`. UNK-01 was resolved on 20261125 with option B, so no ADR-001 item 10 / INV-11 text change, no `docs/10_adr/adr_01_index.md` matrix row change, and no `docs/23_agent/` (agent_03_03, agent_06_02, agent_06_04) approval-statement change is needed: `task_id` keeps its documented meaning (the turn id) and the new fields are additive. The final design-docs sweep belongs to the mcpai012 Issue.

## Assumptions
- `task_id` handling follows option B of UNK-01, decided by the owner on 20261125 (keep `task_id` = turn id so ADR-001 INV-11 stays true; add `turn_id` and `task_linkage`). No ADR amendment is needed.
- The only repository consumers of the audit event shape are tests and docs (`rg` over `scripts/` and `tools/` found no parser of `tool_exec`/`tool_approval` fields); there is no audit schema version field. External consumers are unknown (UNK-04).
- Dedup refusals are returned as HTTP 200 with `is_error: true` and `dedup_state`, because `/v1/call_tool` raises no 4xx for them (`server.py` returns 422 only for a keyless side-effecting call, before dispatch). The tolerant 4xx parse is defensive.
- Sequencing (compatible overlap): pending implementation procedures of the structured execution context Plan (mcpai005, procedures `20261125-122426_*`) edit `transport_dto.py`, `http_transport.py`, and `tool_runner.py`, and those of the logical idempotency key Plan (mcpai004, procedures `20261125-112546_*`) edit `tool_runner.py` and `tests/agent/test_tool_runner.py`. This Plan MUST be implemented after those procedures are executed; new `ToolCallResult` fields are appended last, and `tool_runner.py` size MUST be re-measured at implementation time because those procedures also add code.
- `dataclasses.replace` in `HttpTransport.call` and `ToolTransportInvoker` preserves the new field; this is covered by a test, not assumed.
- Overlap with the cliplc006 Plan on `docs/23_agent/agent_13_reference-api-generated.md` (Step 8b overlap check, 20261125): compatible — both Plans only regenerate this generated document from their own source changes; neither hand-edits it, and the designs do not contradict each other.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The Issue requires `task_id` to come from workflow state and `turn_id` from turn state. ADR-001 item 10 and INV-11 (Blocking, test-gated by `TestAuditApprovalInv11`) define `task_id` of `tool_approval` as the turn id. Which contract holds? (A) change `task_id` to the workflow task id, amend ADR-001 INV-11, its index row, the three `docs/23_agent` statements, and the test; (B) keep `task_id` = turn id, add `turn_id` and `task_linkage`. | Owner decision; no repository evidence can decide it. | Resolved on 20261125: the owner chose option B (additive). No ADR amendment; the Plan stands as drafted on B. | Resolved (option B, 20261125) |
| UNK-02 | `turn_start`/`turn_end` events keep `task_id` = turn id; under A the same key would mean different things across events. | Owner decision on whether to align those events. | Resolved by the UNK-01 decision (option B, 20261125): `turn_start`/`turn_end` are unchanged, so no cross-event divergence arises. No follow-up Issue needed. | Resolved (moot under option B) |
| UNK-03 | `transport_failure` diagnostics store `result.output[:500]`, which for a transport error contains the raw exception text. The Issue wants raw exceptions out of audit rows. | Whether diagnostics count as audit rows and which redaction owner applies. | Route to the redaction/diagnostics Issue (cliplc009); this Plan changes no `error` text. | False |
| UNK-04 | Downstream consumers of the audit schema outside this repository. | Not enumerable from the repository; the Issue lists it as `不明`. | Owner confirms; the additive-only change keeps older readers working. | False |
| UNK-05 | The Issue names a `review_required` dedup state and an approval "decision" event. Neither exists: the closest state is `reconciliation_required`, and decisions are the `decision` field of `tool_approval`. | Whether `review_required` is a planned state. | This Plan uses the shipped state set (AC-1) and `tool_approval.decision`; owner confirms no state is planned. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/transport_dto.py` | Modify | High (46 candidate consumers of `ToolCallResult`; field is defaulted) | 4 | N/A | not applicable (rsynced) |
| `scripts/shared/http_transport.py` | Modify | Medium | 9 | N/A | not applicable (rsynced) |
| `scripts/agent/shared/models.py` | Modify | Low (two writers) | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_audit.py` | Modify | Medium | 10 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_runner.py` | Modify | High (central execution path) | 15 | N/A | not applicable (rsynced) |
| `scripts/agent/tool_result_audit.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/diagnostic_store.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `tests/shared/test_transport_dto.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_http_transport.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_audit.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_audit_log_format.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_runner.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_diagnostic_store.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_dedup_audit_correlation.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_13_reference-api-generated.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
**Classification**: Path B (more than 3 files; changes the runtime `ToolCallResult` contract and audit event shapes). Persisted schema check: no DDL, schema version, or migration is touched (`tool_call_state` is unchanged; diagnostics use a JSON `content` blob), so `rules/persisted-schema-change.md` does not apply.

**Corrected understanding of the Issue** (Step 2 adversarial verification):
- "No occurrence of `dedup_state` in `scripts/agent/`" is stale: `audit_tool_exec` already accepts and serializes `dedup_state` (`tool_audit.py:222,295`). The real gap is that `ToolCallResult` cannot carry it and `tool_runner.py` never passes it (line 344 at the Step 3a re-check on 20261125; 362 at plan generation).
- The turn-id-in-`task_id` mapping is confirmed (`tool_audit.py:141,277`) and is a documented, tested invariant (ADR-001 INV-11), not an accident; hence UNK-01.
- Logical call id in approval, state row, and `tool_exec` is already done (`audit_approval`/`audit_tool_exec` take `idempotency_key`; `tool_runner._logical_call_id` is the sole key). The remaining gap is the diagnostics record.
- `review_required` is not a shipped state (UNK-05).

**Decisions**:
- `dedup_state` is an opaque `str` on `ToolCallResult` (empty = no branch), like the server's `CallToolResponse`; `shared` cannot import `mcp_servers` (`.importlinter` shared-is-leaf), and the state set must not change here.
- The writer keeps conditional serialization of `dedup_state` so the exact-field-set tests and old readers see no new key for ordinary calls.
- New audit fields (`turn_id`, `task_linkage` on approval) are dataclass fields with `""` defaults, so older call sites and records stay valid. `task_linkage` already exists on `ToolExecEvent`; this reuses it for the workflow task id.
- Alternatives for `task_id`: option A (re-point `task_id`) breaks ADR-001 INV-11 and `TestAuditApprovalInv11` and makes `task_id` differ between `turn_start` and tool events; option B (additive) keeps them. The owner chose option B on 20261125 (UNK-01 resolved).

**Consumer scan** (`tools/scan_change_consumers.py`, seeds `ToolCallResult`, `ToolExecEvent`, `ToolApprovalEvent`; candidates only): `ToolCallResult` has 46 script candidates (constructions use keywords and defaults, so a new defaulted field is source-compatible), 19 doc candidates; `ToolExecEvent`/`ToolApprovalEvent` have only `tool_audit.py`, `models.py`, and tests. Dispositions: docs candidates other than the three target docs are `not affected: no field list is stated` (`mcp_02_01`, `mcp_03_01`, `mcp_03_03`, `mcp_06_07`, `agent_12`, `shared_03_03`); the ADR candidates cite tests only, `not affected`.

**Predictable fallout check**: module size — `tool_runner.py` 23736 B of 24576 B at the Step 8 re-run (840 B headroom; was 24544 B at generation), so the pending mcpai004/mcpai005 procedure additions can cross the gate; the new `tool_result_audit.py` row and REQ-007 cover it (`tool_audit.py` 11984 B, `http_transport.py` 17744 B, `diagnostic_store.py` 10198 B, `transport_dto.py` 3651 B, `models.py` 2619 B are under the gate). Pinned counts — `tests/agent/test_tool_audit.py:385-403` pins the exact `tool_exec` field set (target row). Tool inventory — no `tools/*.py` added. Generated blocks — `agent_13_reference-api-generated.md` regenerates for the new module (target row).

**Validation quality baseline** (Step 5): `radon cc`: `execute_one_tool_call` B(8), `audit_approval` A(5), `HttpTransport._tool_error_result` B(6); `vulture scripts/ --min-confidence 80`: pre-existing findings only (for example `document_manager.py:119`), none in target files; `bandit -r scripts/ -c pyproject.toml`: pre-existing Medium/High counts, none attributed to target files in this check; `diff-cover`: not run in this phase (a full coverage run was not performed); the Plan requires at least 90% on changed lines per `rules/toolchain.md` Completion checklist.

## Implementation steps
1. **Phase 1: Transport result and parser**
   - [ ] Add `dedup_state` to `ToolCallResult` and `from_transport` (REQ-001; `scripts/shared/transport_dto.py`)
   - [ ] Parse it in `_parse_http_response` and tolerantly in `_tool_error_result` (REQ-002; `scripts/shared/http_transport.py`)
   - [ ] Add DTO and parser tests (REQ-001, REQ-002; `tests/shared/test_transport_dto.py`, `tests/shared/test_http_transport.py`)
2. **Phase 2: Audit event fields**
   - [ ] Add `turn_id` (and `task_linkage` on approval) to the event dataclasses (REQ-004, REQ-006; `scripts/agent/shared/models.py`)
   - [ ] Populate `turn_id` and `task_linkage` in both writers per the UNK-01 decision (option B: `task_id` keeps its current value, the turn id) (REQ-004, REQ-005; `scripts/agent/tool_audit.py`)
   - [ ] Update the field-set pins and add cases (REQ-004, REQ-006; `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py`)
3. **Phase 3: Runner wiring, extraction, and diagnostics**
   - [ ] Create `record_tool_exec` and `record_transport_failure`, passing `dedup_state` and ids (REQ-003, REQ-005, REQ-007; `scripts/agent/tool_result_audit.py`)
   - [ ] Replace the inline audit call and `_record_transport_failure` in the runner; confirm size under the gate (REQ-003, REQ-007; `scripts/agent/tool_runner.py`)
   - [ ] Add optional id keys to `save_transport_failure` (REQ-005; `scripts/agent/diagnostic_store.py`)
   - [ ] Add runner and diagnostics tests (REQ-003, REQ-005; `tests/agent/test_tool_runner.py`, `tests/agent/test_diagnostic_store.py`)
4. **Phase 4: End-to-end correlation test**
   - [ ] Add the transport-to-audit correlation test (REQ-009; `tests/agent/test_dedup_audit_correlation.py`)
5. **Phase 5: Documentation**
   - [ ] Correct the tracing document and add field definitions and the compatibility note (REQ-006, REQ-008; `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`)
   - [ ] Describe the new `ToolCallResult` field (REQ-008; `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`)
   - [ ] Regenerate the reference (REQ-008; `docs/23_agent/agent_13_reference-api-generated.md`)
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` because `scripts/` changes; prerequisite: the change is committed and pushed, and deploying is the user's decision (approval gate). Run the full validation sequence first (REQ-007; `scripts/agent/tool_runner.py`, `scripts/agent/tool_result_audit.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/transport_dto.py`, `scripts/shared/http_transport.py` | Unit parser and DTO tests | `uv run pytest tests/shared/test_transport_dto.py tests/shared/test_http_transport.py` | All states parse; missing or non-string gives `""` |
| `scripts/agent/tool_audit.py`, `scripts/agent/shared/models.py` | Unit serialization tests | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py` | New fields present; exact field set updated; old shapes valid |
| `scripts/agent/tool_runner.py`, `scripts/agent/tool_result_audit.py`, `scripts/agent/diagnostic_store.py` | Unit and runner tests | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_diagnostic_store.py` | `dedup_state` reaches the audit line; diagnostics carry ids |
| Transport-to-audit path | Integration correlation test | `uv run pytest tests/agent/test_dedup_audit_correlation.py` | Request, session, call, task, turn correlate |
| All changed `scripts/` and `tests/` | Format, lint, type, architecture, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | No findings |
| Module size | Gate | `uv run python tools/check_module_size.py` | `tool_runner.py` under 24576 B |
| Full suite and coverage | Regression | `uv run python tools/run_validation_gates.py --full` (diff-cover at least 90%) | Pass |
| `docs/` changes | Docs gates | `uv run python tools/generate_reference_table.py --check` and the checkers selected by `rules/tool-gates.md` | Pass |

## Risks
- **Risk**: Option A for UNK-01 is chosen after implementation starts, forcing an ADR-001 amendment and rework of `task_id` tests (likelihood: medium) → **Mitigation**: UNK-01 is blocking, so the Plan is not frozen and no procedure is generated until it is decided. Resolved on 20261125: the owner chose option B; the Plan is frozen on that basis.
- **Risk**: Pending procedures of the structured execution context (mcpai005) and logical idempotency key (mcpai004) Plans edit the same files and conflict on `ToolCallResult` field order or `tool_runner.py` (likelihood: medium) → **Mitigation**: implement after them, append the field last, re-read each file and re-measure `tool_runner.py` size before editing.
- **Risk**: `tool_runner.py` is 840 B under the size gate at the Step 8 re-run (23736 B of 24576 B), and the pending mcpai004/mcpai005 procedures add code that can cross the gate (likelihood: medium) → **Mitigation**: REQ-007 and the extraction row; the gate is a validation row; re-measure at implementation time.
- **Risk**: A server returns a non-string `dedup_state` or a malformed 4xx body and breaks classification (likelihood: low) → **Mitigation**: REQ-002 requires `""` without raising, with tests for both.
- **Risk**: Downstream readers outside the repository assume `task_id` is the turn id or reject unknown keys (likelihood: unknown, UNK-04) → **Mitigation**: additive-only fields, `task_id` unchanged under option B, compatibility note in the docs.
- **Risk**: The diagnostics `error` text still contains raw exception text (likelihood: existing) → **Mitigation**: unchanged here; tracked as UNK-03 for the redaction Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Transport result and parser | In Progress | — | — |  |
| 2 | Phase 2: Audit event fields | In Progress | — | — |  |
| 3 | Phase 3: Runner wiring, extraction, and diagnostics | In Progress | — | — |  |
| 4 | Phase 4: End-to-end correlation test | In Progress | — | — |  |
| 5 | Phase 5: Documentation | In Progress | — | — |  |
| 6 | Phase 6: Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-6 | UNK-01: `task_id` contract conflicts with ADR-001 INV-11; owner decision required before freeze | Yes | 20261125 (owner chose option B; Plan frozen on that basis) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| issues/20261125-142023_unknowns.md | 2 | Issue | Resolved (option B, 20261125) | — | — |
| implementations/20261125-162155_01_scripts_shared_transport_dto.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-162155_02_scripts_shared_http_transport.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-162155_03_scripts_agent_shared_models.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-162155_04_scripts_agent_tool_audit.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-162155_05_scripts_agent_tool_runner.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-162155_06_scripts_agent_tool_result_audit.py.md | 3, 4 | Procedure | Pending | — | — |
| implementations/20261125-162155_07_scripts_agent_diagnostic_store.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-162155_10_tests_agent_test_tool_audit.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-162155_11_tests_agent_test_audit_log_format.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-162155_12_tests_agent_test_tool_runner.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-162155_15_docs_22_mcp_mcp_06_06_end-to-end-tool-call-tracing.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261125-162155_16_docs_40_shared_shared_02_02_types_and_protocols-tool-and-execution-dto.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261125-162155_17_docs_23_agent_agent_13_reference-api-generated.md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-142023
- **Related target files**: `scripts/shared/transport_dto.py`, `scripts/shared/http_transport.py`, `scripts/agent/shared/models.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_result_audit.py`, `scripts/agent/diagnostic_store.py`, `tests/shared/test_transport_dto.py`, `tests/shared/test_http_transport.py`, `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py`, `tests/agent/test_tool_runner.py`, `tests/agent/test_diagnostic_store.py`, `tests/agent/test_dedup_audit_correlation.py`, `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`, `docs/23_agent/agent_13_reference-api-generated.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Background | `scripts/shared/transport_dto.py` | Phase 1 | AC-1 | `tests/shared/test_transport_dto.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/shared/test_transport_dto.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_transport_dto.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes bullet 1 (success and tool-level error) | `scripts/shared/http_transport.py` | Phase 1 | AC-1, AC-2 | `tests/shared/test_http_transport.py` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations (parser tests per state) | `tests/shared/test_http_transport.py` | Phase 1 | AC-2 | `uv run pytest tests/shared/test_http_transport.py` | Explicit in issue |
| REQ-003 | Acceptance Criteria 1; `tool_runner.py:344` (line shifted from 362; re-checked at Step 3a on 20261125) | `scripts/agent/tool_runner.py` | Phase 3 | AC-1 | `tests/agent/test_tool_runner.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria 1 | `scripts/agent/tool_result_audit.py` | Phase 3 | AC-1 | `tests/agent/test_tool_runner.py` | Derived from confirmed evidence |
| REQ-003 | Acceptance Criteria 1 | `tests/agent/test_tool_runner.py` | Phase 3 | AC-1 | `uv run pytest tests/agent/test_tool_runner.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes bullet 2; `tool_audit.py:141,277`; ADR-001 INV-11 | `scripts/agent/shared/models.py` | Phase 2 | AC-3 | `tests/agent/test_tool_audit.py` | Confirmed (UNK-01 resolved: option B, 20261125) |
| REQ-004 | Required Changes bullet 2 | `scripts/agent/tool_audit.py` | Phase 2 | AC-3 | `tests/agent/test_tool_audit.py` | Confirmed (UNK-01 resolved: option B, 20261125) |
| REQ-004 | Testing Expectations (audit serialization) | `tests/agent/test_tool_audit.py` | Phase 2 | AC-3 | `uv run pytest tests/agent/test_tool_audit.py` | Confirmed (UNK-01 resolved: option B, 20261125) |
| REQ-004 | Testing Expectations | `tests/agent/test_audit_log_format.py` | Phase 2 | AC-3 | `uv run pytest tests/agent/test_audit_log_format.py` | Confirmed (UNK-01 resolved: option B, 20261125) |
| REQ-005 | Required Changes bullet 4; `diagnostic_store.py:259` | `scripts/agent/diagnostic_store.py` | Phase 3 | AC-5 | `tests/agent/test_diagnostic_store.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 4 | `scripts/agent/tool_audit.py` | Phase 2 | AC-5 | `tests/agent/test_tool_audit.py` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria 5 | `tests/agent/test_diagnostic_store.py` | Phase 3 | AC-5 | `uv run pytest tests/agent/test_diagnostic_store.py` | Derived from confirmed evidence |
| REQ-006 | Constraints; AI Implementation Instruction | `tests/agent/test_audit_log_format.py` | Phase 2 | AC-4 | `uv run pytest tests/agent/test_audit_log_format.py` | Explicit in issue |
| REQ-006 | Acceptance Criteria 4; Documentation Impact | `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Phase 5 | AC-4 | Docs checkers in Validation plan | Explicit in issue |
| REQ-007 | Derived: `wc -c scripts/agent/tool_runner.py` = 24544 B vs gate 24576 B | `scripts/agent/tool_runner.py` | Phase 3 | AC-6 | `uv run python tools/check_module_size.py` | Confirmed by repository evidence |
| REQ-007 | Derived: extraction target | `scripts/agent/tool_result_audit.py` | Phase 3 | AC-6 | `uv run python tools/check_module_size.py` | Derived from confirmed evidence |
| REQ-008 | Documentation Impact; stale `mcp_06_06` lines 51 and 55 | `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Phase 5 | AC-4 | Docs checkers in Validation plan | Confirmed by repository evidence |
| REQ-008 | Documentation Impact | `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | Phase 5 | AC-4 | Docs checkers in Validation plan | Explicit in issue |
| REQ-008 | Predictable fallout check (generated block) | `docs/23_agent/agent_13_reference-api-generated.md` | Phase 5 | AC-4 | `uv run python tools/generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-009 | Testing Expectations (end-to-end correlation) | `tests/agent/test_dedup_audit_correlation.py` | Phase 4 | AC-7 | `uv run pytest tests/agent/test_dedup_audit_correlation.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-162155 -->