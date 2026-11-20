# Verify the two-layer state mapping and fail-closed behavior end to end

## Priority
Medium

## Summary
Add integration tests that prove the Agent and MCP layers use the same logical call, keep compatible state machines, execute a side effect at most once, and fail closed at every safety boundary.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 6). Unit tests cannot prove two-layer safety: the Agent can record durable intent while the MCP server uses another id, or the ledger can enforce one owner while the Agent retries an unknown outcome. Which cross-process tests already exist is `Needs confirmation`.

## Problem
Cross-process behavior (process termination, network ambiguity, store continuity, configuration drift) is tested only inside single components, if at all.

## Reason for Change
Verification of the whole defense once its parts exist; it is separate from the implementation issues because it validates behavior across processes.

## Implementation Intent
A test matrix shows that one logical call is traceable across both layers, a side effect runs at most once, ambiguous results are reconciled instead of retried, and a safety-critical storage or configuration failure rejects the write. Legacy-behavior tests stay separate as characterization tests until the behavior is removed.

## Target Files or Areas
- Agent integration tests, MCP dispatcher and dedup integration tests, workflow recovery tests, multi-process SQLite tests, and deployment and config-isolation tests (exact files `Unknown`)

## Required Changes
- Define the authoritative Agent-to-MCP state mapping.
- Test pre-dispatch denial, dispatch started, response received, completed, failed before effect, outcome unknown, reconciliation required, and replay unavailable.
- Inject an Agent crash before send, after send, and after MCP completion; inject an MCP crash before the handler, during it, after the effect, and before the response.
- Test duplicate HTTP and direct dispatch, store loss, replacement, schema and configuration fingerprint mismatch, unavailable audit and state stores, approval argument tampering, and identical arguments for independent logical calls.
- Assert at-most-once handler execution per logical call and that an unknown outcome is never rerun.

## Constraints
- Tests must not touch `/opt/llm` or any production store.
- Keep legacy-behavior tests separate as characterization tests.

## Acceptance Criteria
- [ ] Every supported state transition has an integration test.
- [ ] One logical call runs its handler at most once under concurrency.
- [ ] No side effect runs when mandatory Agent or MCP safety state is unavailable.
- [ ] Response-loss recovery uses MCP evidence and reconciliation.
- [ ] Independent calls with identical arguments both execute once.
- [ ] A store continuity failure blocks side-effecting calls.

## Testing Expectations
- The matrix above; run ruff, mypy, and the full test suite including multi-process tests.

## Documentation Impact
Yes. The authoritative state mapping and the list of proving tests, which `issues/20261119-140519_mcpai012_mcp-design-docs-update.md` links from the documentation.

## Out of Scope
- Implementation of the contracts under test.

## Dependencies
- Depends on issues/20261120-115840_mcpdl001_approval-grant-intent.md, issues/20261120-115841_mcpdl002_store-identity-continuity.md, issues/20261120-115842_mcpdl003_dedup-config-isolation.md, issues/20261120-115843_mcpdl004_call-state-control-api.md, and issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md.
- Related: `issues/20261119-140517_mcpai010_github-http-contract-tests.md` covers GitHub HTTP contracts and should not be duplicated here.

## Unresolved Questions
- `不明`: how multi-process crash injection is done in the repository's test environment.

## AI Implementation Instruction
Do not start before the implementation issues land. Reuse existing fixtures. Stop and report if a safety boundary cannot be tested without touching production data.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115845
- **Related target files**: N/A: not yet confirmed
