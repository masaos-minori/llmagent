## Goal

Verify and lightly correct `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` so
its "Shutdown Termination" implementation note (`:95-97`) matches the current behavior and,
where useful, names the new `TerminationOutcome` reporting (rows 2-3). This doc already
describes the SIGTERM→SIGKILL escalation and per-server isolation accurately.

## Scope

`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` only. Reference: the coordinator
(row 3), the terminator (row 2), the router (row 8). No source change.

## Assumptions

- The doc is architecture/flow documentation for the MCP transport layer; it should stay
  accurate to the runtime shutdown behavior.

## Design decisions

- **Verify, then correct.** Read the Lifecycle Flow (`:65-97`) and confirm:
  - `_ServerLifecycleRouter._shutting_down` guard (`:89`) and the signal-handler swap during
    cleanup (`:93`) are described accurately.
  - The "Shutdown Termination" note (`:95-97`) correctly states: SIGTERM to all servers,
    bounded by one termination timeout (~30s), reaping detects prompt exits, SIGKILL
    escalates servers that ignore SIGTERM, and a termination failure keeps that server's
    tracking entry without affecting others.
- **Optional refinement:** add a clause that the failure is now reported as a specific
  outcome (`SIGNAL_NOT_DELIVERED` errors; `EXIT_UNCONFIRMED` warns) per rows 2-3, without
  over-exposing internal enum names.

## Alternatives considered

- Rewriting the lifecycle flow — rejected: the existing description is accurate; minimal
  correction only.

## Implementation

### Target file

`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure

1. Read `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` around `:65-97`.
2. Confirm the shutdown-termination note (`:95-97`) matches rows 2-3.
3. Add a one-line note on outcome-based reporting if it improves operator clarity.
4. Leave the transport-error tracing section (`:17-24`) untouched.

### Method

Additive correction to the shutdown-termination note. Do not alter unrelated sections.

### Details

- The doc's existing statement that total shutdown time is bounded by one termination
  timeout (`:97`) aligns with REQ-007's graceful-shutdown bound.

## Compatibility considerations

- Doc-only; no source or behavioral impact.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
  restores HEAD. Reversible.

## Validation plan

- Manual read-through of the shutdown-termination note against rows 2-3.
- If the repo has a doc linter/checker per `rules/toolchain.md`, run it.

## Completion criteria

The shutdown-termination note (`:95-97`) matches the current escalation and per-outcome
behavior; no unrelated text changed.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the source tests (rows 12-17), the generated reference table (row 21), and the
  other doc corrections (rows 18, 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/correct shutdown-termination note (`:95-97`) | Pending | — | — | Doc-only |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |

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
- **Requirement ID**: REQ-007 (indirect)
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
