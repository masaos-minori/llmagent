# Implementation Procedure: ADR-003 advisory availability-hint boundary

## Goal

Record the advisory dynamic-availability hint contract and its non-authority boundary in
ADR-003 (REQ-008; plan AC-1). Decisions 11/12 stay byte-identical.

## Scope

**In scope:**
- `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`: one new
  Decision Details entry (next free number 17; entries 1-16 verified present at HEAD
  `124e340b4`).

**Out of scope:**
- Decisions 11 ("Static availability ... and Dynamic Health ... are separate
  subsystems", `:81`) and 12 ("Dynamic Health state must not automatically change LLM
  visibility", `:82`) — quoted as anchors, never edited (plan target row: "decisions
  11/12 unchanged").
- The ADR-016 authority matrix (`docs/10_adr/adr_01_index.md` is not a target row here):
  the plan Dependency records the matrix already assigns routing/visibility/health
  authority to ADR-003; no matrix change is expected.

## Assumptions
- The hint contract recorded normatively is the one in this plan's Design section:
  normalized reason codes (`server_unavailable`, `half_open_trial_in_progress` (new)), circuit
  state, optional `retry_after_seconds` (new), carried on structured tool results only.
- Docs policy (`skills/DESIGN.md`): intent and boundaries only — the ADR wording must not
  name implementation locations (no file paths, no class names beyond the ADR's existing
  vocabulary).

## Design decisions
- New Decision 17 (append-only after 16, `:86`), wording to the effect of: "Dynamic
  Health may surface an advisory availability hint on the structured tool result
  (normalized reason code, circuit state, optional retry timing). The hint is advisory
  only: it does not gate, reroute, or retry Routing or execution, does not alter
  `RuntimeTool` static fields, and does not change LLM visibility (Decision Details #11,
  #12). A bounded turn-loop guard response to repeated unavailability is an advisory turn
  termination, not a routing decision."
- No Status/Approval changes: this is elaboration consistent with existing decisions, not
  a supersession (ADR-016 matrix already records ADR-003 as primary for
  routing/visibility/health).

## Alternatives considered
- Amending Decision 11/12 bodies with hint sentences: rejected — the plan fixes "decisions
  11/12 unchanged", and inline edits to normative decisions risk conflicts with concurrent
  ADR work (plan Risks: `dbmig001`/`adrauth001` doc phases).
- Recording only in Consequences (non-normative): rejected — the contract is a binding
  boundary for the code rows; Decision Details is the normative home.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Re-read the Decision Details block against current HEAD immediately before editing
  (ADR-set churn risk).
2. Append Decision 17 with the wording shape above, cross-referencing #11/#12.
3. Add one Invariants line only if an existing invariant enumerates "what Dynamic Health
  may not do" — otherwise none (append-only preference).

### Method
- Single append to the Decision Details list; no renumbering.

### Details
- Keep the Japanese document's keyword conventions (Static Availability, Dynamic Health,
  Routing as used in the existing text).

## Compatibility considerations
- `adr_01_index.md` ADR List row for ADR-003 needs no change (status/title unchanged).
- If `adrauth001`'s ADR-016 matrix lands first (expected: it lands its index edits
  earlier), verify Decision 17 wording does not contradict the matrix; on conflict, stop
  and re-scope per the plan Dependency note rather than editing the matrix.

## Security considerations
- Wording must state the closed reason-code nature of the hint (matches rows 01-03
  design).

## Rollback considerations
- Delete the appended Decision 17 line(s); nothing else references it in this phase.

## Validation plan
- ADR/docs checkers named in `routing.md` (ADR structure + index consistency) green.
- `tools/stale_detector.py` green for this procedure doc.

## Completion criteria
- Decision 17 present, decisions 11/12 byte-identical, checkers green.

## Out of Scope
- Other ADR bodies, `adr_01_index.md`, agent/MCP spec docs (rows 13-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append Decision 17 (advisory hint boundary) against current HEAD | Pending | — | — | |
| 2 | Verify decisions 11/12 unchanged and ADR-016 matrix consistency | Pending | — | — | |
| 3 | Run docs/ADR checkers from `routing.md` | Pending | — | — | |

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
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
