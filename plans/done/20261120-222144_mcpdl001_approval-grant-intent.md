# Plan: Establish the logical call id, approval grant, and durable Agent intent contract

## Goal
- Give every Agent-side tool call one immutable logical call id carried unchanged from preparation through approval, durable intent, gateway, transport, and audit; make approval a verifiable capability the gateway checks immediately before execution; and persist durable intent before any side-effecting dispatch, failing closed when state or mandatory audit cannot be written.

## Priority
High

## Scope
- **In-Scope**:
  - Opaque logical call id generated once per prepared call, validated, never LLM-supplied.
  - Immutable `ToolExecutionContext` added to `PreparedToolCall` and carried through `RepositoryGateway`, `ToolExecutor`, `ToolTransportInvoker`, `HttpTransport`, audit, and state records.
  - `X-Idempotency-Key` carries the logical call id; removal of `derive_idempotency_key` and `tool_runner._state_key()`; no transport-derived fallback for side-effecting calls.
  - Immutable `ApprovalGrant` issued by the approval flow and verified in `RepositoryGateway` before execution.
  - `tool_call_state` re-keyed on the logical call id; Agent intent state vocabulary extended; fail-closed state and mandatory-audit persistence for side-effecting calls; best-effort audit kept only for read-only calls.
  - Post-send response loss recorded as `outcome_unknown`, never auto-retried.
  - Deploy path for the legacy-shape `workflow.sqlite`: operator archive-and-recreate per the current-schema-only policy (no migration code).
- **Out-of-Scope**: The Agent-managed replay directive (mcpai004), the MCP-side ledger and store identity (mcpdl002), dispatcher integration (mcpai001), reconciliation and result replay (mcpdl004, mcpdl006), the config-isolation decision for grant lifetime (mcpdl003), and the docs final sweep (mcpai012).
- **Dependencies**: No prerequisite; this Plan is the first of the `mcpdl` chain and owns the logical call id and the Agent-side state vocabulary. It blocks mcpdl002 (ledger key format), mcpdl004, mcpdl006, and mcpai004 (replay directive); mcpai005, mcpai006, mcpai007, and mcpai009 may start once it lands and must adopt the field names defined here.
  - **Depends on**: N/A: none

## Background
- Consolidated MCP deduplication two-layer defense backlog (memo-issue.md, Issue 1). The logical call id unification moved here from mcpai004, which now depends on this Plan.
- Adversarial verification against HEAD `d77b0589e` (2026-11-20) confirmed the issue's evidence and corrected two stale points (see Design and Risks): the repo has no migration framework (removed by the completed compatrm001 Plan), and audit persistence is confirmed fail-open today (`tool_audit.py:198-204` silently skips the event), resolving the issue's "Needs confirmation" item.

