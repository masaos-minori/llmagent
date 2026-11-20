# Make dedup retention state-aware and monitor store capacity and health

## Priority
Medium

## Summary
Replace age-only purge with retention that depends on the call state, and add controls and monitoring for store size, WAL growth, lock contention, lease health, store identity, and reconciliation backlog.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 5).

Evidence (`Explicit in code`, by reading): `scripts/shared/mcp_dedup.py` purges by age only (`purge_expired(retention_days)`, lines 399-424), with `retention_days = 14` in the shipped `config/mcp_dedup.toml`, and sets `PRAGMA journal_mode = WAL` (line 271). `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` cites ADR-008 Decision Detail 23 (unbounded growth accepted) as a constraint; re-verify it first. The absence of capacity, lock-wait, and lease monitoring is from the backlog and `Needs confirmation`.

## Problem
An execution ledger is safety evidence. Entries in an unknown, reconciliation-required, interrupted, or replay-unavailable state may be the only records that prevent a duplicate side effect, and age-based purge deletes them. Without monitoring, lock waits, stalled heartbeats, WAL growth, or incompatible settings can silently stop writes or weaken recovery.

## Reason for Change
Retention and operations are one lifecycle concern: the system must know when evidence can be deleted and whether the store is healthy enough to enforce the contract. It follows the state vocabulary and the control operations.

## Implementation Intent
Only resolved terminal evidence is eligible for automatic purge; unresolved calls stay until reconciliation or an explicit operator decision. Operators get safe metrics, thresholds, and runbooks for capacity, contention, leases, store continuity, and recovery backlog.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py`, `config/mcp_dedup.toml` (or its replacement, see Dependencies)
- Dedup maintenance and metrics modules, and the MCP health and status services (exact files `Unknown`)
- Deployment monitoring and operator runbooks (`Unknown`)

## Required Changes
- Define purge eligibility per call state; exclude running, unknown, reconciliation-required, interrupted, and unresolved replay-unavailable records; require reconciliation completion for side-effecting terminal calls; support operational and legal holds; keep external references before local result deletion; delete calls, attempts, and results with referential integrity; record purge decisions without sensitive content.
- Monitor database and WAL size, free disk space, busy errors, lock-wait time, acquisition latency, and purge lag, with warning and fail-closed thresholds; verify WAL checkpoint and maintenance under multi-process use.
- Monitor active owners, heartbeat delay, expired leases, unknown outcomes, reconciliation backlog, and replay-unavailable results; expose store identity and fingerprint status; detect an identity mismatch before accepting calls.
- Use stable codes and counts only in normal status output; write runbooks for loss, replacement, contention, migration, capacity exhaustion, and backlog.

## Constraints
- A change to an ADR decision or invariant, including the unbounded-growth acceptance of ADR-008, needs a maintainer approval record in the same change; do not write or simulate that approval.
- Status output must not contain raw arguments, results, paths, or credentials.

## Acceptance Criteria
- [ ] Unresolved safety evidence is never purged by age alone.
- [ ] Resolved terminal evidence follows the configured retention.
- [ ] Store loss and fingerprint mismatch are visible before tool execution.
- [ ] Lease and lock degradation can be detected operationally.
- [ ] Metrics contain no raw payloads or secrets.

## Testing Expectations
- Retention matrix by state; referentially safe purge; hold behavior; WAL and database capacity thresholds; busy and lock contention; heartbeat delay and backlog metrics; redaction of status and diagnostics.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Retention rules per state, thresholds, and runbooks.

## Out of Scope
- The ownership and lease redesign (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); the store identity (issues/20261120-115841_mcpdl002_store-identity-continuity.md).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, issues/20261120-115841_mcpdl002_store-identity-continuity.md, and issues/20261120-115843_mcpdl004_call-state-control-api.md. Blocks issues/20261120-115845_mcpdl006_two-layer-failure-verification.md.
- Related: `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` bounds `retention_days`; issues/20261120-115842_mcpdl003_dedup-config-isolation.md moves the retention setting out of `config/mcp_dedup.toml`.

## Unresolved Questions
- `不明`: threshold values and the legal-hold mechanism.
- `不明`: whether the existing health and status services can expose the new counts.

## AI Implementation Instruction
Write the retention matrix test first. Do not purge an unresolved state. Do not write ADR approval statements. Stop and report the ADR-008 unbounded-growth conflict instead of resolving it.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115844
- **Related target files**: `scripts/shared/mcp_dedup.py`, `config/mcp_dedup.toml`
