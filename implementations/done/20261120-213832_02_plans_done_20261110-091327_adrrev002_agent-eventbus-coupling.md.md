## Goal
- Reference the governance decision from the archived adrrev002 Plan by rewriting the `UNK-02` row's `Resolution Path` cell in `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` to name `AGENT-001`, per the Plan's REQ-002 (make the UNK-02 text reference the recorded decision).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `AGENT-001` exists: it is created by the sibling procedure `implementations/20261120-213832_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md` (earlier `seq` of the same Plan), which runs first; run this procedure only after that one completes.
- In-place editing of this archived Plan is allowed because it is a `Verified` frozen target row of this Plan — the same method the closed adrchk009 cycle used on this file (Plan Assumptions).

## Design decisions
- Only the `Resolution Path` cell changes; the row's question text, `Evidence Missing`, and `Blocking? False` stay, so `tools/check_workitem_structure.py --archived-status` (Status-vocabulary rule) sees no new Status value.
- The new cell is present-tense (Current-Specification-Only policy): it records the live decision reference, not the history of the cell.

## Alternatives considered
- Editing the whole Unknowns row or closing UNK-02: rejected — the keep-versus-retire decision is still pending with the maintainer, so the row must stay open with its question text unchanged (Plan REQ-002).

## Implementation
### Target file
`plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`

### Procedure
1. Locate the `## Unknowns` table row whose ID cell is `UNK-02` (`rg -n "UNK-02"` finds it plus two prose mentions outside the Unknowns table — the `Out-of-Scope` bullet and a Phase 6 preconditions bullet — which MUST NOT be touched).
2. Replace only that row's `Resolution Path` cell with the new cell text in Details; every other cell of the row and every other table row stays byte-identical.

### Method
- Single-cell table edit with the edit tool, anchored on the full `UNK-02` row line so the replacement cannot land on the prose mentions. Do not touch the `Freeze status` line, Execution Status, Blocker Log, or Work Items Created tables.

### Details
Old cell (exact):

```text
Owner decides; if yes, file a follow-up Issue (this Plan leaves both in place and documents them accurately)
```

New cell:

```text
Governance Known Issue AGENT-001 records the pending maintainer keep-versus-retire decision; this Plan leaves both modules in place and documents them accurately
```

In the target file, write the new cell inside the table row with `AGENT-001` backticked as code, and keep the row's other five cells byte-identical.

## Compatibility considerations
- `AGENT-001` resolves once sibling procedure seq 01 has run; running this document before that one leaves a dangling ID reference in an archived Plan (no checker covers `plans/`, but the Plan text would be wrong).

## Security considerations
- N/A: documentation-only edit; no secrets, code, or config touched.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --archived-status` — no finding for this Plan file.
- `rg -n "UNK-02" plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` — the Unknowns row's `Resolution Path` cell names `AGENT-001`; the two prose mentions unchanged.
- `git diff --name-only` — this procedure touches exactly the target file.

## Completion criteria
- The UNK-02 row's `Resolution Path` cell names `AGENT-001`; question text and `Blocking? False` unchanged; the `Out-of-Scope` and Phase 6 prose mentions unchanged; the archived-status checker passes with no finding for this file.

## Out of Scope
- Any other row or section of the adrrev002 Plan; the adrrev005 Plan's own UNK-02 (a different file and question); editing the governance document (covered by the seq 01 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-11-20 | Run after the seq 01 procedure creates `AGENT-001` seq 01 completed and archived; AGENT-001 exists in governance_03 single-cell edit applied to line 169 row only |
| 2 | Run the documentation checkers named in the Validation plan (`routing.md` Tools) | Completed | — | 2026-11-20 | archived-status checker no findings; prose mentions unchanged; full suite (13154 passed, 7 skipped) run earlier in this cycle |

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
- **Requirement ID**: `REQ-002` (reference the recorded decision from the adrrev002 UNK-02 row)
- **Source issue**: issues/20261117-123023_adrchk023_eventbus-client-modules.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-212359_adrchk023_eventbus-client-modules.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-213832
- **Related target files**: `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`