## Problem
- Three key derivations coexist: `_idempotency_key` (`{workflow}:{task}:{turn}:{call_id}`, audit only, `tool_runner.py:137-145`), `_state_key` (transport-derived `derive_idempotency_key(name, args, session_id)` plus task id, `tool_runner.py:148-160`), and the wire key (`http_transport.py:198-208`, derived from tool name, canonical args, and session uid). Audit, workflow state, and the wire therefore never agree, and two distinct calls with identical arguments in one session collide on the same transport key (`record_tool_call`'s `INSERT OR IGNORE`, `tool_call_state_ops.py:63-69`, silently merges them).
- Approval is enforced by call order only: `_run_approval_gate` states approved calls reach execution "without any further approval check performed anywhere downstream" (`tool_runner.py:567-572`), and `RepositoryGateway.execute()` takes raw `tool_name`/`args` with no approval reference (`repository_gateway.py:82-118`).
- State recording is fail-open: recorder failures are logged and execution proceeds (`tool_runner.py:187-191`, `209-210`); audit is skipped entirely when `audit_logger` is None or no request id/source is present (`tool_audit.py:198-204`). After a lost response there is no durable evidence a side-effecting call was approved and dispatched.

## Reason for Change
- At-most-once correctness and write authorization both depend on one stable logical identity and durable evidence. The MCP-side ledger (mcpdl002), the dispatcher (mcpai001), and recovery (mcpdl004) all build on the id defined here.

## Implementation Intent
- Generate one opaque logical call id (`uuid.uuid7()`, available in both the dev and production venvs — 3.14.10, verified 2026-11-20) at preparation time; wrap it in an immutable `ToolExecutionContext` placed in the shared leaf layer and attached to `PreparedToolCall`; pass the context through the executor chain and use it as the sole identity in state rows, audit events, and the `X-Idempotency-Key` header.
- Issue an immutable `ApprovalGrant` per approved call in the approval gate; `RepositoryGateway._gate_write` verifies the grant (tool name, canonical argument hash, execution mode, expiry, single use) immediately before `ToolExecutor.execute`.
- Extend the `tool_call_state` intent vocabulary, write the intent row before dispatch, and make state-write and mandatory-audit failures raise (fail closed) for side-effecting calls; read-only calls keep best-effort audit.
- Treat this as one end-to-end signature change: no compatibility path for the transport-derived key or for unapproved side-effecting calls. The Git MCP server's own validation stays independent (ADR-012 INV-04).

## Requirements
- `REQ-001`: Generate exactly one opaque logical call id per prepared call, not derived from credentials, session identity, tool arguments, or content hashes; validate length, format, whitespace, and control characters; the LLM never emits or edits it.
- `REQ-002`: Add an immutable `ToolExecutionContext` (logical call id, session/workflow/task/turn/tool-call ids, tool name, server key, execution mode, canonical argument hash, tool-contract version, side-effect classification, execution snapshot, approval reference) to `PreparedToolCall` and carry it unchanged through gateway, executor, invoker, transport, audit, and state records.
- `REQ-003`: Send the logical call id as `X-Idempotency-Key`; remove `derive_idempotency_key` (`http_transport.py:45`) and `tool_runner._state_key()`; reject a side-effecting call that carries no id; keep no transport-derived fallback.
- `REQ-004`: No internal id in any LLM-facing message (verified absent today; preserved as a contract, not a removal).
- `REQ-005`: `tool_call_state` rows keyed by the logical call id, with the intent vocabulary `{pending, dispatch_starting, dispatched, response_received, completed, failed, interrupted, outcome_unknown, reconciliation_required}` (canonical DDL `CHECK` and `TOOL_CALL_STATES` updated in the same change).
- `REQ-006`: Immutable `ApprovalGrant` bound to logical call id, tool name, canonical argument hash, risk level, decision, issue time, expiry, and execution mode; issued in `_run_approval_gate`; verified in `RepositoryGateway` before execution; reject tool, argument, mode, call, expiry, and reuse mismatches.
- `REQ-007`: Persist intent before dispatch; fail closed for side-effecting calls when the state row or the mandatory audit record cannot be written; best-effort audit allowed only for explicitly read-only calls.
- `REQ-008`: Record the logical call id in approval events, workflow state, execution audit, and diagnostics; keep raw arguments, credentials, signed URLs, and raw exceptions out of audit rows (existing `mask_args`/preview bounding preserved).
- `REQ-009`: A post-send response loss becomes `outcome_unknown`; `outcome_unknown` is never auto-retried and never replayed by stale-pending control.
- `REQ-010`: No migration code. The legacy-shape `workflow.sqlite` is rejected at startup by the existing current-schema gate; the operator archives and recreates it per the current runbook. This re-states the issue's "migrate existing rows" bullet against the repository's actual policy (see Design).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_preparation.py | modify | Generate the logical call id once and build the `ToolExecutionContext` on `PreparedToolCall`; reject malformed ids | REQ-001, REQ-002, AC-1, AC-3 | `PreparedToolCall` fields at :40-48; `call_id` taken from the LLM dict at :77-84 | `tests/agent/test_tool_preparation.py` | Verified |
| scripts/agent/tool_approval.py | modify | Issue the `ApprovalGrant` when a call passes the approval gate | REQ-006, AC-4 | module purpose :3-6; audit_approval call at :18 | `tests/agent/test_tool_approval_preflight.py` | Verified |
| scripts/agent/repository_gateway.py | modify | Verify the grant immediately before `_gate_write` execution; deny on mismatch, expiry, or reuse | REQ-006, AC-4 | docstring precondition :62-68; `_gate_write` executes with no approval reference :107-118 | `tests/agent/test_repository_gateway.py` | Verified |
| scripts/agent/tool_runner.py | modify | Remove `_idempotency_key`/`_state_key` derivations; propagate the context; fail-closed intent recording and finalize transitions | REQ-003, REQ-005, REQ-007, REQ-009, AC-2, AC-5, AC-6 | key derivations :137-160; fail-open excepts :187-191 and :209-210; audit call :298-309 | `tests/agent/test_tool_runner.py` | Verified |
| scripts/agent/tool_audit.py | modify | Record the logical call id in audit events; make the audit record mandatory (raising) for side-effecting calls | REQ-007, REQ-008, AC-2, AC-5 | silent skip on missing logger/id :198-204; `idempotency_key` param :188, :223 | `tests/agent/test_tool_audit.py`; `tests/agent/test_audit_log_format.py` | Verified |
| scripts/agent/context.py | modify | Update the `ToolCallRecorder` protocol to the new key/state contract | REQ-005, REQ-007 | protocol :284-299; unwired defaults :311-312 | `tests/agent/test_tool_runner.py` | Verified |
| scripts/agent/factory.py | modify | Wire a session-scoped state recorder for non-workflow (plain REPL) sessions so side-effecting calls have a durable intent store | REQ-007, AC-5 | gateway wired unconditionally at :358; recorder/task_id wired only by workflow_engine_adapter (see Reference Files) — plain REPL today writes no `tool_call_state` row | `tests/agent/test_tool_runner.py` | Verified |
| scripts/agent/shared/models.py | modify | Replace the `idempotency_key` event fields with the logical call id; define the `ApprovalGrant` model | REQ-006, REQ-008 | `ToolApprovalEvent` :13, `ToolExecEvent` :30; `idempotency_key: str = ""` with "nothing" comment :48-50 | `tests/agent/test_audit_log_format.py` | Verified |
| scripts/agent/workflow/models.py | modify | Extend `TOOL_CALL_STATES` to the intent vocabulary | REQ-005, AC-6 | `TOOL_CALL_STATES` frozenset at :20 | `tests/agent/workflow/test_workflow_status_vocabulary.py` | Verified |
| scripts/agent/workflow/tool_call_state_ops.py | modify | Rows keyed by logical call id; intent transitions; stale classification split (never-dispatched → `interrupted`, dispatched → `outcome_unknown`) | REQ-005, REQ-009, AC-6 | state values comment :30; `INSERT OR IGNORE` collision merge :63-69; `classify_stale_pending` :105-141 | `tests/agent/workflow/test_workflow_state_store.py`; `tests/agent/workflow/test_workflow_engine.py` | Verified |
| scripts/agent/workflow/state_store.py | modify | Pass the new key/state contract through the recorder methods | REQ-005, REQ-007 | `record_tool_call` / `finalize_tool_call` / `classify_stale_pending` :139-161 | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| scripts/db/schema_sql.py | modify | `tool_call_state` canonical DDL: extend the `state` CHECK vocabulary and re-state the key semantics comment | REQ-005, AC-2 | table DDL with CHECK :215-223 | `tests/db/test_create_schema.py`; `tests/db/test_schema_validation_per_database.py` | Verified |
| scripts/shared/transport_dto.py | modify | Define the immutable `ToolExecutionContext` in the shared leaf layer; carry it on `ToolCallResult` for downstream consumers | REQ-002, AC-2 | `ToolCallResult` definition :26-32; shared-is-leaf contract in `.importlinter` | `tests/shared/test_http_transport.py` | Verified |
| scripts/shared/tool_executor.py | modify | Accept and forward the execution context to the invoker | REQ-002, AC-2 | routing delegation :8-10, :32-36 | `tests/shared/test_tool_executor.py` | Verified |
| scripts/shared/tool_transport_invoker.py | modify | Forward the execution context to the transport; record the dispatch-stage intent signal | REQ-002, REQ-005 | transport invocation layer module docstring :2 | `tests/shared/test_tool_transport_invoker.py` | Verified |
| scripts/shared/http_transport.py | modify | Delete `derive_idempotency_key`; send the logical call id as `X-Idempotency-Key`; reject a side-effecting call with no id | REQ-003, AC-1, AC-3 | derivation function :45-52; header construction :192-208 | `tests/shared/test_http_transport.py`; `tests/shared/test_tool_executor_routing.py` | Verified |
| `tests/agent/test_tool_preparation.py` | modify | Id generation, malformed-id rejection, context attachment | REQ-001, REQ-002 | imports `PreparedToolCall`/`prepare_tool_calls` at :13 | — | Verified |
| `tests/agent/test_tool_approval_preflight.py` | modify | Grant issuance on approval; denial produces no grant | REQ-006 | calls `run_approval_checks` | — | Verified |
| `tests/agent/test_tool_runner.py` | modify | Delete transport-key assertions (:2325-2366, :2547-2564); add fail-closed state/audit and intent-transition tests | REQ-003, REQ-005, REQ-007, REQ-009 | derive-key assertions at :2325, :2343, :2366, :2547, :2551, :2564 | — | Verified |
| `tests/agent/test_repository_gateway.py` | modify | Direct-gateway bypass without grant; argument/mode/expiry/reuse rejection | REQ-006, AC-4 | exists; gateway audit coupling at `grep audit_tool_exec` hit | — | Verified |
| `tests/agent/test_tool_audit.py` | modify | Mandatory audit for side-effecting calls; best-effort for read-only; logical id recorded | REQ-007, REQ-008 | exists; calls `audit_tool_exec` | — | Verified |
| `tests/agent/test_audit_log_format.py` | modify | Audit event field contract (logical call id, no raw args) | REQ-008 | exists; `grep audit_tool_exec` hit | — | Verified |
| `tests/agent/workflow/test_workflow_status_vocabulary.py` | modify | Pin the new intent vocabulary | REQ-005 | pins `TOOL_CALL_STATES` (only test naming it) | — | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | modify | New-key row writes, intent transitions, collision-freedom | REQ-005 | uses `tool_call_state` | — | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | modify | Stale-pending split: never-dispatched replayable, dispatched → `outcome_unknown` non-replayable | REQ-009 | uses `tool_call_state` via engine | — | Verified |
| `tests/shared/test_http_transport.py` | modify | Header carries the opaque id; delete derivation tests (:255-289, :332) | REQ-003 | imports `derive_idempotency_key` at :22, :255, :266, :273, :280, :289 | — | Verified |
| `tests/shared/test_tool_executor.py` | modify | Context forwarded through execute | REQ-002 | exists in issue target list | — | Verified |
| `tests/shared/test_tool_transport_invoker.py` | modify | Context forwarded to transport | REQ-002 | exists in issue target list | — | Verified |
| `tests/shared/test_tool_executor_routing.py` | modify | Delete `derive_idempotency_key` imports/assertions | REQ-003 | imports it at :14 | — | Verified |
| `tests/db/test_create_schema.py` | modify | Workflow DDL shape after the CHECK vocabulary change | REQ-005 | names `tool_call_state` | — | Verified |
| `tests/db/test_schema_validation_per_database.py` | modify | Per-database shape validation against the new DDL | REQ-005 | names `tool_call_state` | — | Verified |
| `tests/deploy/test_required_workflow_tables_parity.py` | modify | Workflow-table parity list against the changed DDL | REQ-005 | names `tool_call_state` | — | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/workflow_engine.py | Consumes `interrupted` rows for replay control; the `outcome_unknown` non-replay rule must not break its interrupted-list contract (no change planned) | scripts/agent/workflow/tool_call_state_ops.py; REQ-009 |
| scripts/agent/workflow_engine_adapter.py | Only place `current_task_id` and `tool_call_recorder` are wired (:304-316); establishes the plain-REPL gap REQ-007 must close | scripts/agent/factory.py; REQ-007 |
| scripts/shared/tool_constants.py | Canonical side-effect classification (`ALL_SIDE_EFFECTING_TOOLS` :223) and `RETRYABLE_TOOLS` drive the fail-closed gate scope | REQ-003, REQ-007 |
| scripts/mcp_servers/server.py | Server-side REQ-004 middleware consumes `x-idempotency-key` opaquely (:149-180); confirms the server boundary is unaffected by the format change | scripts/shared/http_transport.py; REQ-003 |
| scripts/mcp_servers/dispatch.py | `_duplicate_cache` keys wire dedup opaquely (:103-135); unaffected by id format, must stay working | REQ-003 |
| scripts/db/create_schema.py | Current no-automatic-migration, drift-refusal policy (module docstring); basis for REQ-010 | REQ-005, REQ-010 |
| scripts/agent/services/workflow_schema.py | Startup current-shape gate that rejects the legacy workflow.sqlite | REQ-010 |
| config/agent.toml | Existing `approval_*` keys; confirms no grant-expiry config exists today | REQ-006 |
| scripts/shared/execution_snapshot.py | Execution-snapshot builder already embedded in every audit event; the context must reuse it | REQ-002, REQ-008 |
| scripts/agent/workflow/idempotency_ops.py | Task-side `processed_events` idempotency — a distinct mechanism this Plan must not conflate with the tool-call id | REQ-005 |
| scripts/shared/mcp_dedup.py | MCP-side `tool_call_state` store in `mcp_dedup.sqlite` (owned by mcpdl002); boundary must not be touched | Out-of-scope boundary |
| tests/shared/test_mcp_dedup.py | Pins the MCP-side store DDL (:139-174); read-only confirmation of the boundary | Out-of-scope boundary |
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | ADR-012 INV-04 constraint: server-side validation stays independent of Agent approval | REQ-006 constraint |
| plans/done/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md | Evidence that the migration framework was deleted and the archive-and-recreate lifecycle is the policy | REQ-010 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-003): Independent calls with identical arguments get different ids; a retry of the same call reuses its id.
- AC-2 (REQ-002, REQ-005, REQ-008): Agent audit, workflow state, HTTP header, and approval carry the same logical call id.
- AC-3 (REQ-003): A side-effecting call without an id cannot execute.
- AC-4 (REQ-006): An unapproved write cannot execute through `RepositoryGateway`; arguments cannot change after approval; a grant cannot be reused.
- AC-5 (REQ-007): A side effect is rejected when durable state or mandatory audit cannot be written.
- AC-6 (REQ-005, REQ-009): A post-send response loss becomes `outcome_unknown` and is not retried or replayed automatically.

