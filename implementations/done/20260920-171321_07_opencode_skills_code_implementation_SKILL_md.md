## Goal
Mirror the workspace `code-implementation` skill renumbering into `.opencode/skills/code-implementation/SKILL.md`: replace Phase overview table row `2.5 | Pre-execution stale detection` with `3 | Pre-execution stale detection`, shift all subsequent rows +1, and update cross-reference `workflow.md` Step 2.5 → `workflow.md` Step 3.

## Scope
- **In-Scope**: Phase overview table row update, cross-reference update in `.opencode/skills/code-implementation/SKILL.md`
- **Out-of-Scope**: Modifying workflow.md section headings (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The workspace counterpart (`skills/code-implementation/SKILL.md`) receives identical changes via its own procedure document
- workflow.md section headings are already updated (or will be updated concurrently) before this change is validated

## Design decisions
- Phase overview table must stay synchronized with workflow.md section headings
- Cross-references within the skill must point to the correct step number after renumbering

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift

## Implementation
### Target file
`.opencode/skills/code-implementation/SKILL.md`

### Procedure
1. Read the current file to identify Phase overview table and cross-references
2. Update Phase overview table: replace row `2.5 | Pre-execution stale detection` with `3 | Pre-execution stale detection`; shift all subsequent rows +1
3. Update cross-reference: `workflow.md` Step 2.5 → `workflow.md` Step 3
4. Verify alignment with workflow.md section headings

### Method
Edit-based update of Phase overview table row and cross-reference. The Phase overview table uses Markdown table format — each row must maintain proper column alignment.

### Details
Current state (verified via repository evidence):
- Line 31: `| 2.5 | Pre-execution stale detection | Verify the procedure's referenced code constructs still exist in current source; abort if stale. |`
- Lines 32-36: Phase overview table rows for Steps 3–7
- Line 59: `- **Pre-execution stale detection**: see \`workflow.md\` Step 2.5 — abort execution if`

Required changes:
1. Replace Phase overview table row: `| 2.5 | Pre-execution stale detection | ... |` → `| 3 | Pre-execution stale detection | ... |`
2. Shift all subsequent Phase overview table rows +1: `| 3 |` → `| 4 |`, `| 4 |` → `| 5 |`, ..., `| 7 |` → `| 8 |`
3. Update cross-reference on line 59: `workflow.md` Step 2.5 → `workflow.md` Step 3

## Compatibility considerations
- This file's Phase overview table must align with workflow.md section headings; both are updated as part of the same overall task
- Downstream consumers reading this skill's description will expect consistent step numbering

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original content via `git checkout -- .opencode/skills/code-implementation/SKILL.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .opencode/skills/code-implementation/SKILL.md | Phase overview table verification | Read SKILL.md Phase overview table | Consecutive integers 0–8, no gaps |
| .opencode/skills/code-implementation/SKILL.md | Cross-reference consistency | Read SKILL.md for step number refs | All refs match new numbers |

## Completion criteria
- [ ] Phase overview table has consecutive integers 0–8 with no gaps
- [ ] Row `3 | Pre-execution stale detection` replaces the old `2.5` row
- [ ] Cross-reference `workflow.md` Step 2.5 → `workflow.md` Step 3 is updated
- [ ] Phase overview table alignment with workflow.md section headings confirmed

## Out of scope
- Updating workflow.md section headings (separate procedure)
- Updating sibling skill cross-references (separate procedure)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-191242 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-191242 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-191242 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-191242 | Not applicable: this IS the documentation change |

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
- **Related target files**: .opencode/skills/code-implementation/SKILL.md