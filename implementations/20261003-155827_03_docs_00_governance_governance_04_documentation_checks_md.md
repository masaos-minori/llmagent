# Implementation Procedure: Exit-Behavior Documentation in governance_04_documentation-checks.md

## Goal

Document the exit-status decision for the Needs Confirmation Inventory Check in the documentation-checks reference: WARNING findings (including untracked markers) do not cause a non-zero exit and only ERROR findings fail.

## Scope

Add one sentence under check #3 (Needs Confirmation Inventory Check) in `docs/00_governance/governance_04_documentation-checks.md` stating WARNING findings (including untracked markers) do not cause a non-zero exit and only ERROR findings fail. Canonical governance reference is currently silent on exit behavior. GV-009 row (`:305`) lists severity Warning; the check description (`:90-99`) has no exit-behavior text.

## Assumptions

- The owner decision is recorded: warnings → exit 0 (detection mode), only ERROR findings cause failure.
- The check #3 description section currently lacks any mention of exit behavior.
- No additional files require modification beyond this single documentation file.

## Design decisions

- The sentence should be concise and placed within the check #3 description paragraph, after the existing bullet list.
- The wording should mirror the language used in the source plan's Design section ("warnings → exit 0") while being self-contained enough for readers who only consult this document.

## Alternatives considered

- Adding the exit-behavior note to the GV-009 Governance Verification Matrix row instead of the check description: the matrix row is more structured but less visible to consumers reading the check descriptions. Placing it in the check description ensures visibility during routine review.
- Adding the note to both locations: redundant but provides cross-referencing. However, the check description is the primary consumer-facing location; the matrix row can reference it.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the check #3 description section (lines 90–99 of the file).
2. After the existing bullet list, add one sentence documenting the exit-behavior decision.
3. Do not modify any other section of the document.

### Method

Edit the check #3 description using targeted insertion after the existing content. Preserve all existing text; append only the new sentence.

### Details

**Before edit — check #3 description (current state):**

```markdown
### 3. Needs Confirmation Inventory Check (`check_needs_confirmation_inventory.py`)

Verifies the NC inventory stays in sync with `docs/*.md`.

**Checks:**
- "Needs confirmation" mentions in docs are registered in the centralized inventory (`governance_03_issue-and-uncertainty-management.md`)
- Resolved NC items do not leave markers in source documents
- Field count declarations match actual list item counts
```

**After edit — check #3 description (proposed state):**

```markdown
### 3. Needs Confirmation Inventory Check (`check_needs_confirmation_inventory.py`)

Verifies the NC inventory stays in sync with `docs/*.md`.

**Checks:**
- "Needs confirmation" mentions in docs are registered in the centralized inventory (`governance_03_issue-and-uncertainty-management.md`)
- Resolved NC items do not leave markers in source documents
- Field count declarations match actual list item counts

**Exit behavior:** WARNING findings (including untracked inline markers) do not cause a non-zero exit; only ERROR findings produce a non-zero exit.
```

## Compatibility considerations

- This is a documentation-only change. No behavioral change to the checker.
- The GV-009 Governance Verification Matrix row already lists severity Warning; this addition makes the exit behavior explicit rather than implicit.

## Security considerations

- No security impact: this is a documentation recording of an existing owner decision.

## Rollback considerations

- Revert the added sentence via git checkout if the classification is disputed.
- The rollback restores the original check description without the exit-behavior note.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Manual: verify the exit-behavior sentence is present and accurate | Read check #3 description | Exit behavior documented |

## Completion criteria

- The check #3 description contains a clear statement of the exit-behavior contract (WARNING → exit 0; ERROR → non-zero).
- The sentence is self-contained and does not require cross-referencing another document.
- No new `[ERROR]`/`[WARNING]` findings introduced by running relevant validation tools.

## Out of scope

- Changing the checker's warning messages or severity levels.
- Resolving the actual orphaned markers themselves.
- Changing inventory entry format.
- Altering `report_and_exit()` logic or any other checker function.
- Modifying CI configuration files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add exit-behavior sentence to check #3 description | Pending | — | — | REQ-002 |
| 2 | Verify no new validation findings introduced | Pending | — | — | AC-001 |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261002-155701_ncinv002_exit_status_for_untracked_markers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-144238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-155827
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