## Tests
- Test-first per the issue instruction: write the bypass and outage tests (Phase 1) before the grant and fail-closed code.
- End-to-end id propagation from preparation to the HTTP header; same-call retry vs different-call-same-arguments; missing-id rejection for side-effecting tools (REQ-001, REQ-003).
- Direct gateway invocation without a grant; tool/argument/mode/expiry/reuse mismatch (REQ-006).
- State-store and audit-store outage: side-effecting call rejected, read-only call still best-effort (REQ-007).
- Plain-REPL (non-workflow) side-effecting call persists an intent row through the new session-scoped recorder (REQ-007).
- `outcome_unknown` transition after a post-send transport failure; `classify_stale_pending` never replays it (REQ-009).
- No LLM-facing message contains the logical call id or any internal key (REQ-004).
- Run ruff, mypy, import-linter, and the full test suite (rules/toolchain.md).

## Documentation Impact
Yes. The identifier contract (workflow/task/turn/call/session/request ids), the approval capability, the intent state vocabulary, and the fail-closed behavior must be reflected in the docs named by `docs/00_index.md` "Document References by Task" rows: "Agent REPL flow / tool execution" (Agent table), "MCP server implementation" and "MCP transport / startup_mode / lifecycle" (MCP table), and the high-risk tool policy row (Security table). Driven by REQ-002, REQ-005, REQ-006, REQ-007. The final sweep is owned by mcpai012 (title only, per Scope rules).

