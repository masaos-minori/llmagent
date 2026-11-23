# Integrate the atomic ownership ledger into the MCP dispatcher

## Priority
High

## Summary
Make the shared MCP dispatcher act only on the typed acquisition result of the atomic ownership ledger (`issues/20261120-115841_mcpdl002_store-identity-continuity.md`): refuse execution while another owner holds a fresh lease, keep long-running handlers protected by heartbeat renewal, finalize only as the current owner, and return explicit results for in-progress, interrupted, reconciliation-required, review-required, and replay-unavailable calls, so that exactly one caller executes a logical call at a time.

## Background
Source: consolidated MCP server review backlog (`memo-issue.md`, Issue 3). The storage half of this item (atomic acquisition, lease and attempt columns, immutable terminal evidence, attempt history, removal of the `force` path, store identity) moved to `issues/20261120-115841_mcpdl002_store-identity-continuity.md`, which this issue depends on; this issue keeps the dispatcher side. It is on the critical path `mcpdl001 -> mcpdl002 -> mcpai001 -> mcpai004 -> mcpai005 -> mcpai010 -> mcpai012`. Related archived work: `issues/done/20261109-112844_adrrev008_mcp-dedup-ownership.md` (store classified as a disposable cache, Option B) and `issues/done/20261117-123018_adrchk018_mcp-retry-classes.md`; re-verify this issue if either changed the store contract.

Evidence (`Explicit in code`, by reading): `scripts/mcp_servers/dispatch.py` loads the store lazily; `_dedup_context()` (lines 160-177) catches any exception and falls back to overlay-only behavior ("fail-open by design"); its result type carries `dedup_state` and the outcomes `idempotency_key_reused`, `dedup_unreplayable`, and `dedup_store_error` (docstring, lines 50-63). The remaining claims below come from the review and are `Needs confirmation` against the current dispatcher.

## Problem
- Two concurrent callers can both observe no active owner and both execute the same handler (`Needs confirmation`: reproduce with a dispatcher concurrency test first).
- A retryable classification can make fresh pending, interrupted, and failed states be handled too similarly (`Needs confirmation`).
- A snapshot mismatch or a truncated stored result can lead the dispatcher to execute the same logical call again, although code or configuration drift does not prove a prior external side effect is safe to repeat (`Needs confirmation`).

## Reason for Change
Duplicate execution of external side effects is a correctness and data-integrity risk, and the later issues (replay directive, dry-run context, GitHub retry policy, observability) depend on the dispatcher behavior defined here. No external deadline is known.

## Implementation Intent
The dispatcher calls the single acquisition operation of `issues/20261120-115841_mcpdl002_store-identity-continuity.md` and acts only on its typed result. Active ownership is a renewable lease that the dispatcher keeps alive while a handler runs. Retryability is a property of a known recovery procedure, not of the transport. Change the dispatcher and the storage in one release so old code never misreads new states. Keep human-readable output separate from control metadata.

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py`
- `scripts/shared/execution_snapshot.py` (snapshot compatibility data used by the dispatcher)
- `tests/mcp_servers/test_mcp_dispatch.py` and new dispatcher concurrency tests (they do not exist yet and are created here)
- The lease and timing settings come from the typed configuration of `issues/20261120-115842_mcpdl003_dedup-config-isolation.md`; `config/mcp_dedup.toml` is removed there and is not edited here.

## Required Changes
- Replace the separate lookup and pending write in the dispatcher by the typed acquisition operation of `issues/20261120-115841_mcpdl002_store-identity-continuity.md`.
- Refuse execution while a fresh lease exists and return `dedup_in_progress`.
- Renew the lease by heartbeat while a long-running handler executes; move only expired leases to interrupted, and treat expiry as a reconciliation trigger, never as retry permission.
- Finalize completed and failed outcomes only as the current owner; a rejected finalization (zero updated rows) is ownership loss and is reported, not ignored.
- Separate the interrupted and failed recovery policies; permit automatic replay only for explicitly reconcilable operations allowed by policy.
- Return `review_required` for snapshot mismatch, code or schema incompatibility, and truncated stored results; never invoke the handler automatically in those cases.
- Expose the states `in_progress`, `interrupted`, `reconciliation_required`, and `review_required` in tool results; the final vocabulary is decided in `issues/20261120-115841_mcpdl002_store-identity-continuity.md`.
- Remove lookup-plus-record patterns and content-derived key use from the dispatcher's production paths (the id itself comes from `issues/20261120-115840_mcpdl001_approval-grant-intent.md`).
- Define the shared dispatcher rule that a non-retryable side-effecting tool fails closed when the durable dedup store is unavailable (the registered ADR-004 overlay-only exception for retryable tools is unchanged); the GitHub, MDQ, and CI/CD issues classify their own tools and reuse this rule instead of redefining it.

## Constraints
- Exactly-once execution must hold across async callers, connections, and processes; the dispatcher never holds a SQLite transaction open during handler execution.
- A change to an ADR decision, invariant, or authority edge needs a maintainer approval record in the same change (`governance_01`, `governance_05`); do not write or simulate that approval. The ADR-008 and ADR-004 questions are owned by `issues/20261120-115841_mcpdl002_store-identity-continuity.md`.
- The storage DDL change forces database recreation; plan the rollout together with `issues/20261120-115841_mcpdl002_store-identity-continuity.md`.
- The overlay-only fallback for a retryable tool whose dedup store is unavailable (`_dedup_context()`) and the warning-only handling of a failed store write after a successful open are ADR-004 exceptions that the governance inventory lists without a maintainer approval record (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`, Known Issues MCP-001 and MCP-002). Keep their behavior unchanged here, do not treat them as approved, and do not write the approval.

