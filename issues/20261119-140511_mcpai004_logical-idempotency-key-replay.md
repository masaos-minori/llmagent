# Unify logical idempotency keys and implement Agent-managed replay

## Priority
High

## Summary
Create one logical idempotency key per tool call at the Agent boundary, propagate it unchanged through workflow state, audit, gateway, executor, HTTP transport, and MCP deduplication, and reuse it through a one-time Agent-managed replay directive.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 4). Follow-on of archived `issues/done/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`, which identified the audit-versus-wire key mismatch.

Evidence (`Explicit in code`, by reading `scripts/agent/tool_runner.py` and `rg`): `_idempotency_key` (workflow, task, turn, call id) feeds audit only; `_state_key` derives the state row key from `derive_idempotency_key("call_tool", name, args, session_id)` plus the task id; `scripts/shared/http_transport.py:202` derives the wire key from tool name, arguments, and session. Three derivations exist. The replay-directive claims (the LLM is asked to reissue a call with no binding to the stored key) are from the review and `Needs confirmation`.

## Problem
Audit, workflow state, and the wire carry different keys, so end-to-end correlation fails, and two distinct logical calls with identical arguments in one session share a transport key. Workflow recovery shows the old key to the LLM, but a reissued call gets a new call id and normally a different identity, so recovery cannot reconnect to the original durable state.

## Reason for Change
Correctness of at-most-once behavior for side effects depends on a stable logical identity. Final acceptance needs the durable ownership semantics of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`.

## Implementation Intent
One key identifies one logical call: generate it once, carry it unchanged, never ask the LLM to manage it. On recovery the Agent internally attaches the original key to an approved reissued call through a one-time `ReplayDirective` held in Agent-controlled context, not in tool arguments or editable LLM text. Treat this as an end-to-end signature change; do not keep the transport-derived key as an automatic fallback for side-effecting tools.

## Target Files or Areas
- `scripts/agent/tool_preparation.py`, `tool_runner.py`, `repository_gateway.py`, `context.py`
- `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/conversation_state_manager.py` (replay injection path; existence confirmed, current content `Needs confirmation`)
- `scripts/shared/tool_executor.py`, `tool_transport_invoker.py`, `http_transport.py`, `transport_dto.py`
- Tests: `tests/agent/test_tool_runner.py`, `tests/agent/test_repository_gateway.py`, `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/agent/test_workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py` (existence `Needs confirmation`)

## Required Changes
- Add `idempotency_key` to `PreparedToolCall`, generated once from workflow id, task id, turn id, and original call id (or an equivalent stable UUID contract).
- Pass it through RepositoryGateway, ToolExecutor, ToolTransportInvoker, and HttpTransport; put the exact value in `X-Idempotency-Key`; use the same key in workflow state and audit; keep session id as correlation metadata only.
- Reject side-effecting calls when the key is absent.
- Add `ReplayDirective` (original key, task id, original call id, tool name, canonical argument hash); match a reissued call during preparation and attach the original key; consume each directive once; fail with a structured ambiguity error when several directives match; create none for non-retryable or outcome-unknown operations.
- Remove or deprecate the alternate `_state_key()` derivation after migration.

## Constraints
- Fail closed on ambiguity and missing key.
- The LLM never emits or edits the key.
- Update every intermediate type and test in the same change set.

## Acceptance Criteria
- [ ] Agent audit, workflow state, HTTP header, and MCP dedup database contain the same logical key.
- [ ] HTTP retries of one logical call reuse the key; a different logical call with identical tool and arguments gets a different key.
- [ ] Side-effecting calls cannot execute without the key.
- [ ] Interrupted approved calls reuse the original key through Agent logic; the LLM never needs to emit or modify it.
- [ ] Ambiguous replay matching fails closed; a directive cannot be used twice.

## Testing Expectations
- End-to-end key propagation from preparation to HTTP header and MCP store.
- Same-call retry and different-call-same-arguments tests; missing-key rejection for side-effecting tools.
- Interrupted-to-reissued-to-completed integration test; ambiguous replay rejection and one-time consumption.
- Run ruff, mypy, lint-imports, and the full test suite.

## Documentation Impact
Yes. Define the identifiers (workflow, task, turn, call, session, request, key) and the Agent-managed replay in one place (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`); remove comments that call the transport key the call identity.

## Out of Scope
- Dedup storage semantics (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); dedup state and turn id audit fields (`issues/20261119-140514_mcpai007_dedup-audit-observability.md`); dry-run context (`issues/20261119-140512_mcpai005_structured-execution-context.md`).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` for final ownership, attempt, and replay-state semantics; signature changes may start in parallel, end-to-end acceptance requires it.
- Blocks `issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`, and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`: their acceptance uses the propagated key.
- Re-verify against archived `issues/done/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md` before planning.

## Unresolved Questions
- `不明`: key composition (stable composite string versus UUID).
- `不明`: where replay directives are persisted so they survive restart (the review lists adapter and conversation-state files as needed reading).
- `不明`: migration of existing `tool_call_state` rows keyed by the old derivation.

## AI Implementation Instruction
Change the type chain end to end in one change set, tests first. Keep the transport-derived key out of side-effecting paths. Do not implement out-of-scope items; stop and report if the replay injection path cannot be located.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140511
- **Related target files**: `scripts/agent/tool_preparation.py`, `scripts/agent/tool_runner.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/context.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/shared/http_transport.py`, `scripts/shared/transport_dto.py`
