## Goal
Update the Governance Verification Matrix in `docs/00_governance_04_documentation-checks.md`
to register the new routing logic once confirmed working per REQ-010, following the same
"implemented only after confirmed working" convention M-01-05 established.

## Scope
- **In-Scope**: adding/updating a Governance Verification Matrix row for the routing
  logic (destination classification and duplicate-active-record detection).
- **Out-of-Scope**: every other change to this file; modifying existing rows.

## Assumptions
- Phase 3 (REQ-008, REQ-009) is confirmed working before this procedure executes —
  the routing logic must be verified before registering it in the matrix.
- The existing matrix format uses columns: Rule ID, Rule, Doc, Method, Tool/Review,
  Timing, Gate, Status, Follow-up.
- The existing convention is "implemented only after confirmed working" — the Status
  column should reflect actual implementation status, not planned.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Add a new Rule ID (e.g., GV-022) rather than reusing an existing one — the routing
  logic is a distinct governance check.
- Set Status to "Existing" only after Phase 3 verification confirms the routing logic
  works; set to "Missing" if executed before Phase 3 completes.

## Alternatives considered
N/A: straightforward addition of a matrix row; no alternative approach applies.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Add a new row to the Governance Verification Matrix table with:
   - Rule ID: `GV-022` (next available ID after GV-021)
   - Rule: "Canonical source conflict routing and deduplication"
   - Doc: `Pol` (governance-class document)
   - Method: `Auto`
   - Tool/Review: `check_canonical_source_conflicts.py`
   - Timing: `PR`
   - Gate: `Blocking`
   - Status: `Existing` (if Phase 3 confirmed working) / `Missing` (if not yet verified)
   - Follow-up: `None` (if existing) / `Implement` (if missing)

### Method
Edit via exact string insertion using Edit tool, inserting a new row into the matrix table.

### Details
- The new row follows the exact same column structure as existing rows.
- If Phase 3 has not been verified, Status should be `Missing` and Follow-up should be
  `Implement`.
- Phase 0 prerequisite check: confirm M-01-01 through M-01-06 are all implemented
  before proceeding.

## Compatibility considerations
N/A: governance-class document; no runtime/code caller.

## Security considerations
N/A.

## Rollback considerations
- Remove the new row to revert.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md` passes.
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm exactly one new row was added with correct Rule ID (GV-022).

## Completion criteria
- Governance Verification Matrix registers the new routing logic (AC12).
- Documentation structural/quality validation passes (AC12).

## Out of scope
- Every other change to this file.
- Modifying existing rows.
- Updating `docs/00_governance_01_documentation-policy.md` (REQ-001, REQ-004, separate procedure).
- Adding Part 3/Part 4 sections (REQ-002, REQ-003, separate procedure).
- Extending `tools/check_canonical_source_conflicts.py` (REQ-008, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Prerequisite REQ-008 not confirmed working |
| 2 | Add or update tests per Validation plan | Skipped | — | — | Blocked on Step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Skipped | — | — | Blocked on Step 1 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Prerequisite REQ-008 target file `tools/check_canonical_source_conflicts.py` does not exist | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010` (update Governance Verification Matrix once routing logic is confirmed working)
- **Source issue**: issues/20260903-103030_m0107_integrate-canonical-source-conflicts-with-issue-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185612_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185612
- **Related target files**: docs/00_governance_04_documentation-checks.md
