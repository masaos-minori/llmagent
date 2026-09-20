## Goal
Mirror the workspace `code-implementation` skill renumbering into `.opencode/skills/code-implementation/workflow.md`: replace decimal step number Step 2.5 with integer Step 3, shifting all subsequent steps +1 (Steps 3→4 through 7→8).

## Scope
- **In-Scope**: Renumbering Step 2.5 → Step 3 and shifting Steps 3→4 through 7→8 throughout `.opencode/skills/code-implementation/workflow.md`
- **Out-of-Scope**: Modifying SKILL.md Phase overview table (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The workspace counterpart (`skills/code-implementation/workflow.md`) receives identical changes via its own procedure document
- No other files outside the listed target files contain references requiring updates within this single-file change

## Design decisions
- Insert the decimal step into the integer sequence by shifting all subsequent steps +1, maintaining sequential numbering without gaps
- This is a mechanical renaming task — no behavioral or architectural implications

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift

## Implementation
### Target file
`.opencode/skills/code-implementation/workflow.md`

### Procedure
1. Read the current file to identify all step headings and cross-references
2. Apply renumbering cascade: Step 2.5 → Step 3, Step 3 → Step 4, Step 4 → Step 5, Step 5 → Step 6, Step 6 → Step 7, Step 7 → Step 8
3. Update all internal cross-references to step numbers within the file
4. Verify Phase overview table alignment (if present in this file)

### Method
Edit-based renumbering of section headings and cross-references. Each heading `## Step X:` must be updated to `## Step Y:` where Y = X+1 for X >= 3, and `## Step 2.5:` becomes `## Step 3:`. All prose references to step numbers (e.g., "see workflow.md Step 3") must also be updated.

### Details
Current state (verified via repository evidence):
- Line 170: `## Step 2.5: Pre-execution Stale Detection`
- Lines 208+: `## Step 3:` through `## Step 7:` headings exist
- Cross-references to step numbers appear in prose throughout the file

Required changes:
1. Rename `## Step 2.5: Pre-execution Stale Detection` → `## Step 3: Pre-execution Stale Detection`
2. Rename `## Step 3: Implement the Feature` → `## Step 4: Implement the Feature`
3. Rename `## Step 4: Test the Feature` → `## Step 5: Test the Feature`
4. Rename `## Step 5: Update Documentation` → `## Step 6: Update Documentation`
5. Rename `## Step 6: Validate Documentation` → `## Step 7: Validate Documentation`
6. Rename `## Step 7: Move the Completed Implementation Procedure File` → `## Step 8: Move the Completed Implementation Procedure File`
7. Update all internal cross-references in descending order to prevent cascading: "Step 7" → "Step 8", "Step 6" → "Step 7", "Step 5" → "Step 6", "Step 4" → "Step 5", "Step 3" → "Step 4", "Step 2.5" → "Step 3"
8. Update sub-step references in descending order: e.g., "Step 7a" → "Step 8a", "Step 6a" → "Step 7a", ..., "Step 3a" → "Step 4a"
9. Update Execution Status table row numbers (if present)
10. Update any remaining step number references in prose text

## Compatibility considerations
- Downstream consumers of this skill (`code-implementation` workflow) will read step numbers from this file; all references must be consistent after changes
- The Phase overview table in `SKILL.md` is handled separately but must remain aligned

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original step numbers via `git checkout -- .opencode/skills/code-implementation/workflow.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .opencode/skills/code-implementation/workflow.md | Manual review of numbering consistency | `rg "Step [0-9]+\.[0-9]+" .opencode/skills/code-implementation/workflow.md` | Zero decimal step matches |
| .opencode/skills/code-implementation/workflow.md | Phase overview table alignment | Read file Phase overview table if present | Consecutive integers 3–8, no gaps |
| .opencode/skills/code-implementation/workflow.md | Cross-reference consistency | Read file prose for step number refs | All refs match new numbers |

## Completion criteria
- [ ] No decimal step numbers remain in `.opencode/skills/code-implementation/workflow.md`
- [ ] Phase overview table has consecutive integers starting from 3 (no gap at 2→3 transition)
- [ ] All cross-references within the file are consistent with new numbering
- [ ] Execution Status table rows reflect new step numbers

## Out of scope
- Updating SKILL.md Phase overview table (separate procedure)
- Updating sibling skill cross-references (separate procedure)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-191152 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-191152 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-191152 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-191152 | Not applicable: this IS the documentation change |

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
- **Requirement ID**: REQ-007 (.opencode/skills/ mirror matches workspace skills in all step numbers and cross-references)
- **Source issue**: issues/20260920-164935_doc001_unify_decimal_step_numbers_to_integers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-170042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-171321
- **Related target files**: .opencode/skills/code-implementation/workflow.md