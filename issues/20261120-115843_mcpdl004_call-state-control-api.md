# Add an Agent-only call-state API, reconciliation contract, and secure result replay

## Priority
High

## Summary
Let the Agent query structured call state from the MCP server after response loss, run tool-specific reconciliation, and receive a complete result, a secure reference, or explicit replay-unavailable evidence, without re-executing completed side effects.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 4). Tool-specific reconcilers are carried by the existing tool issues listed under Dependencies; this issue defines the shared contract and the result storage.

Evidence (`Explicit in code`, by reading and `rg`): `scripts/mcp_servers/server.py` exposes the `/v1/call_tool` and `/v1/tools` endpoints and no call-state or reconciliation endpoint (negative `rg`, `Needs confirmation` for other modules). `scripts/shared/mcp_dedup.py` keeps a result preview of `RESULT_PREVIEW_CHARS = 1000` characters plus a hash for a result that is too large (lines 44-47 and 217-247), so a replay of such a result returns a truncated sentinel. The behavior claims about duplicated Git pushes, workflow dispatches, deletions, and merges after a lost response are backlog claims and `Needs confirmation`.

## Problem
After a network failure or Agent crash the Agent cannot know whether the side effect was applied; lease expiry proves only that the process stopped renewing ownership. A redacted preview and a hash show that a call completed but are not a complete response, and re-executing to recover output is unsafe.

## Reason for Change
Recovery of side-effecting calls without duplication. State retrieval, reconciliation, and replay form one contract: separating them would let the Agent learn that a call completed with no safe way to read its result.

## Implementation Intent
Add authenticated control operations, authorized separately from ordinary tool calls, that return logical call state, attempt state, dispatch evidence, result availability, a stable error code, and whether reconciliation is required, never raw arguments, credentials, signed URLs, raw exceptions, or internal paths. Define a reconciler contract that the tools implement. Classify a result as complete and replayable, a secure reference, a redacted preview, or `replay_unavailable`, and never re-execute because a full result is missing.

## Target Files or Areas
- `scripts/mcp_servers/server.py`, `scripts/mcp_servers/dispatch.py`, `scripts/shared/mcp_dedup.py`
- Agent transport and workflow recovery services (exact files `Unknown`)
- Reconciliation helpers for Git, GitHub, CI/CD, filesystem, and indexing (exact files `Unknown`)
- MCP authentication and authorization middleware

## Required Changes
- Add authenticated, Agent-only call-state and reconciliation operations with their own authorization.
- Define the reconciler contract: reuse completed evidence, never rerun an active, unknown, or ambiguous call, require operator review for multiple candidates or an unverifiable outcome, and record evidence and decision without raw sensitive payloads.
- Store content hash, byte size, stable result code, external object id, full-result availability, and an optional secure reference; apply redaction before creating previews; define encryption, access control, and retention for stored full results.
- Map MCP state into Agent states (`completed`, `in_progress`, `outcome_unknown`, `reconciliation_required`) in the Agent recovery service; remove internal idempotency keys from LLM-facing messages.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- The control operations must not widen what ordinary tool authorization allows; full-result storage must not become a way to read data the caller could not read.
- Follow the Current-Specification-Only policy.

## Acceptance Criteria
- [ ] The Agent can query MCP state after response loss.
- [ ] Completed and active calls are not re-executed; ambiguous outcomes require reconciliation or operator review.
- [ ] A caller can tell a complete result, a secure reference, a redacted preview, and replay-unavailable evidence apart.
- [ ] The control operations are Agent-only.
- [ ] Sensitive data is absent from normal responses and ledger previews.

## Testing Expectations
- Workflow dispatch accepted but response lost; Git remote update reconciliation; file deletion already completed; ambiguous external result; complete result and secure reference retrieval; replay-unavailable result does not rerun the handler; unauthorized control access.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. The control operations, the reconciler contract, the result classes, and the failure behavior.

## Out of Scope
- The ledger ownership and lease redesign (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); the Agent approval and intent states (issues/20261120-115840_mcpdl001_approval-grant-intent.md); retention (issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, and issues/20261120-115840_mcpdl001_approval-grant-intent.md. Blocks issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md and issues/20261120-115845_mcpdl006_two-layer-failure-verification.md.
- Related: `issues/20261119-140513_mcpai006_github-write-retry-policy.md` and `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md` implement tool-specific reconciliation on this contract; `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md` and `issues/20261119-140516_mcpai009_file-mcp-hardening.md` cover Git and file outcomes.

## Unresolved Questions
- `不明`: where full results are stored and how they are encrypted.
- `不明`: how `review_required` (mcpai001) and `replay_unavailable` are named in one vocabulary.
- `不明`: which tool classes get a reconciler.

## AI Implementation Instruction
Define the contract with tests before adding reconcilers. Do not add a path that re-executes a handler to recover output. Do not write ADR approval statements. Stop and report if a control operation cannot be authorized separately.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115843
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/dispatch.py`, `scripts/shared/mcp_dedup.py`
