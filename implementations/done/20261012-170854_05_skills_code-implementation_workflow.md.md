## Goal
- State in the stale detection step that a symbol or import written with the (new) marker is not checked (`REQ-004`).

## Scope
- Only the subsection Stale detection result handling of `skills/code-implementation/workflow.md`: two added sentences. The abort rules are unchanged.

## Assumptions
- The subsection explains what the detector reports and that any mismatch aborts the procedure; the new text explains one input convention and does not change the abort policy.

## Design decisions
- Add the sentences after the description of what the detector extracts so a reader meets the marker before the abort rules.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Locate the subsection with `grep -n "Stale detection result handling" skills/code-implementation/workflow.md`.
2. Add, in English and in the same register, two sentences: a symbol or an import statement that the procedure marks with the word (new) after its backticked name is declared as created by the procedure and is not checked against the current source (see the notes in `templates/implementation-procedure.md`); and an unmarked name that does not exist is still a mismatch and aborts the procedure as before.
3. Leave the abort rules and every other step untouched.

### Method
- Insert the sentences as a short paragraph or a bullet that matches the surrounding formatting.

### Details
- Do not weaken the sentence that forbids correcting the procedure and continuing after a mismatch; the marker only affects what counts as a mismatch.
- Apply together with procedures 03 and 04.

## Compatibility considerations
N/A: documentation-only change; the workflow's behavior for real mismatches is unchanged.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` passes (the new file reference resolves).
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The subsection states the exemption and keeps the abort rules unchanged; the reference checker passes.

## Out of scope
- The abort policy, other steps of the workflow, and the skill's overview file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker sentences to the stale detection subsection | Completed | 20261012-171434 | 20261012-171450 | stale_detector clean changed: skills/code-implementation/workflow.md (one paragraph in Stale detection result handling; abort rules unchanged) |
| 2 | Run the skills reference checker | Completed | 20261012-171450 | 20261012-171450 | check_skills_references passes |

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
- **Requirement ID**: `REQ-004` (state the exemption where the detector's result is handled)
- **Source issue**: issues/20261012-132457_stale001_fix-stale-detector-false-positives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-132739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-170854
- **Related target files**: skills/code-implementation/workflow.md