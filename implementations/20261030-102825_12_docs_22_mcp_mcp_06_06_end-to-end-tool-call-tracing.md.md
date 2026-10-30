# Implementation Procedure: docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md

## Goal

Document the execution snapshot and dedup state as new fields of the tool-call audit
trace (REQ-004 snapshot in the trace; plan AC-4).

## Scope

**In scope:**
- `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`: trace-record field list and
  the dedup-outcome narrative.

**Out of scope:**
- Audit code (rows 04-05); reference table regeneration (row 14 domain).

## Assumptions

- Land after rows 04-05 so documented field names (`execution_snapshot_json` (new),
  `dedup_state` (new), `snapshot_mismatch` (new) / `dedup_unreplayable` (new) outcome tags) match shipped
  output.

## Design decisions

- Extend the existing trace-anatomy section with the two new record fields and their
  sources (dispatcher `DispatchResult` / agent audit payload), plus one example line
  showing a replayed completed-hit.
- Explain per-component snapshot equality in one paragraph; link `docs/41_db/db_03_07`
  (row 14) for storage details.

## Alternatives considered

- N/A: doc-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`

### Procedure
1. Add the two fields to the trace record description where audit fields are enumerated.
2. Add the replay/snapshot-mismatch outcome vocabulary to the outcomes section.

### Method
Prose edits preserving the file's existing walkthrough structure.

### Details
- Example log line uses synthetic keys (no real deployed values).

## Compatibility considerations

- N/A: docs-only.

## Security considerations

- Example record must not depict secrets or real user data.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Docs checkers per `routing.md` Tools; stale detector after rows 04-05 land.

## Completion criteria

- Every new audit field emitted by rows 04-05 is documented with name, source, and
  semantics; no claim outruns shipped code.

## Out of Scope

- Config/retention docs (row 11/14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update trace field + outcome sections | Pending | — | — | After rows 04-05 |
| 2 | Run the docs validation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (snapshot + dedup states visible in the trace)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md
