## Goal
Add the 8 required routing rules to `docs/00_governance_01_documentation-policy.md`,
adjacent to M-01-02's resolution sequence, per REQ-001. Extend the Merge Conditions
section with explicit Canonical Source Conflict severity/blocking behavior per REQ-004.

## Scope
- **In-Scope**: adding the 8 routing rules after M-01-02's six-step resolution sequence;
  extending Merge Conditions with explicit severity/blocking mapping for Canonical Source
  Conflicts.
- **Out-of-Scope**: every other change to this file; adding/removing any other section.

## Assumptions
- M-01-01 through M-01-06 are all implemented before this procedure executes (Phase 0
  prerequisite check).
- The existing "## Merge Conditions" section (lines 263-283) already lists "Canonical
  source conflict unresolved" as Blocking and "Config drift detected but no behavioral
  impact" as Non-Blocking, but does not yet state severity/blocking mapping explicitly
  for the new categories.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Place the 8 routing rules immediately after M-01-02's resolution sequence under a
  new subsection ("## Routing Rules") within the same "## Canonical Source Precedence"
  section — routing is the natural next step after the resolution sequence's final step
  ("record unresolved differences through the designated conflict workflow").
- Extend the existing Merge Conditions section rather than creating a separate section —
  the severity/blocking mapping belongs alongside the existing Blocking/Non-Blocking
  conditions.

## Alternatives considered
N/A: straightforward addition of routing rules; no alternative approach applies.

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. After M-01-02's six-step resolution sequence, add a new subsection "### Routing Rules"
   containing the 8 required routing rules:
   - design-vs-code → Known Issue
   - functional-requirement-vs-implementation → Known Issue
   - Specification-vs-acceptance-test → blocking conflict
   - deployed-vs-approved config → Configuration Drift
   - undetermined intent → Needs Confirmation
   - missing canonical source → design/governance gap
   - multiple normative sources → blocking Canonical Source Conflict
   - stale non-canonical wording only → documentation-correction task
2. Extend the existing "## Merge Conditions" section:
   - Under "### Blocking Conditions", add: "Canonical Source Conflict severity is
     `High` when the conflicting source is a normative source; `Medium` when the
     conflicting source is a non-normative reference."
   - Under "### Non-Blocking Conditions", add: "Configuration Drift has no behavioral
     impact (already listed)."

### Method
Edit via exact string replacement using Edit tool.

### Details
- The 8 routing rules are added as a numbered list under "### Routing Rules".
- The Merge Conditions extension adds explicit severity/blocking text to both the
  Blocking Conditions and Non-Blocking Conditions subsections.
- Phase 0 prerequisite check: confirm M-01-01 through M-01-06 are all implemented
  before proceeding.

## Compatibility considerations
N/A: governance-class document; no runtime/code caller.

## Security considerations
N/A.

## Rollback considerations
- Revert the edits to restore the original routing rules and Merge Conditions sections.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md` passes.
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm exactly 8 routing rules are present and each maps to exactly one destination.

## Completion criteria
- Every one of the 8 required routing rules has exactly one documented destination (AC1).
- Design-versus-code differences route to Known Issues (AC2).
- Production-value differences route to Configuration Drift (AC3).
- Unknown intent routes to Needs Confirmation, duplicate normative sources route to
  blocking Canonical Source Conflict, stated explicitly (AC4).
- Missing canonical ownership routes to a design or governance gap (AC5).
- Documentation structural/quality validation passes (AC8).

## Out of scope
- Every other change to this file.
- Adding/removing any other section.
- Updating `docs/00_governance_03_issue-and-uncertainty-management.md` (REQ-002, REQ-003, separate procedure).
- Extending `tools/check_canonical_source_conflicts.py` (REQ-008, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Already implemented |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Skipped | — | — | No new code to validate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A |

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
- **Requirement ID**: `REQ-001` (document the 8 required routing rules), `REQ-004` (extend Merge Conditions with explicit Canonical Source Conflict severity/blocking behavior)
- **Source issue**: issues/20260903-103030_m0107_integrate-canonical-source-conflicts-with-issue-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185612_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185612
- **Related target files**: docs/00_governance_01_documentation-policy.md
