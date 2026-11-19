# Redesign MCP durable deduplication as an atomic ownership and recovery state machine

## Priority
High

## Summary
Replace the lookup-then-record durable deduplication flow with atomic execution ownership, renewable leases, immutable terminal evidence, and explicit handling of pending, interrupted, failed, truncated, and snapshot-mismatched calls, so that exactly one caller owns a logical execution at a time.

## Background
Source: consolidated MCP server review backlog (`memo-issue.md`, Issue 3). It is the foundation of the critical path `mcpai001 -> mcpai004 -> mcpai005 -> mcpai010 -> mcpai012`. Related archived work: `issues/done/20261109-112844_adrrev008_mcp-dedup-ownership.md` (store classified as a disposable cache, Option B) and `issues/done/20261117-123018_adrchk018_mcp-retry-classes.md` (retry class sources). This issue must be re-verified against current source if either decision changed the store contract.

Evidence checked in this session (`Explicit in code`, by `rg`): `scripts/shared/mcp_dedup.py` exposes separate `record_pending` (line 310), `lookup` (line 390), `record_completed`, `record_failed`, and `mark_interrupted`; writes use `BEGIN IMMEDIATE` per call, but lookup and pending write are separate transactions. The remaining claims below come from the review and are `Needs confirmation` against the current dispatcher.

## Problem
- Two concurrent callers can both observe no active owner and both execute the same handler (`Needs confirmation`: reproduce with a concurrency test first).
- A retryable classification can make fresh pending, interrupted, and failed states be handled too similarly (`Needs confirmation`).
- A snapshot mismatch or a truncated stored result can reset a terminal row to pending and execute the same logical key again, although code or configuration drift does not prove a prior external side effect is safe to repeat. Overwriting terminal rows also destroys reconciliation evidence (`Needs confirmation`).

## Reason for Change
Duplicate execution of external side effects is a correctness and data-integrity risk, and every later item of the backlog (key unification, dry-run context, GitHub retry policy, observability) depends on the state and result contract defined here. No external deadline is known.

## Implementation Intent
Guarantee one owner per logical execution through a single transactional acquire operation. Represent active ownership with an owned, renewable lease; never reuse `created_epoch` as a lease. Keep terminal rows and their original snapshots immutable and record further attempts in a separate attempt-history table. Treat retryability as a property of a known recovery procedure, not of the transport. Change the storage and the dispatcher in one change set so old code never misreads new states. Keep human-readable output separate from control metadata.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py`
- `scripts/mcp_servers/dispatch.py`
- `scripts/shared/execution_snapshot.py`
- MCP dedup DDL, schema fingerprint, and `db_schema_versions.yaml` entry
- `config/mcp_dedup.toml`
- Dedup and dispatch tests under `tests/shared/` and `tests/mcp_servers/` (new concurrency test files do not exist yet and are created here)

## Required Changes
- Replace separate lookup and pending write with `try_acquire_execution()`: row lookup, state classification, and ownership acquisition in one `BEGIN IMMEDIATE` transaction.
- Add `owner_id`, `lease_expires_epoch`, and `attempt_number`; return a structured acquisition result (`acquired`, state, owner, retry or review guidance).
- Refuse execution while a fresh pending lease exists and return `dedup_in_progress`.
- Add heartbeat-based lease renewal for long-running handlers; move only expired leases to interrupted.
- Separate interrupted and failed recovery policies; permit automatic replay only for explicitly reconcilable operations allowed by policy.
- Make completed and failed updates conditional on the current owner; treat a zero-row update as ownership loss.
- Return `review_required` for snapshot mismatch, code or schema incompatibility, and truncated stored results; never invoke the handler automatically in those cases.
- Preserve terminal rows and original snapshots; add an attempt-history table.
- Add the dedup schema fingerprint to execution compatibility data.
- Expose the states `in_progress`, `interrupted`, `reconciliation_required`, and `review_required`.

## Constraints
- Exactly-once ownership must hold across async callers, connections, and processes.
- Existing incompatible dedup databases must be rejected by the schema and fingerprint gate; the old table must not be silently reinterpreted.
- ADR-008 Decision Details 22 and 23 (shape mismatch archives and recreates, no migration; unbounded growth accepted) and the disposable-cache classification from adrrev008 apply. A change to an ADR decision, invariant, or authority edge needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate that approval.
- A `schema.sql`-style DDL change forces database recreation; plan the rollout accordingly.

## Acceptance Criteria
- [ ] Exactly one caller can acquire a new logical key, and concurrent callers do not execute the handler.
- [ ] Fresh pending calls are never replayed; long-running active calls stay protected by heartbeat renewal.
- [ ] Only expired leases can transition to interrupted.
- [ ] Failed and interrupted recovery follow separate policies.
- [ ] Completion and failure updates require the current owner.
- [ ] Snapshot mismatch and truncated stored results return `review_required` and do not invoke the handler.
- [ ] Original results, snapshots, and timestamps remain available for audit and reconciliation.
- [ ] Existing incompatible dedup databases are rejected by the schema and fingerprint gate.

## Testing Expectations
- One key submitted by 100 concurrent async callers executes the handler exactly once.
- Multi-connection and multi-process ownership tests.
- Owner-mismatch completion and failure rejection tests.
- Fresh-pending tests before lease expiry; boundary tests immediately before and after expiry.
- Heartbeat tests for long-running handlers.
- Snapshot-mismatch tests expecting `review_required` and preserved terminal evidence; truncated-result tests that do not re-execute.
- Run ruff, mypy, lint-imports, the schema and fingerprint checks, and the full test suite.

## Documentation Impact
Yes. Document the ownership and lease state machine, the new states, and the recovery policies as intent, boundaries, and failure behavior (ADR-008 and the dedup design section). The final documentation sweep is tracked by `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`.

## Out of Scope
- Propagating the logical idempotency key and replay directives (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`).
- Dry-run and execution-context contract (`issues/20261119-140512_mcpai005_structured-execution-context.md`).
- GitHub-specific retry classification and reconciliation (`issues/20261119-140513_mcpai006_github-write-retry-policy.md`).
- Agent audit and transport DTO fields (`issues/20261119-140514_mcpai007_dedup-audit-observability.md`).

## Dependencies
- Blocks `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, `issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md`, and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`: they rely on the new states and result contract. Implement this issue first.
- Related: `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` carries the server-side keyless rejection and shipped-configuration hardening; implement it after this issue.
- No open dependency on other issues or plans (sibling check found no open issue or plan sharing the target files; `plans/` holds only adrchk010 and ragcrv002 plans).

## Unresolved Questions
- `不明`: whether the new states and attempt-history table are consistent with the disposable-cache classification of `mcp_dedup.sqlite` (adrrev008); if immutable evidence must outlive the cache, an ADR-008 change with approval is needed.
- `不明`: heartbeat interval and lease duration values.
- `不明`: state name for a truncated stored result (`review_required` here; the later Web Search and CI/CD backlog calls it `replay_unavailable`); decide one name when planning.
- `不明`: whether the current dispatcher already serializes acquisition in-process (the review claims it does not); confirm by the concurrency test before changing storage.

## AI Implementation Instruction
Write the 100-caller concurrency test first and confirm it fails on current code. Change storage and dispatcher together. Do not touch unrelated files, do not implement out-of-scope items, and do not write maintainer approval statements. Stop and report if the store contract conflicts with ADR-008.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140508
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `scripts/shared/execution_snapshot.py`, `config/mcp_dedup.toml`