## Acceptance Criteria
- [ ] Exactly one caller executes the handler for a new logical call, and concurrent callers do not execute it.
- [ ] Fresh in-progress calls are never replayed; long-running active calls stay protected by heartbeat renewal.
- [ ] Only expired leases become interrupted; failed and interrupted recovery follow separate policies.
- [ ] Completion and failure updates require the current owner.
- [ ] Snapshot mismatch and truncated stored results return `review_required` and do not invoke the handler.
- [ ] A non-retryable side-effecting tool is rejected when the durable store is unavailable.

## Testing Expectations
- One key submitted by 100 concurrent async callers executes the handler exactly once through the dispatcher.
- Owner-mismatch completion and failure rejection; fresh-in-progress before lease expiry and boundary tests immediately before and after expiry; heartbeat for long-running handlers.
- Snapshot-mismatch tests expecting `review_required` and preserved terminal evidence; truncated-result tests that do not re-execute; store-unavailable tests for retryable and non-retryable tools.
- Run ruff, mypy, import-linter, the schema and fingerprint checks, and the full test suite.

## Documentation Impact
Yes. Document the dispatcher behavior for each state and the recovery policies as intent, boundaries, and failure behavior (ADR-008 and the dedup design section). The final documentation sweep is tracked by `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`.

## Out of Scope
- The ledger schema, ownership primitives, and store identity (`issues/20261120-115841_mcpdl002_store-identity-continuity.md`); the logical call id, approval, and intent (`issues/20261120-115840_mcpdl001_approval-grant-intent.md`).
- Propagating the id and replay directives (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`); dry-run and execution-context contract (`issues/20261119-140512_mcpai005_structured-execution-context.md`).
- GitHub-specific retry classification and reconciliation (`issues/20261119-140513_mcpai006_github-write-retry-policy.md`); Agent audit and transport DTO fields (`issues/20261119-140514_mcpai007_dedup-audit-observability.md`).

## Dependencies
- Depends on `issues/20261120-115841_mcpdl002_store-identity-continuity.md` (ledger primitives and state vocabulary) and, through it, on `issues/20261120-115840_mcpdl001_approval-grant-intent.md`.
- Blocks `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, `issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md`, and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`: they rely on the dispatcher states and result contract.
- Related: `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` carries the server-side keyless rejection and shipped-configuration hardening and follows this issue; `issues/20261120-115842_mcpdl003_dedup-config-isolation.md` removes `config/mcp_dedup.toml`; `issues/20261120-115843_mcpdl004_call-state-control-api.md` consumes the states.
- Also relied on by `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md` and `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md` for the shared fail-closed rule above.

## Unresolved Questions
- `不明`: whether the dispatcher already serializes acquisition in-process (the review claims it does not); confirm by the dispatcher concurrency test before changing it.
- `不明`: heartbeat interval and lease duration values (set in `issues/20261120-115841_mcpdl002_store-identity-continuity.md` and `issues/20261120-115842_mcpdl003_dedup-config-isolation.md`).
- `不明`: the final state vocabulary, decided once in `issues/20261120-115841_mcpdl002_store-identity-continuity.md` together with `issues/20261120-115843_mcpdl004_call-state-control-api.md` and `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`.
- `不明`: whether the maintainer approves or removes the two ADR-004 exceptions above (MCP-001, MCP-002); a removal would change the dispatcher rule defined in this issue.

## AI Implementation Instruction
Write the 100-caller dispatcher concurrency test first and confirm it fails on current code. Change the dispatcher and the storage of `issues/20261120-115841_mcpdl002_store-identity-continuity.md` in one release. Do not touch unrelated files, do not implement out-of-scope items, and do not write maintainer approval statements. Stop and report if the store contract conflicts with ADR-008.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140508
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `scripts/shared/execution_snapshot.py`, `tests/mcp_servers/test_mcp_dispatch.py`
