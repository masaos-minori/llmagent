## Goal
Resolve `REQ-001` at its root: amend `docs/00_governance_01_documentation-policy.md` to define the task-level-approval-
decision standard as sufficient acceptance evidence for an ADR's `Status: Accepted`,
so the 10 affected ADRs' Approval Record sections (seq 01-10 of this Plan) have a
defined policy basis instead of contradicting the existing "RACI approval not
obtained from accountable party" Blocking Condition.

## Scope
Modify exactly `docs/00_governance_01_documentation-policy.md`: add a new `### ADR Acceptance Evidence Standard`
subsection under `## ADR Status Definitions`, and add a clarifying parenthetical to
the "RACI approval not obtained from accountable party" bullet under `## Merge
Conditions` > `### Blocking Conditions (Prevent Merge)`.

## Assumptions
- The amendment should be scoped narrowly to this gap only (Plan `Assumptions`), not
  a restructuring of the whole approval process.

## Design decisions
Define two explicitly equally-valid forms of acceptance evidence (named Approval
Record, or task-level approval decision) rather than replacing the named-record
option outright — this preserves ADR-003's existing real Approval Record as still
valid under the amended policy, and avoids narrowing what counts as evidence for
future ADRs that do obtain a named reviewer.

## Alternatives considered
Option (a) (require every ADR to obtain a real named Approval Record) — rejected at
the Plan level; see Plan `Design` section for the full rationale (REQ-003, UNK-02).

## Implementation
### Target file
docs/00_governance_01_documentation-policy.md

### Procedure
Insert a new `### ADR Acceptance Evidence Standard` subsection immediately after the
existing `## ADR Status Definitions` bullet list (before `## ADR Change Protocol`),
and append a parenthetical to the "RACI approval not obtained from accountable
party" bullet under `## Merge Conditions` > `### Blocking Conditions (Prevent
Merge)`.

### Method
1. Locate `## ADR Status Definitions` (the two-bullet `Proposed`/`Accepted`
   definition list).
2. Insert, immediately after that list and before `## ADR Change Protocol`:
   ```
   ### ADR Acceptance Evidence Standard

   An ADR's `## Approval` > `### Approval Record` section satisfies the "RACI approval not
   obtained from accountable party" Blocking Condition (see Merge Conditions) when either of
   the following holds:

   1. **Named Approval Record**: the section records a specific reviewer, approval date, and
      reference (e.g., a review ticket or PR) for that ADR.
   2. **Task-level approval decision**: the accountable party (repository owner) issued an
      explicit instruction, given as part of a specific documented task, to set the ADR's
      Status to `Accepted`. That instruction is itself sufficient acceptance evidence; no
      separate named Approval Record is required.

   Where an ADR relies on a task-level approval decision, its Approval Record section must
   say so explicitly. It must not use `pending` for `Approved By` / `Approval Date` /
   `Approval Reference` (`pending` asserts that acceptance evidence is still outstanding,
   which is false once a task-level decision has been made), and must not fabricate a
   reviewer name, date, or reference that was never given.
   ```
3. Locate `## Merge Conditions` > `### Blocking Conditions (Prevent Merge)`'s
   `- RACI approval not obtained from accountable party` bullet and append:
   ` (for ADRs, see ADR Acceptance Evidence Standard for what counts as approval)`.

### Details
Both edits are additive — no existing sentence is deleted or reworded beyond the one
bullet's trailing parenthetical. This keeps the change narrowly scoped per the
Plan's `Assumptions`.

## Compatibility considerations
Documentation-only change. Downstream effect: the 10 ADRs' Approval Record sections
(seq 01-10) now have a defined policy basis for their wording — those documents
depend on this one being applied in the same cycle.

## Security considerations
N/A: governance-documentation wording change only.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file. Rolling
back this file alone (without also rolling back seq 01-10) would leave the 10 ADRs'
new Approval Record wording referencing a standard that no longer exists in the
policy document — if reverting, revert all 11 files together.

## Validation plan
- `.venv/bin/python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md` → no new issues.
- Manual diff review: confirm only the two additive edits described above were made.

## Completion criteria
`docs/00_governance_01_documentation-policy.md` defines the ADR Acceptance Evidence Standard subsection and the Merge
Conditions bullet cites it.

## Out of scope
The 10 affected ADR files — each covered by its own implementation procedure
document for this same Plan (seq 01-10).

## Documentation
This file is itself the governance policy document being amended; no separate
`docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert `### ADR Acceptance Evidence Standard` subsection | Completed | 2026-09-02 | 2026-09-02 | Placed under `## ADR Status Definitions`, before `## ADR Change Protocol` |
| 2 | Append parenthetical to Merge Conditions blocking-condition bullet | Completed | 2026-09-02 | 2026-09-02 | |
| 3 | Run validation sequence | Completed | 2026-09-02 | 2026-09-02 | `check_docs_quality.py` reported no issues (via `.venv/bin/python` fallback — `uv run` hit a transient `UnknownIssuer` TLS error reaching pypi.org) |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated |

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
- **Requirement ID**: REQ-001 (define task-level-approval-decision acceptance-evidence standard)
- **Source issue**: `issues/20260831-191101_govdocs003_missing_approval_record_across_adrs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-223351_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-133930
- **Related target files**: `docs/00_governance_01_documentation-policy.md`