## Assumptions
- `ToolExecutionContext` lives in `scripts/shared/transport_dto.py` (shared is a leaf under the `.importlinter` contracts, so agent types cannot be imported there; a plain-data context fits the leaf) and `ApprovalGrant` in `scripts/agent/shared/models.py`; no new modules are introduced.
- Grant lifetime: fixed module constant (short, single-use, consumed at the gateway) until the config-isolation decision in mcpdl003 lands; no `agent.toml` key is added.
- Python fact verified 2026-11-20: dev venv and `/opt/llm/.venv` are both 3.14.10 and provide `uuid.uuid7()`; `requires-python = ">=3.13"`. (The AGENTS.md "3.13" line is stale relative to both venvs; noted, not acted on.)
- LLM-facing messages contain no internal idempotency key today (repo-wide grep 2026-11-20); REQ-004 preserves this.
- The server treats `X-Idempotency-Key` opaquely (middleware and `_duplicate_cache`), so the id-format change requires no MCP-server change.
- The two author names "Masao Sugimoto"/"Masao SUGIMOTO" in git history are the same person: bus factor is effectively 1 for all target areas.
- `tool_runner.py:227` cites "factory.py:652" for unconditional gateway creation; the current line is 358 — a stale citation noted, not a target change.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Grant expiry value and whether it becomes config (issue carried this as `不明`; see mcpdl003) | No grant exists today; `config/agent.toml` has no grant-expiry key (verified 2026-11-20) | Plan default: module constant, single-use; owner confirms at mcpdl003 | False |
| UNK-02 | Exact session-scope identity used as `task_id` for plain-REPL intent rows (schema has no FK, so a synthetic scope string is safe, but the naming convention is an owner choice) | No precedent in code: `workflow_engine_adapter.py:304` is the only writer today | Plan default: session-scoped pseudo-task id derived from `session_id`; owner confirms before procedure generation | False |
| UNK-03 | Whether `reconciliation_required` may be written by this Plan's code paths or only introduced as vocabulary now and written by mcpdl004 (reconciliation) | No consumer exists in the repo (verified 2026-11-20) | Plan default: vocabulary-only in this change; mcpdl004 adds the writer | False |
| UNK-04 | Owner confirmation that no legacy `tool_call_state` row data needs preservation at deploy (archive-and-recreate discards rows) | Production `/opt/llm/db/workflow.sqlite` exists but its row contents were not inspected (read-only inspection not requested) | Operator inspects/archives at deploy per the compatrm001 runbook | False |

