# Implement Agent-managed replay on the unified logical call id

## Priority
High

## Summary
Reuse the logical call id through a one-time Agent-managed replay directive, so that an approved, reissued call after an interruption reconnects to the original durable state while the LLM never sees, emits, or edits the id.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 4). The id unification itself (single generation, execution context, propagation, removal of the three derivations, keyless rejection, state-row migration) moved to `issues/20261120-115840_mcpdl001_approval-grant-intent.md`, which this issue depends on; this issue keeps only the replay directive. Follow-on of archived `issues/done/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`, which identified the audit-versus-wire key mismatch.

Evidence (`Explicit in code`, by reading `scripts/agent/tool_runner.py` and `rg`): the key derivations that replay must reconnect to are listed in `issues/20261120-115840_mcpdl001_approval-grant-intent.md`. The claims that the LLM is asked to reissue a call with no binding to the stored key, and that workflow recovery shows the old key to the LLM, are from the review and `Needs confirmation`.

## Problem
A reissued call gets a new call id and normally a different identity, so recovery cannot reconnect to the original durable state even once the id is stable.

## Reason for Change
At-most-once behavior after an interruption needs the reissued call to reuse the original id under Agent control. Final acceptance needs the dispatcher states of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`.

## Implementation Intent
On recovery the Agent internally attaches the original id to an approved reissued call through a one-time `ReplayDirective` held in Agent-controlled context, not in tool arguments or editable LLM text. No directive is created for a non-retryable or outcome-unknown operation. Fail closed on ambiguity.

## Target Files or Areas
- `scripts/agent/tool_preparation.py` (directive matching during preparation)
- `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/conversation_state_manager.py` (replay injection path; existence confirmed, current content `Needs confirmation`)
- Tests: `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_tool_runner.py`; the adapter test named by the review (`tests/agent/test_workflow_engine_adapter.py`) is not a tracked file (`Needs confirmation`)

## Required Changes
- Add `ReplayDirective` (original id, task id, original call id, tool name, canonical argument hash); match a reissued call during preparation and attach the original id; consume each directive once.
- Fail with a structured ambiguity error when several directives match; create no directive for non-retryable or outcome-unknown operations.
- Persist directives so that they survive a restart, or document why they need not.

## Constraints
- Fail closed on ambiguity.
- The LLM never emits or edits the id.
- Update every intermediate type and test of the replay path in the same change set.

## Acceptance Criteria
- [ ] Interrupted approved calls reuse the original id through Agent logic; the LLM never needs to emit or modify it.
- [ ] Ambiguous replay matching fails closed; a directive cannot be used twice.
- [ ] No directive exists for a non-retryable or outcome-unknown operation.

## Testing Expectations
- Interrupted-to-reissued-to-completed integration test; ambiguous replay rejection and one-time consumption; no directive for non-retryable operations.
- Run ruff, mypy, import-linter, and the full test suite.

## Documentation Impact
Yes. The Agent-managed replay in one place, next to the identifier definitions of `issues/20261120-115840_mcpdl001_approval-grant-intent.md` (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- The logical call id, execution context, propagation, keyless rejection, and state-row migration (`issues/20261120-115840_mcpdl001_approval-grant-intent.md`).
- Dispatcher and ledger semantics (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261120-115841_mcpdl002_store-identity-continuity.md`); dedup state and turn id audit fields (`issues/20261119-140514_mcpai007_dedup-audit-observability.md`); dry-run context (`issues/20261119-140512_mcpai005_structured-execution-context.md`).

## Dependencies
- Depends on `issues/20261120-115840_mcpdl001_approval-grant-intent.md` (the logical call id) and `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (replay-state semantics in the dispatcher).
- Issues that cite this issue for the propagated id (`issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`, `issues/20261119-140517_mcpai010_github-http-contract-tests.md`) get the id from `issues/20261120-115840_mcpdl001_approval-grant-intent.md` and need not wait for replay.
- Related: `issues/20261120-115843_mcpdl004_call-state-control-api.md` reads the id for call-state queries and owns recovery.

## Unresolved Questions
- `不明`: where replay directives are persisted so they survive restart (the review lists adapter and conversation-state files as needed reading).

## AI Implementation Instruction
Keep the replay directive out of tool arguments and LLM text. Do not implement out-of-scope items; stop and report if the replay injection path cannot be located.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140511
- **Related target files**: `scripts/agent/tool_preparation.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/conversation_state_manager.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_tool_runner.py`
