## Goal

Correct `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` so
its shutdown/rollback section reflects the new outcome-based termination (rows 2-3) and the
`TerminationOutcome` vocabulary (row 1). The doc currently describes rollback via
`shutdown_all()` and re-raise (line `:37`, `:145`); it should note that termination now
reports a specific outcome.

## Scope

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` only.
Reference: the startup orchestrator (row 10), the coordinator (row 3), the terminator
(row 2). No source change.

## Assumptions

- The doc is user/operator-facing operational documentation; it should stay accurate to the
  runtime behavior without exposing internal enum names unless useful.

## Design decisions

- **Verify, then correct.** Read the shutdown section (`:74-95`, `:144-145`) and confirm it
  is consistent with:
  - Rollback calls `lifecycle.shutdown_all()` on startup failure and re-raises the original
    exception (`:37`, `:145`) — unchanged by this Plan.
  - The new behavior: a server that ignores SIGTERM is escalated to SIGKILL, and a
    termination failure is reported as a specific outcome (`SIGNAL_NOT_DELIVERED` errors,
    `EXIT_UNCONFIRMED` warns) rather than a coarse success/fail.
- **Add a short note** under "Resource Cleanup on Shutdown" (`:74`) describing the
  graceful-then-kill escalation and per-outcome handling (REQ-004, REQ-005). Do not rewrite
  the whole doc.

## Alternatives considered

- Rewriting the operational doc — rejected: minimal, targeted correction only.

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Read `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
   around `:74-95`, `:144-145`.
2. Confirm the rollback/re-raise description (`:37`, `:145`) is still accurate.
3. Add a concise note on the graceful-then-SIGKILL escalation and outcome-based reporting
   under "Resource Cleanup on Shutdown".
4. Keep the existing ADR-008 / WAL-timeout notes (`:95`, `:144`) intact.

### Method

Additive correction to the shutdown section. Do not alter unrelated sections.

### Details

- The doc's existing statement that a rollback failure is only logged (`:145`) remains
  true; this Plan adds outcome granularity to the termination itself, not the rollback.

## Compatibility considerations

### Corrections found while implementing

- Resource Cleanup step 4 now states what `shutdown_all()` reports and that clean means every started server was confirmed gone; Known-Limitations item 2 corrected (console line carries cause and unconfirmed keys). The WAL item was not touched.


- Doc-only; no source or behavioral impact.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
  restores HEAD. Reversible.

## Validation plan

- Manual read-through of the corrected section against rows 2-3.
- If the repo has a doc linter/checker per `rules/toolchain.md`, run it.

## Completion criteria

The shutdown section states the graceful-then-SIGKILL escalation and per-outcome handling,
and remains consistent with the rollback/re-raise description; no unrelated text changed.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the source tests (rows 12-17), the generated reference table (row 21), and the
  other doc corrections (rows 19-20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct shutdown/rollback section (add outcome-based note) | Completed | 20261023-152955 | 20261023-152955 | Doc-only implemented; full suite passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-152955 | 20261023-152955 | AC-9 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-005 (indirect)
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`