Resolved during verification (no longer unknown): key composition — Plan decides opaque `uuid.uuid7()` (a content-composite key would collide exactly as `_state_key` does today); exact state vocabulary — decided in REQ-005; migration location — no migration mechanism exists (deleted by the completed compatrm001 Plan; `create_schema.py` refuses drift), REQ-010 restates the issue's migrate-rows bullet as archive-and-recreate; audit mandatory today — no, `tool_audit.py:198-204` skips silently, so REQ-007 is a behavior change, not a confirmation.

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_runner.py | Remove key derivations; fail-closed recording | High — round execution path | 15 | High (single author) | No |
| scripts/agent/tool_preparation.py | Context + id generation | Medium — preparation phase contract | 2 | High (single author) | No |
| scripts/agent/tool_approval.py | Grant issuance | Medium — approval flow | 5 | High (single author) | No |
| scripts/agent/repository_gateway.py | Grant verification | High — authorization boundary | 2 | High (single author) | No |
| scripts/agent/tool_audit.py | Mandatory audit for side effects | Medium — audit writers | 7 | High (single author) | No |
| scripts/agent/context.py | Recorder protocol change | Medium — DI hub | 11 | High (single author) | No |
| scripts/agent/factory.py | Session-scoped recorder wiring | Medium — service construction | 1 (n/a, not measured) | High (single author) | No |
| scripts/agent/workflow/tool_call_state_ops.py | Intent transitions, stale split | High — recovery semantics | 6 | High (single author) | No |
| scripts/db/schema_sql.py | `tool_call_state` CHECK vocabulary | High — persisted schema | 19 | High (single author) | Yes — legacy workflow.sqlite rejected; operator archive-and-recreate |
| scripts/shared/http_transport.py | Delete derivation; opaque header | High — wire contract | 7 | High (single author) | No |
| scripts/shared/tool_executor.py | Context forwarding | Medium — execution chain | 3 | High (single author) | No |
| scripts/shared/tool_transport_invoker.py | Context forwarding | Medium — transport gate layer | 5 | High (single author) | No |
| tests/agent/test_tool_runner.py | Key-assertion removal; new fail-closed tests | Medium | 15 | High (single author) | No |
| tests/shared/test_http_transport.py | Derivation-test removal | Medium | — | High (single author) | No |

(File rows above are a subset of `Implementation Target Files`; the remaining test rows carry Medium radius and No deploy.sh impact.)

