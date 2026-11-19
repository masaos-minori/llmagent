# Reconcile GitHub Actions workflow dispatch and enforce safe retry behavior

## Priority
High

## Summary
Treat workflow dispatch as an external side effect that needs explicit run reconciliation, a stable execution identity, and conservative retry behavior.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 6). A successful dispatch response confirms acceptance, not run creation; the current implementation reporting immediate success without a run id is a backlog claim and `Needs confirmation`. `trigger_workflow` is in `CICD_WRITE_TOOLS` (`scripts/shared/tool_constants.py:75`).

## Problem
Response loss or a crash after dispatch can lead to a retry that starts a duplicate workflow, and the result gives no run id to reconcile against.

## Reason for Change
External side-effect safety; token, key, and dry-run contracts must be final first.

## Implementation Intent
Return structured states `accepted`, `confirmed`, `accepted_unconfirmed`, `outcome_unknown`, and `reconciliation_required`. Search for the original run before any repeat dispatch of the same logical call. Never retry ambiguous outcomes automatically; keep `trigger_workflow` explicitly non-retryable until reconciliation is proven.

## Target Files or Areas
- `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `cicd_service_github_actions_composite.py`
- CI/CD dispatch response models and formatter; CI/CD dedup integration
- Workflow-dispatch tests under `tests/mcp_servers/cicd/` (`test_cicd_mcp_service.py`, `test_service_github_actions_composite.py`, `test_service_github_actions_error_edges.py`)
- Design documentation (location of `22_mcp_all.md` `不明`)

## Required Changes
- Return `accepted` after the dispatch API succeeds; add a correlation marker to workflow inputs when the workflow contract allows it, with a fallback correlation on workflow identifier, ref, actor, and dispatch time.
- Poll for the matching run with bounded timeout and interval; return `confirmed` (run id, URL, status, workflow, ref) on a unique match, `accepted_unconfirmed` when none is found, `reconciliation_required` for multiple candidates, `outcome_unknown` for response loss or timeout.
- Search for an existing run before re-dispatching the same logical call; fail closed when durable deduplication is unavailable.
- Redact workflow input values from previews and recovery output (keys and counts only).

## Constraints
- 2xx never becomes `confirmed` without a matched run.
- `accepted_unconfirmed` and `outcome_unknown` are never retried automatically.

## Acceptance Criteria
- [ ] A confirmed dispatch returns the matching run id and URL.
- [ ] Missing, delayed, and ambiguous run creation have distinct outcomes.
- [ ] Response-loss recovery searches before dispatching again; ambiguous outcomes are never retried automatically.
- [ ] Workflow input values do not appear in previews, logs, or recovery messages.

## Testing Expectations
- Confirmed run creation, creation delay, no run, multiple matching runs, response loss and server crash after acceptance, dedup-store failure, and preview redaction; replace immediate-success tests with the structured-state contract.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. The five states, the correlation and polling strategy, and why automatic retry stays disabled; remove any statement that a dispatch response proves run creation.

## Out of Scope
- Credential and configuration contract (`issues/20261119-141106_mcpci001_cicd-credential-config-contract.md`); log retrieval (`issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`).

## Dependencies
- Depends on `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` (required keys), `issues/20261119-141106_mcpci001_cicd-credential-config-contract.md` (credential contract), `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (recovery-state semantics), and `issues/20261119-140512_mcpai005_structured-execution-context.md` (structured execution result).
- Can run in parallel with `issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md` once `issues/20261119-141106_mcpci001_cicd-credential-config-contract.md` is complete.

## Unresolved Questions
- `不明`: whether target workflows can accept a correlation input.
- `不明`: polling timeout and interval values.

## AI Implementation Instruction
Do not make `trigger_workflow` retryable. Write the response-loss and multiple-match tests first. Stop and report if a correlation marker cannot be added without changing the workflow contract.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141109
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`
