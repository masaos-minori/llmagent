# Establish the logical call id, approval grant, and durable Agent intent contract

## Priority
High

## Summary
Create one immutable Agent-side execution context with a single logical call id, use it as the sole identity from preparation through approval, durable intent, gateway, transport, and audit, make approval a capability that the gateway verifies against that call, and record durable intent before any side-effecting dispatch, failing closed when state or audit cannot be written.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 1), the whole item. This issue is the first of the `mcpdl` chain and is implemented first. The logical call id unification moved here from `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, which keeps only the Agent-managed replay directive and now depends on this issue.

Evidence (`Explicit in code`, by reading and `rg`): three key derivations exist today. `_idempotency_key` in `scripts/agent/tool_runner.py` (workflow, task, turn, call id) feeds audit only; `_state_key` derives the state row key from `derive_idempotency_key("call_tool", name, args, session_id)` plus the task id; `scripts/shared/http_transport.py` (line 202) derives the wire key from tool name, arguments, and session. `scripts/agent/repository_gateway.py` (docstring, lines 6-14 and 59-68) states that approval is enforced upstream by the call order in `tool_runner`, and that callers must route write or risky calls through the approval gate; the gateway does not verify an approval itself. `scripts/agent/tool_runner.py` (lines 189 and 209) catches any exception from state recording with the comment that a recording failure must not break tool execution, so durable state recording is fail-open for side-effecting calls. The tool-call state values are `pending`, `completed`, `failed`, and `interrupted` (`scripts/agent/workflow/tool_call_state_ops.py`, line 30). `ApprovalGrant` and the proposed intent states appear nowhere in the repository. That audit persistence is fail-open for side-effecting calls is a backlog claim and `Needs confirmation`. Related archived work: `issues/done/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md` identified the audit-versus-wire key mismatch.

## Problem
Audit, workflow state, and the wire carry different keys, so end-to-end correlation fails, and two distinct calls with identical arguments in one session share a transport key. Approval is guaranteed by call ordering only: if arguments change after approval, or a caller invokes the gateway directly, a side effect can bypass the authorization boundary. When Agent state or audit persistence fails, the call still executes, so after a lost response there is no durable evidence that it was approved and dispatched.

## Reason for Change
Correctness of at-most-once behavior and of authorization for side effects depends on one stable logical identity and on durable evidence. The MCP-side ledger (`issues/20261120-115841_mcpdl002_store-identity-continuity.md`), the dispatcher (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`), and recovery (`issues/20261120-115843_mcpdl004_call-state-control-api.md`) all build on this id.

## Implementation Intent
Generate one opaque logical call id exactly once and carry it, inside one immutable execution context, through every Agent-side record and onto the wire; never ask the LLM to manage it. Create an immutable grant bound to the logical call, tool, canonical argument hash, risk level, decision, issue and expiry time, and execution mode, and let the gateway verify it immediately before execution. Persist intent before dispatch and fail closed for side-effecting calls when state or mandatory audit cannot be written. Treat this as an end-to-end signature change: the transport-derived key is not kept as a fallback for side-effecting tools. The grant check is Agent-side only; the Git MCP server's own validation stays independent of Agent approval.

## Target Files or Areas
- `scripts/agent/tool_preparation.py`, `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_audit.py`, `scripts/agent/context.py`
- `scripts/agent/workflow/tool_call_state_ops.py` and the workflow tool-call state DDL and event models (exact files `Unknown`)
- `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/shared/http_transport.py`, `scripts/shared/transport_dto.py`
- `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_runner.py`, `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_transport_invoker.py`