## Design
- **Identity contract**: one opaque UUIDv7 (`uuid.uuid7()`, verified available in both venvs) generated in `prepare_tool_calls`; it is the primary key of `tool_call_state`, the audit `idempotency_key` field value, and the `X-Idempotency-Key` value. `_idempotency_key` and `_state_key` are deleted; the LLM `call_id` remains only as the history/tool-message correlation id, never as identity.
- **Layer placement**: `ToolExecutionContext` in `shared/transport_dto.py` keeps the shared-is-leaf import-linter contract intact (agent cannot be imported from shared; the context is plain str/dict data plus the frozen dataclass). `ApprovalGrant` in `agent/shared/models.py` stays Agent-side; grant verification never reaches the MCP server (ADR-012 INV-04 preserved — the gateway check is additive, the git server's own validation is untouched).
- **Grant flow**: `_run_approval_gate` → grant issued and bound to the `PreparedToolCall` → `RepositoryGateway._gate_write` verifies hash-of-args, tool name, execution mode, expiry, and single use immediately before `ToolExecutor.execute`; any mismatch returns the existing `_denied_result` path. Gateway-bypass branch (`tool_runner.py:239-246`) must likewise require a grant for non-READ calls.
- **Intent lifecycle**: `pending` is written at preparation (existing behavior), transitions `dispatch_starting` → `dispatched` → `response_received` → `completed`/`failed`; a cancelled or crashed in-flight row is stale-classified: never-dispatched → `interrupted` (replayable, existing workflow_engine contract kept), dispatched → `outcome_unknown` (never replayable). `reconciliation_required` is vocabulary-only in this Plan (UNK-03). `pending` is kept rather than renamed to `prepared` so `classify_stale_pending` and its tests remain valid until the new states are exercised.
- **Fail-closed scope**: side-effect classification from `ALL_SIDE_EFFECTING_TOOLS`; when classified non-READ, a failed state write or unwritable mandatory audit raises into `execute_one_tool_call`, producing a tool-error row instead of executing. Read-only calls keep the current best-effort behavior. Newly failing paths (issue Constraint): plain-REPL writes when the new session recorder is unwired or its store errors; workflow writes when `tool_call_state` writes fail; any side-effecting call when `audit_logger` is None (today such events are silently skipped — `tool_audit.py:198`).
- **Plain-REPL gap (adversarial finding)**: `current_task_id`/`tool_call_recorder` are wired only by `workflow_engine_adapter.py:304-316`; plain REPL sessions write no `tool_call_state` row today. `factory.py` must wire a session-scoped recorder (UNK-02 task-scope convention) or REQ-007 would deny every plain-REPL write.
- **Persisted-schema checklist outcomes** (rules/persisted-schema-change.md, applied 2026-11-20): item 1 — version stores were deleted by the completed compatrm001 Plan; the workflow DB has no ledger; N/A. Item 2 — the startup gate compares exact shape against canonical DDL; editing canonical DDL alone is correct under the recreate policy; `tools/check_db_separation.py` must still pass. Item 3 — no table rebuild is performed; the production DB is recreated fresh; N/A by policy. Item 4 — the tightened `CHECK` ships with the code vocabulary in one release unit (Unit-2); every writer is a target row. Item 5 — no registry/frozen steps exist; N/A. Item 6 — the pinning tests are named as target rows (test_workflow_status_vocabulary, test_create_schema, test_schema_validation_per_database, test_required_workflow_tables_parity). Item 7 — rows with old meanings: owner decision = archive-and-recreate, no row mapping (UNK-04). Note: the rules file cites framework files that no longer exist (`scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/shared/eventbus_schema_fingerprint.py`) — verified absent 2026-11-20; a follow-up issue should refresh that rules file (out of this Plan's file scope).
- **Consumer-scan dispositions** (tools/scan_change_consumers.py, 2026-11-20): targets added beyond the issue list — `scripts/agent/workflow/models.py`, `scripts/agent/shared/models.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/factory.py`, `scripts/db/schema_sql.py`, `tests/agent/test_tool_preparation.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py`, the three `tests/agent/workflow/` state tests, `tests/shared/test_tool_executor_routing.py`, and the three DB/deploy DDL-pin tests. Not affected: `tests/shared/test_mcp_dedup.py` and `scripts/shared/mcp_dedup.py` (MCP-side store, mcpdl002-owned); `tests/mcp_servers/test_server_idempotency_boundary.py` and `scripts/mcp_servers/server.py` (opaque-key middleware, logic unchanged); `tools/check_db_separation.py` (table inventory names unchanged); `tests/agent/test_repl_health.py` (fixtures built from canonical DDL; legacy-marker tests unchanged); `tests/agent/test_tool_loop_guard_wiring.py` and `tests/agent/test_agent_repl_tool_exec.py` (monkeypatch the approval gate wiring, not its contract); `tests/agent/workflow/test_workflow_engine.py`'s replay-control consumer module `workflow_engine.py` itself needs no change (interrupted semantics preserved).
- **Operational state inspected 2026-11-20**: no process listens on service ports (`ss -ltn`); `/opt/llm/db/workflow.sqlite` exists and will be rejected at startup after the DDL change until archived and recreated (intended deploy-time operator action, consistent with the compatrm001 precedent).

## Implementation steps
Each step cites rows of the frozen `Implementation Target Files` table.

1. **Phase 1: Contract and bypass/outage tests first**
   - [ ] Add failing-now characterization tests: gateway bypass without grant, argument/mode/expiry/reuse mismatch, store/audit outage for side-effecting vs read-only, plain-REPL intent persistence (REQ-006, REQ-007, AC-4, AC-5; tests/agent/test_repository_gateway.py, tests/agent/test_tool_runner.py, tests/agent/test_tool_audit.py)
   - [ ] Add id-collision and header-propagation contract tests (REQ-001, REQ-003; tests/shared/test_http_transport.py, tests/agent/test_tool_preparation.py)
2. **Phase 2: Logical call id and ToolExecutionContext**
   - [ ] Generate UUIDv7 id and immutable context at preparation; attach to `PreparedToolCall` (REQ-001, REQ-002; scripts/agent/tool_preparation.py, scripts/shared/transport_dto.py)
   - [ ] Replace audit/state key fields with the logical call id (REQ-008; scripts/agent/shared/models.py, scripts/agent/tool_audit.py)
3. **Phase 3: Transport key replacement**
   - [ ] Delete `derive_idempotency_key` and `_state_key`; header carries the logical id; reject side-effecting calls with no id (REQ-003; scripts/shared/http_transport.py, scripts/agent/tool_runner.py, tests/shared/test_http_transport.py, tests/shared/test_tool_executor_routing.py, tests/agent/test_tool_runner.py)
   - [ ] Forward the context through the executor chain (REQ-002; scripts/shared/tool_executor.py, scripts/shared/tool_transport_invoker.py)
4. **Phase 4: ApprovalGrant and gateway verification**
   - [ ] Issue the grant in the approval gate; define the model (REQ-006; scripts/agent/tool_approval.py, scripts/agent/shared/models.py)
   - [ ] Verify the grant in `_gate_write` and in the gateway-bypass path; deny on mismatch (REQ-006, AC-4; scripts/agent/repository_gateway.py, scripts/agent/tool_runner.py)
5. **Phase 5: Intent states and fail-closed persistence**
   - [ ] Extend `TOOL_CALL_STATES` and the canonical DDL `CHECK` in the same commit (REQ-005; scripts/agent/workflow/models.py, scripts/db/schema_sql.py)
   - [ ] Implement intent transitions and the stale split; update the recorder contract and wiring (REQ-005, REQ-007, REQ-009; scripts/agent/workflow/tool_call_state_ops.py, scripts/agent/workflow/state_store.py, scripts/agent/context.py, scripts/agent/factory.py, scripts/agent/tool_runner.py)
   - [ ] Make audit mandatory for side-effecting calls; keep read-only best-effort (REQ-007; scripts/agent/tool_audit.py)
6. **Phase 6: Deployment & verification**
   - [ ] Confirm `tools/check_db_separation.py` and the DB-shape pins pass against the new DDL; run the full toolchain gates (REQ-005, REQ-010; tests/db/test_create_schema.py, tests/db/test_schema_validation_per_database.py, tests/deploy/test_required_workflow_tables_parity.py)
   - [ ] Deploy note validated: legacy `/opt/llm/db/workflow.sqlite` is rejected by the startup gate; the archive-and-recreate runbook applies (no deploy file change) (REQ-010)

### Release units
**Unit**: contract-chain | **Phases**: 1, 2, 3 | **Reason**: Phase 1 tests fail by construction until Phase 2-3 land, and Phase 3 key deletion breaks the Phase-2 wiring and the old test assertions in the same commit set.
**Unit**: auth-intent | **Phases**: 4, 5 | **Reason**: grant verification, fail-closed writes, and the DDL/`TOOL_CALL_STATES` vocabulary must land together; intermediate commits would leave side-effecting calls denied or vocabulary tests red.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_preparation.py | Unit | `uv run pytest tests/agent/test_tool_preparation.py` | Id unique per call; malformed ids rejected; context attached |
| scripts/agent/repository_gateway.py | Unit | `uv run pytest tests/agent/test_repository_gateway.py` | Grantless/mismatched calls denied |
| scripts/agent/tool_runner.py | Unit | `uv run pytest tests/agent/test_tool_runner.py` | Fail-closed paths raise; no transport-key references remain |
| scripts/shared/http_transport.py | Unit | `uv run pytest tests/shared/test_http_transport.py` | Header carries opaque id; derivation tests removed |
| scripts/agent/workflow/* + scripts/db/schema_sql.py | Unit + scratch-DB shape check (rules/persisted-schema-change.md recipe) | `uv run pytest tests/agent/workflow tests/db tests/deploy/test_required_workflow_tables_parity.py && uv run python tools/check_db_separation.py` | Vocabulary consistent DDL↔code; separation check passes |
| Cross-layer | Static | `uv run ruff check . && uv run mypy scripts/ && uv run lint-imports` | Clean; shared-leaf contract intact |
| Whole suite | Integration | `uv run pytest` | Green; newly failing paths enumerated in Design appear as intended behavior changes |

## Risks
- **Risk**: fail-open → fail-closed turns today-silent degradations (unwired recorder, missing audit logger, store errors) into user-visible denials for every side-effecting call → **Mitigation**: the newly failing paths are enumerated in Design; Phase 1 tests pin the exact denial results before the behavior lands.
- **Risk**: plain-REPL sessions currently have no task context; an unwired session-scoped recorder would deny all plain-REPL writes → **Mitigation**: factory wiring (target row) + a plain-REPL regression test.
- **Risk**: `workflow.sqlite` in production carries rows keyed by the old derivation and will be rejected at startup after the DDL change → **Mitigation**: archive-and-recreate runbook (compatrm001 precedent); UNK-04 operator confirmation before deploy.
- **Risk**: high churn on `scripts/db/schema_sql.py` (19 commits/30d) and `scripts/agent/tool_runner.py` (15) plus single-author bus factor → **Mitigation**: characterization tests first; land Unit-2 in one reviewed commit.
- **Risk**: `rules/persisted-schema-change.md` cites deleted framework files and could mislead the implementer → **Mitigation**: this Plan records current facts (create_schema policy, compatrm001); file a follow-up issue to refresh the rules file (out of this Plan's targets).
- **Risk**: downstream plans (mcpdl002, mcpdl004, mcpai005) adopt this contract; a naming drift would fork the identity model → **Mitigation**: this Plan's REQ-002/REQ-005 vocabulary is the canonical source they must cite.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Contract and bypass/outage tests first | In Progress | — | — |  |
| 2 | Phase 2: Logical call id and ToolExecutionContext | In Progress | — | — |  |
| 3 | Phase 3: Transport key replacement | In Progress | — | — |  |
| 4 | Phase 4: ApprovalGrant and gateway verification | In Progress | — | — |  |
| 5 | Phase 5: Intent states and fail-closed persistence | In Progress | — | — |  |
| 6 | Phase 6: Deployment & verification | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261120-225424_01_scripts_agent_tool_preparation.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-225424_02_scripts_agent_tool_approval.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261120-225424_03_scripts_agent_repository_gateway.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261120-225424_04_scripts_agent_tool_runner.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261120-225424_05_scripts_agent_tool_audit.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-225424_06_scripts_agent_context.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_07_scripts_agent_factory.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_08_scripts_agent_shared_models.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-225424_09_scripts_agent_workflow_models.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_10_scripts_agent_workflow_tool_call_state_ops.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_11_scripts_agent_workflow_state_store.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_12_scripts_db_schema_sql.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_13_scripts_shared_transport_dto.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-225424_14_scripts_shared_tool_executor.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261120-225424_15_scripts_shared_tool_transport_invoker.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261120-225424_16_scripts_shared_http_transport.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261120-225424_19_tests_agent_test_tool_runner.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261120-225424_22_tests_agent_test_audit_log_format.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-225424_24_tests_agent_workflow_test_workflow_state_store.py.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261120-225424_26_tests_shared_test_http_transport.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261120-225424_32_tests_deploy_test_required_workflow_tables_parity.py.md` | 6 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-115840_mcpdl001_approval-grant-intent.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-222144
- **Related target files**: scripts/agent/tool_preparation.py, scripts/agent/tool_approval.py, scripts/agent/repository_gateway.py, scripts/agent/tool_runner.py, scripts/agent/tool_audit.py, scripts/agent/context.py, scripts/agent/factory.py, scripts/agent/shared/models.py, scripts/agent/workflow/models.py, scripts/agent/workflow/tool_call_state_ops.py, scripts/agent/workflow/state_store.py, scripts/db/schema_sql.py, scripts/shared/transport_dto.py, scripts/shared/tool_executor.py, scripts/shared/tool_transport_invoker.py, scripts/shared/http_transport.py, tests/agent/test_tool_preparation.py, tests/agent/test_tool_approval_preflight.py, tests/agent/test_tool_runner.py, tests/agent/test_repository_gateway.py, tests/agent/test_tool_audit.py, tests/agent/test_audit_log_format.py, tests/agent/workflow/test_workflow_status_vocabulary.py, tests/agent/workflow/test_workflow_state_store.py, tests/agent/workflow/test_workflow_engine.py, tests/shared/test_http_transport.py, tests/shared/test_tool_executor.py, tests/shared/test_tool_transport_invoker.py, tests/shared/test_tool_executor_routing.py, tests/db/test_create_schema.py, tests/db/test_schema_validation_per_database.py, tests/deploy/test_required_workflow_tables_parity.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1 | scripts/agent/tool_preparation.py | 2 | AC-1 | tests/agent/test_tool_preparation.py | Planned |
| REQ-001 | Required Changes bullet 1 | tests/agent/test_tool_preparation.py | 1 | AC-1 | id uniqueness/collision tests | Planned |
| REQ-002 | Required Changes bullet 2 | scripts/shared/transport_dto.py | 2 | AC-2 | tests/shared/test_http_transport.py | Planned |
| REQ-002 | Required Changes bullet 2 | scripts/agent/tool_preparation.py | 2 | AC-2 | tests/agent/test_tool_preparation.py | Planned |
| REQ-002 | Required Changes bullet 2 | scripts/shared/tool_executor.py | 3 | AC-2 | tests/shared/test_tool_executor.py | Planned |
| REQ-002 | Required Changes bullet 2 | scripts/shared/tool_transport_invoker.py | 3 | AC-2 | tests/shared/test_tool_transport_invoker.py | Planned |
| REQ-003 | Required Changes bullet 3 | scripts/shared/http_transport.py | 3 | AC-1, AC-3 | tests/shared/test_http_transport.py | Planned |
| REQ-003 | Required Changes bullet 3 | scripts/agent/tool_runner.py | 3 | AC-2, AC-3 | tests/agent/test_tool_runner.py | Planned |
| REQ-003 | Required Changes bullet 3 | tests/shared/test_tool_executor_routing.py | 3 | AC-3 | derive-key assertion removal | Planned |
| REQ-004 | Required Changes bullet 4 | scripts/agent/tool_runner.py | 2 | AC-2 | no-internal-id LLM-message test | Planned |
| REQ-005 | Required Changes bullets 5, 7 | scripts/agent/workflow/models.py | 5 | AC-6 | tests/agent/workflow/test_workflow_status_vocabulary.py | Planned |
| REQ-005 | Required Changes bullets 5, 7 | scripts/agent/workflow/tool_call_state_ops.py | 5 | AC-2, AC-6 | tests/agent/workflow/test_workflow_state_store.py | Planned |
| REQ-005 | Required Changes bullets 5, 7 | scripts/db/schema_sql.py | 5 | AC-2 | tests/db/test_create_schema.py, tests/db/test_schema_validation_per_database.py | Planned |
| REQ-005 | Required Changes bullets 5, 7 | scripts/agent/workflow/state_store.py | 5 | AC-2 | tests/agent/workflow/test_workflow_state_store.py | Planned |
| REQ-005 | Required Changes bullets 5, 7 | scripts/agent/context.py | 5 | AC-5 | recorder contract in tests/agent/test_tool_runner.py | Planned |
| REQ-005 | Required Changes bullet 5 | tests/agent/workflow/test_workflow_state_store.py | 5 | AC-2 | new-key row tests | Planned |
| REQ-005 | Required Changes bullet 5 | tests/agent/workflow/test_workflow_status_vocabulary.py | 5 | AC-6 | vocabulary pin | Planned |
| REQ-005 | Required Changes bullet 5 | tests/db/test_create_schema.py | 6 | AC-2 | DDL shape pin | Planned |
| REQ-005 | Required Changes bullet 5 | tests/db/test_schema_validation_per_database.py | 6 | AC-2 | shape validation pin | Planned |
| REQ-005 | Required Changes bullet 5 | tests/deploy/test_required_workflow_tables_parity.py | 6 | AC-2 | parity list pin | Planned |
| REQ-006 | Required Changes bullets 6, 8 | scripts/agent/tool_approval.py | 4 | AC-4 | tests/agent/test_tool_approval_preflight.py | Planned |
| REQ-006 | Required Changes bullets 6, 8 | scripts/agent/repository_gateway.py | 4 | AC-4 | tests/agent/test_repository_gateway.py | Planned |
| REQ-006 | Required Changes bullet 6 | scripts/agent/shared/models.py | 4 | AC-4 | grant model tests in approval/gateway suites | Planned |
| REQ-006 | Required Changes bullet 8 | tests/agent/test_tool_approval_preflight.py | 1 | AC-4 | grant issuance tests | Planned |
| REQ-006 | Required Changes bullet 8 | tests/agent/test_repository_gateway.py | 1 | AC-4 | bypass/reuse tests | Planned |
| REQ-007 | Required Changes bullet 9 | scripts/agent/tool_runner.py | 5 | AC-5 | fail-closed tests in tests/agent/test_tool_runner.py | Planned |
| REQ-007 | Required Changes bullet 9 | scripts/agent/tool_audit.py | 5 | AC-5 | tests/agent/test_tool_audit.py | Planned |
| REQ-007 | Required Changes bullet 9 | scripts/agent/factory.py | 5 | AC-5 | plain-REPL intent test in tests/agent/test_tool_runner.py | Planned |
| REQ-007 | Required Changes bullet 9 | tests/agent/test_tool_audit.py | 1 | AC-5 | store-outage tests | Planned |
| REQ-008 | Required Changes bullet 10 | scripts/agent/tool_audit.py | 2 | AC-2 | tests/agent/test_audit_log_format.py | Planned |
| REQ-008 | Required Changes bullet 10 | scripts/agent/shared/models.py | 2 | AC-2 | tests/agent/test_audit_log_format.py | Planned |
| REQ-008 | Required Changes bullet 10 | tests/agent/test_audit_log_format.py | 1 | AC-2 | audit field contract tests | Planned |
| REQ-009 | Required Changes bullet 11 | scripts/agent/workflow/tool_call_state_ops.py | 5 | AC-6 | tests/agent/workflow/test_workflow_engine.py | Planned |
| REQ-009 | Required Changes bullet 11 | tests/agent/workflow/test_workflow_engine.py | 1 | AC-6 | stale-split tests | Planned |
| REQ-009 | Required Changes bullet 11 | scripts/agent/tool_runner.py | 5 | AC-6 | post-send failure transition test | Planned |
| REQ-010 | Constraints + Design (issue migrate bullet restated) | scripts/db/schema_sql.py | 6 | AC-2 | deploy-gate note validated in Phase 6 | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-225424 -->
