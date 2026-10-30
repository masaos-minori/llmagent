# Implementation Procedure: mcp_06_10 reason codes and static-vs-dynamic display

## Goal

Document the closed availability-hint reason codes and the static-vs-dynamic health
display in the MCP health-reasons doc (REQ-008; plan AC-4).

## Scope

**In scope:**
- `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`: one subsection under
  "Health Reasons Priority" (verified present at HEAD `124e340b4`, `:16`) and one short
  display subsection.

**Out of scope:**
- `docs/22_mcp/mcp_03_03_transport-and-health.md` (reference only, per the plan Reference
  Files row); the tool-vs-transport error table at `:47` is not edited.

## Assumptions
- The doc already separates `/health`-body derived display reasons (`health_reason`
  priority table) from registry state changes, and states "Degraded Reasons Are Not
  Stored" — the new reason codes must be described as circuit-state-derived codes, not as
  another `health_reason` priority row, keeping that section's semantics intact.
- Docs policy: behavior and boundaries only, no implementation locations.

## Design decisions
- New subsection "Availability Hint Reason Codes" after the priority section:
  - A closed set of two codes — `server_unavailable`, `half_open_trial_in_progress` (new) —
    derived from the circuit state at rejection time (not from the `/health` body, not a
    stored per-server field: consistent with "Degraded Reasons Are Not Stored").
  - Carried on structured tool results as an advisory signal; `retry_after_seconds` (new) is a
    computed cooldown remainder (present only for the unavailable case), never stored.
  - Explicit boundary: the codes do not gate, reroute, or retry calls and do not change
    LLM tool visibility (matches ADR-003 Decision 17 wording from row 12).
- New subsection "Static availability vs dynamic health in diagnostics": operator status
  output shows static visibility (configuration-derived, `startup_mode=none` means
  excluded) and dynamic health (circuit state + optional reason/retry timing) as separate
  labeled values.

## Alternatives considered
- Extending the `health_reason` priority table with the two codes: rejected — that table
  is `/health`-body display semantics; conflating circuit codes into it would contradict
  the existing "Degraded Reasons Are Not Stored" subsection.

## Implementation
### Target file
`docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`

### Procedure
1. Insert "Availability Hint Reason Codes" after the priority/degraded-reasons block.
2. Insert the static-vs-dynamic display subsection before "Difference Between Tool Errors
  and Transport Errors".
3. Append new terms to Keywords following the file's existing keyword convention.

### Method
- Two append-only subsections; existing tables byte-identical.

### Details
- Use the exact code strings `server_unavailable` / `half_open_trial_in_progress` (new) — the
  doc is the naming authority operators and consumers cross-check against.

## Compatibility considerations
- Wording must match row 12's ADR-003 Decision 17 and row 06's display labels; edit this
  doc after rows 12/06 land (same Phase 4) so terminology is already fixed.

## Security considerations
- State that reason codes are a closed set and never carry server-supplied text.

## Rollback considerations
- Remove the two subsections and keyword entries.

## Validation plan
- Docs checkers from `routing.md` green; `tools/stale_detector.py` green for this doc.

## Completion criteria
- Both subsections present with the closed-code and boundary wording; existing priority
  table and error-kind table unchanged; checkers green.

## Out of Scope
- ADR-003 (row 12), agent doc (row 13), any code row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert availability-hint reason-codes subsection | Completed | — | 20261030-204921 | 'Availability Hint Reason Codes' section inserted after degraded-reasons block with closed-code table and boundary wording |
| 2 | Insert static-vs-dynamic display subsection and Keywords entries | Completed | — | 20261030-204921 | 'Static Availability vs Dynamic Health in Diagnostics' inserted before tool-vs-transport section; display labels match cmd_mcp.py; 5 Keywords appended |
| 3 | Run docs checkers from `routing.md` | Completed | — | 20261030-204921 | check_docs_quality + check_docs_structure + stale_detector green; error-kind and priority tables unchanged |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`