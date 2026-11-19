# Unify MCP process ownership, lifecycle state, shutdown, and restart safety

## Priority
High

## Summary
Introduce one managed-process ownership contract across startup failure, normal shutdown, process-group failure, restart, and shutdown suppression; keep records until exit is confirmed and enforce lifecycle transitions.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 6). Related archived work: `issues/done/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md`, `issues/done/20261016-092822_mcp001_double_startup_failure_crashes_mcp_loop.md` (re-verify against them).

Evidence: all files named under Target Files exist (`Explicit in code`, by listing). The path-dependent ownership claims (startup failure keeping an unconfirmed process, normal shutdown removing the entry, PGID failure releasing tracking, restart over a possibly live process, router marking every server `STOPPED`, invalid transitions mutating state, silent return from `ensure_ready()` and `restart()` during shutdown) are from the backlog and `Needs confirmation`.

## Problem
Process ownership and lifecycle state depend on the code path, so an unconfirmed process may be released, a replacement may start while the old process may be alive (port conflict, duplicate server), and callers may assume success from a silent return during shutdown.

## Reason for Change
Process-lifecycle correctness: a second live server for the same key, or a lost process, is hard to detect and recover.

## Implementation Intent
A `ManagedProcessRecord` owns process, pid, pgid, stderr, and lifecycle state. Only confirmed exit releases ownership; restart requires confirmed exit; invalid transitions fail without mutating state; shutdown-time start, ensure, and restart calls return typed suppression errors.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py`, `http_lifecycle_shutdown_coordinator.py`, `http_lifecycle_process_terminator.py`
- `scripts/agent/lifecycle.py`, `lifecycle_router.py`, `lifecycle_protocol.py`
- Lifecycle tests under `tests/agent/`

## Required Changes
- Introduce `ManagedProcessRecord`; delete records only for confirmed exit; keep ownership for `EXIT_UNCONFIRMED` and `SIGNAL_NOT_DELIVERED`; remove pre-termination process-entry deletion; keep records after PGID failure unless exit is confirmed.
- Add states `STOPPING`, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED`; update state per server outcome and never set `STOPPED` globally without confirmation; reject invalid transitions without mutation.
- Require confirmed old-process exit before restart; return typed non-retryable suppression errors during shutdown; show unconfirmed processes in `/mcp status`; support repeated shutdown and explicit manual cleanup.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate that approval.
- Builds on the global deadline of `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md` and the safe launch of `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`.

## Acceptance Criteria
- [ ] Every unconfirmed process remains owned and visible.
- [ ] Restart cannot create a second live process for the same server.
- [ ] Invalid transitions do not mutate state.
- [ ] Shutdown-time lifecycle calls never return silent success; startup, shutdown, restart, and PGID failure follow one contract.

## Testing Expectations
- Exit-unconfirmed behavior on every lifecycle path; restart refusal and port-conflict prevention; repeated shutdown and manual cleanup; invalid transition and shutdown-suppression tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. The lifecycle state machine, ownership rules, and result codes.

## Out of Scope
- Launch-spec and credential work (`issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`); health semantics (`issues/20261119-145306_cliplc008_mcp-health-capability.md`).

## Dependencies
- Depends on `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md` and `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`. Blocks `issues/20261119-145306_cliplc008_mcp-health-capability.md` and `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`.

## Unresolved Questions
- `不明`: which of the reported ownership defects still exist after the archived star001 and mcp001 work.
- `不明`: the manual cleanup interface (command name and semantics).

## AI Implementation Instruction
Re-verify each reported ownership defect with a test first. Keep the change in the lifecycle modules. Do not weaken confirmed-exit semantics for convenience. Stop and report any path where exit cannot be confirmed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145305
- **Related target files**: `scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/http_lifecycle_process_terminator.py`, `scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle_protocol.py`
