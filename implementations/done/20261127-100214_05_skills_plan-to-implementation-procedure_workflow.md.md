## Goal
- Replace the Step 3c stale-mismatch paragraph of `skills/plan-to-implementation-procedure/workflow.md` with a pointer to the edge section and add the tool to the Toolchain list and Step 4, ending at or below the 34876 B ceiling (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after the seq 04 procedure, so the moved rules already exist in `workflow-edge.md`.

## Assumptions
- Verified in Step 3a: the file is 34853 B; the paragraph is 1207 B; `tools/check_skill_size_baseline.txt` records 34876 for this file. Measure `wc -c` before and after.
- The wfeff007 Plan also adds a Step 3c pointer to this file after this Plan lands; this edit does not touch its lines.

## Design decisions
- Replace the paragraph (net about -1000 B) so the headroom is real, and leave the baseline file unchanged (a shrunk baselined file is reported as advisory only).
- Use the file's existing form "load `skills/plan-to-implementation-procedure/workflow-edge.md` and follow its ... section".

## Alternatives considered
- Lower the baseline entry: out of scope (not a Plan target); the advisory report shows the opportunity.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Before editing, run `wc -c` (expect 34853) and confirm `workflow-edge.md` already contains `### Step 3c: stale mismatch classification` (stop if it does not).
2. In Step 3c replace the bullet that starts "After writing it, run `uv run python tools/stale_detector.py {document_path}`" and ends "against the companion, not against the primary target." with: "After writing it, run `uv run python tools/stale_detector.py {document_path}` (the same check `code-implementation` runs before executing a procedure, so a stale reference surfaces here instead of aborting that later cycle). For each mismatch, or for the whole Plan at once with `uv run python tools/finalize_procedures.py {plan_path}`: load `skills/plan-to-implementation-procedure/workflow-edge.md` and follow its \"Step 3c: stale mismatch classification\" section."
3. In the Toolchain list add: "- `tools/finalize_procedures.py` (Step 3c and Step 4, the stale, structure, and coverage checks for a whole Plan)." beside the other Step 3c tools.
4. In Step 4, after "run `uv run python tools/check_workitem_traceability.py --plan-coverage {plan_path}` and require exit 0 before the move;" add "`tools/finalize_procedures.py` runs it with the per-document checks;".
5. Run `wc -c` again: at most 34876.

### Method
- Exact-string edits; each replaced text occurs once (check with `rg -c` first).

### Details
- Do not reword other Step 3c text.

## Compatibility considerations
- N/A: procedure text; the moved rules stay reachable through the pointer.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit (together with seq 04 if the pointer should not remain).

## Validation plan
- `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` exit 0; a diff of the moved text between the pre-edit `workflow.md` (from `git show HEAD:...`) and the new edge section shows no change.

## Completion criteria
- Step 3c points to the edge section, Toolchain and Step 4 name the tool, the file is at or below 34876 B, and the moved text is identical to the original.

## Out of Scope
- `skills/plan-to-implementation-procedure/workflow-edge.md` (seq 04), `tools/check_skill_size_baseline.txt`, other text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure, then replace the paragraph and add the Toolchain and Step 4 references | Completed | 20261127-101201 | 20261127-101210 | Changed: skills/plan-to-implementation-procedure/workflow.md 34853 -> 34323 B (ceiling 34876); moved text compared whitespace-normalized: identical |
| 2 | Run the skill size, reference, and heading-cycle checks and the moved-text comparison | Completed | 20261127-101210 | 20261127-101210 | check_skill_size, check_skills_references, check_skills_heading_cycles pass |

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
- **Requirement ID**: `REQ-006` (pointer within the size ceiling)
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100214
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`