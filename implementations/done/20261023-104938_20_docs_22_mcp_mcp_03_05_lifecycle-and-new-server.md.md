## Goal

Verify and lightly correct `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` so its
lifecycle descriptions stay consistent with the outcome-based shutdown (rows 2-3) and the
new-server registration flow. This doc covers the manager's read-only snapshots, the
router facade, and the new-server checklist.

## Scope

`docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` only. Reference: the manager (row 4),
the router (row 8), the launcher (row 5). No source change.

## Assumptions

- The doc is operational/architectural guidance for adding new MCP servers; shutdown
  behavior is secondary to the registration flow but must not be inaccurate.

## Design decisions

- **Verify, then correct.** Read the whole doc (`:1-76`) and confirm:
  - The manager's read-only snapshot description (`:18`) and the router facade delegation
    (`:23`) remain accurate.
  - Any mention of shutdown/termination is consistent with the graceful-then-SIGKILL
    escalation and per-outcome handling (rows 2-3). If the doc does not cover shutdown,
    leave it; do not introduce an unverified section.
  - The new-server checklist (`:46-56`) is unchanged unless it references shutdown behavior.

## Alternatives considered

- Adding a full shutdown subsection — rejected: verify-only; introduce only if the doc
  already touches shutdown and is inaccurate.

## Implementation

### Target file

`docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`

### Procedure

1. Read `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` fully (`:1-76`).
2. Confirm the lifecycle/facade descriptions (`:18`, `:23`) are accurate.
3. Correct any shutdown/termination statement that conflicts with rows 2-3; otherwise make
   no change.
4. Leave the new-server checklist (`:46-56`) intact unless it references shutdown.

### Method

Additive correction only if a conflict exists; otherwise no edit.

### Details

- This doc's primary purpose is new-server registration; the Plan's termination changes
  touch it only if a statement is inaccurate.

## Compatibility considerations

### Corrections found while implementing

- Process Introspection: states that snapshots exist only while a process entry exists, so the surviving record after an unconfirmed attempt is the reported failure.


- Doc-only; no source or behavioral impact.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`
  restores HEAD. Reversible.

## Validation plan

- Manual read-through against rows 2-3 and the router (row 8).
- If the repo has a doc linter/checker per `rules/toolchain.md`, run it.

## Completion criteria

The lifecycle descriptions are accurate and any shutdown statement matches rows 2-3; no
unverified content introduced and the new-server checklist is intact.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the source tests (rows 12-17), the generated reference table (row 21), and the
  other doc corrections (rows 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/correct lifecycle descriptions | Completed | 20261023-152957 | 20261023-152957 | Doc-only implemented; full suite passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-152957 | 20261023-152957 | AC-9 |

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
- **Related target files**: `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`