## Required Changes
- Generate the logical call id exactly once per call as an opaque value that is not derived from credentials, session identity, tool arguments, or content hashes (a UUIDv7 is the proposal; the choice against a stable composite key is made when planning); validate length, format, whitespace, and control characters.
- Add an immutable `ToolExecutionContext` (logical call id, session, workflow, task, turn, and tool-call ids, tool name, server key, execution mode, canonical argument hash, tool-contract version, side-effect classification, execution snapshot, approval reference) to `PreparedToolCall` and carry it unchanged through `RepositoryGateway`, `ToolExecutor`, `ToolTransportInvoker`, `HttpTransport`, audit, and recovery.
- Send the id as `X-Idempotency-Key`; remove the transport-derived key (`derive_idempotency_key` in `http_transport.py`) and the alternate `_state_key()` derivation; reject a side-effecting call that carries no id; require the same id for direct side-effecting dispatch.
- Remove internal idempotency keys from LLM-facing messages.
- Migrate existing `tool_call_state` rows keyed by the old derivation without classifying an unresolved call as safe.
- Add an immutable `ApprovalGrant` bound to logical call id, tool name, canonical argument hash, risk level, decision, issue time, expiry, and execution mode.
- Require a valid grant for write, delete, external API write, and every other side-effect classification; verify it in `RepositoryGateway` before execution; reject tool, argument, mode, call, expiry, and reuse mismatches.
- Persist Agent intent before dispatch with explicit states (for example `prepared`, `dispatch_starting`, `dispatched`, `response_received`, `completed`, `outcome_unknown`, `reconciliation_required`).
- Fail closed for side-effecting calls when state recording or mandatory audit is unavailable; allow best-effort audit only for explicitly read-only calls.
- Record the logical call id in approval, workflow state, execution audit, and diagnostics; keep raw arguments, credentials, signed URLs, and raw exceptions out of audit rows.
- Treat response loss after send as `outcome_unknown`, never as an automatic retry.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (`governance_01`, `governance_05`); do not write or simulate that approval. ADR-012 INV-04 (Git MCP validation independent of Agent approval) must hold.
- The LLM never emits or edits the id; fail closed on a missing id and on ambiguity.
- Update every intermediate type and test in the same change set. Removing the fail-open recording changes behavior on purpose; list the newly failing paths.
- Follow the Current-Specification-Only policy: no compatibility path for unapproved side-effecting calls or for the transport-derived key.

## Acceptance Criteria
- [ ] Independent calls with identical arguments get different ids; a retry of the same call reuses its id.
- [ ] Agent audit, workflow state, HTTP header, and approval carry the same logical call id.
- [ ] A side-effecting call without an id cannot execute.
- [ ] An unapproved write cannot execute through `RepositoryGateway`; arguments cannot change after approval; a grant cannot be reused.
- [ ] A side effect is rejected when durable state or mandatory audit cannot be written.
- [ ] A post-send response loss becomes `outcome_unknown` and is not retried automatically.

## Testing Expectations
- End-to-end id propagation from preparation to the HTTP header; same-call retry and different-call-same-arguments; missing-id rejection for side-effecting tools.
- Direct gateway invocation without approval; argument and execution-mode mismatch; expiry and reuse; audit and state store outage for side-effecting and read-only calls.
- Run ruff, mypy, import-linter, and the full test suite.

## Documentation Impact
Yes. The identifiers (workflow, task, turn, call, session, request, id) in one place, the approval capability, the intent states, and the fail-closed failure behavior; the final sweep is `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`.

## Out of Scope
- The Agent-managed replay directive (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`), which builds on this id.
- The MCP-side ledger and store identity (`issues/20261120-115841_mcpdl002_store-identity-continuity.md`); the dispatcher integration (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`).
- Reconciliation and result replay (`issues/20261120-115843_mcpdl004_call-state-control-api.md`).

## Dependencies
- No prerequisite: this is the first issue of the `mcpdl` chain and owns the logical call id and the Agent-side state vocabulary. Blocks `issues/20261120-115841_mcpdl002_store-identity-continuity.md` (ledger key format), `issues/20261120-115843_mcpdl004_call-state-control-api.md`, `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`, and `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` (replay directive).
- Other issues that cite `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` for the propagated id (`issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`) are satisfied by this issue and may start once it lands.
- Related: `issues/20261119-140514_mcpai007_dedup-audit-observability.md` (audit identifiers), `issues/20261119-140512_mcpai005_structured-execution-context.md` (execution mode; the MCP-side context must use the field names defined here).

## Unresolved Questions
- `不明`: key composition (opaque UUIDv7 versus a stable composite string).
- `不明`: the exact set of Agent state values, and where the migration of `tool_call_state` rows is applied.
- `不明`: grant lifetime and whether it is configured in `agent.toml` (see `issues/20261120-115842_mcpdl003_dedup-config-isolation.md`).
- `不明`: whether audit writes are already mandatory for side-effecting calls today.

## AI Implementation Instruction
Change the type chain end to end in one change set, tests first, and write the bypass and outage tests before the grant. Keep grant verification in the Agent and leave the MCP-side validation independent. Do not write ADR approval statements. Stop and report if a caller cannot obtain a grant or an id.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115840
- **Related target files**: `scripts/agent/tool_preparation.py`, `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_audit.py`, `scripts/agent/context.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/shared/http_transport.py`, `scripts/shared/transport_dto.py`, `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_runner.py`, `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_transport_invoker.py`
