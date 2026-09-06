## Goal
Extend `tools/check_canonical_source_conflicts.py` (M-01-05) with destination classification
(5 categories) and duplicate-active-record detection per REQ-008.

## Scope
- **In-Scope**: adding destination classification logic that routes each finding into
  exactly one of the 5 destinations (Known Issue / Configuration Drift / Needs Confirmation
  / Canonical Source Conflict / documentation-correction task); adding duplicate-active-record
  detection that refuses to recommend a second independent entry for a discrepancy already
  tracked in another inventory.
- **Out-of-Scope**: adding test cases (REQ-009, separate procedure); updating the
  Governance Verification Matrix (REQ-010, separate procedure).

## Assumptions
- M-01-05's existing validator interface is known from `plans/20260905-165817_plan.md`;
  this Plan extends it rather than replacing it.
- Each finding the existing checks produce gains the 12 required record fields where the
  destination is Canonical Source Conflict; a lighter field set for the other 4 destinations,
  matching each one's own existing/newly-added template.
- The `Related` field in each entry cross-references any existing Known Issue/Needs
  Confirmation/Configuration Drift/Canonical Source Conflict entry for the same underlying
  discrepancy by decision-target-and-claim-type.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Extend the existing validator rather than creating a new one — the routing/dedup logic
  belongs alongside the existing semantic checks.
- Use a deterministic routing function that takes a finding and returns exactly one
  destination category, preventing silent suppression or duplication.

## Alternatives considered
N/A: straightforward extension of the existing validator; no alternative approach applies.

## Implementation
### Target file
`tools/check_canonical_source_conflicts.py`

### Procedure
1. Add a routing function that classifies each finding into exactly one of the 5
   destinations per the 8 routing rules from REQ-001:
   - design-vs-code → Known Issue
   - functional-requirement-vs-implementation → Known Issue
   - Specification-vs-acceptance-test → blocking conflict
   - deployed-vs-approved config → Configuration Drift
   - undetermined intent → Needs Confirmation
   - missing canonical source → design/governance gap
   - multiple normative sources → blocking Canonical Source Conflict
   - stale non-canonical wording only → documentation-correction task
2. Add duplicate-active-record detection: before creating a new entry recommendation,
   check if the same discrepancy is already active in more than one inventory by
   comparing decision-target-and-claim-type against existing entries.
3. For findings classified as Canonical Source Conflict, output the 12 required record
   fields (Conflict ID, Decision target, Claim type, Canonical source, Conflicting source
   or evidence, Conflict category, Impact, Severity, Blocking status, Required action,
   Owner, Validation evidence).
4. For findings classified as other destinations, output the lighter field set matching
   each one's own template.

### Method
Edit via exact string insertion using Edit tool, adding the routing function and extending
the existing check outputs.

### Details
- The routing function must be deterministic: given the same finding, always return the
  same destination category.
- Duplicate detection compares decision-target-and-claim-type pairs across inventories.
- Phase 0 prerequisite check: confirm M-01-01 through M-01-06 are all implemented
  before proceeding.

## Compatibility considerations
N/A: governance CI tool (M-01-05); no runtime/code caller.

## Security considerations
N/A.

## Rollback considerations
- Revert the edits to restore the original validator without routing/dedup logic.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` passes —
  all 8 routing-outcome cases pass alongside M-01-05's existing cases (AC11).
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm the routing function handles all 8 routing rules deterministically.
- Confirm duplicate detection catches the same discrepancy in multiple inventories.

## Completion criteria
- Each finding is classified into exactly one of the 5 destinations (AC2, AC3).
- Duplicate active records are prohibited or detected (AC6).
- All 8 routing-outcome test cases pass (AC11).
- Documentation structural/quality validation passes (AC12).

## Out of scope
- Adding test cases (REQ-009, separate procedure).
- Updating the Governance Verification Matrix (REQ-010, separate procedure).
- Every other change to this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Target file does not exist |
| 2 | Add or update tests per Validation plan | Skipped | — | — | Blocked on Step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Skipped | — | — | Blocked on Step 1 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Target file `tools/check_canonical_source_conflicts.py` does not exist in repository | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (extend validator with destination classification and duplicate-active-record detection)
- **Source issue**: issues/20260903-103030_m0107_integrate-canonical-source-conflicts-with-issue-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185612_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185612
- **Related target files**: tools/check_canonical_source_conflicts.py
