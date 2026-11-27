## Goal
- Add a `### Step 3c: stale mismatch classification` section to `skills/plan-to-implementation-procedure/workflow-edge.md` holding the Step 3c mismatch rules moved verbatim from `skills/plan-to-implementation-procedure/workflow.md`, plus the tool usage (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs before the seq 05 procedure: adding the section first keeps every rule present while both files are valid.

## Assumptions
- Verified in Step 3a: the file is 6089 B with sections at lines 8, 32, 42, 55, 78, 88 and no entry in `tools/check_skill_size_baseline.txt` (limit 16384 B); the paragraph to move is the 1207 B "After writing it, run `uv run python tools/stale_detector.py {document_path}`" bullet of Step 3c.
- This is a procedure revision, so it does not route through `python-documentation` (`routing.md` Documentation row exception).

## Design decisions
- Keep the section order of the file (sections follow the order of Steps); insert the new section after `### Step 3c: existing output path`.
- Move the rules (1) `(new)` marking, (2) sibling-declared names, (3) other stale references, and the companion sentence verbatim; add only the tool usage lines.

## Alternatives considered
- Keep the paragraph in `workflow.md` and only add a pointer: rejected, the file has 23 B of headroom.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow-edge.md`

### Procedure
1. After `### Step 3c: existing output path`, add the heading `### Step 3c: stale mismatch classification`.
2. Under it write, verbatim from `workflow.md`, the text that follows "For each mismatch:" through "against the companion, not against the primary target." (rules (1) to (3) and the companion sentence), introduced by the sentence "Apply this section to each mismatch `tools/stale_detector.py` reports for a document written in Step 3c."
3. Append: "For a whole Plan, `uv run python tools/finalize_procedures.py {plan_path}` runs the stale, structure, and Plan coverage checks, prints only failures, and classifies each `symbol_missing` name as `created here`, `not a code symbol`, or `ambiguous`; add `--apply` (after `--dry-run`) to apply only the unambiguous actions. An `ambiguous` name is corrected by hand under rule (3)."

### Method
- Copy the moved text from the file with the editor, then diff the two copies before and after the seq 05 edit to prove nothing was lost.

### Details
- Plain ASCII punctuation as in the neighboring sections; the heading must be unique.

## Compatibility considerations
- N/A: on-demand section; `tools/check_skills_references.py` must still resolve the references.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` exits 0 (the file stays far below 16384 B); `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Completion criteria
- The new section exists with the moved rules verbatim and the tool usage; the skill gates pass.

## Out of Scope
- `skills/plan-to-implementation-procedure/workflow.md` (seq 05) and any other section of this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the section with the moved text and the tool usage | Completed | 20261127-101152 | 20261127-101201 | Changed: skills/plan-to-implementation-procedure/workflow-edge.md (7556 B); moved text verbatim up to indentation |
| 2 | Run the skill size, reference, and heading-cycle checks | Completed | 20261127-101210 | 20261127-101210 | skill size, references, heading cycles pass |

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
- **Requirement ID**: `REQ-006` (moved rules and tool usage)
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100214
- **Related target files**: `skills/plan-to-implementation-procedure/workflow-edge.md`