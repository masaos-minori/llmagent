## Goal
- Make `skills/issue-to-plan/workflow.md` Step 8a run the normalizer before the structure check, without growing the file past its 42540 B ceiling (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the Step 8a "Run" paragraph and wording tightenings in Step 8 that offset it. Out of scope: any other step, `skills/issue-to-plan/SKILL.md`, and `tools/check_skill_size_baseline.txt`.

## Assumptions
- Verified in Step 3a: the file is 42540 B, equal to its ceiling in `tools/check_skill_size_baseline.txt`, so net growth fails `uv run python tools/check_skill_size.py`; the Step 8a "Run `uv run python tools/check_workitem_structure.py --file plans/{filename}.md`" paragraph is at lines 536-538; the edit measured +111 B with the longer wording, and the offsets below measured -92 B, so the added text must be at most 92 B: drop the parenthetical "(backticks every cited path)" (measured +82 B net of the shorter text).
- Procedure 03 makes the command real before this document runs (`seq` order).

## Design decisions
- Reword only; no rule is removed: the offsets drop redundant wording of Step 8 (listed below) and keep every instruction.

## Alternatives considered
- Raise the ceiling: rejected, the baseline only shrinks (as in wfeff002). Put the text in `workflow-edge.md`: not a Plan target.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Record `wc -c` (42540 expected).
2. Replace the paragraph "Run `uv run python tools/check_workitem_structure.py --file plans/{filename}.md` on the" newline "filled Plan (per `rules/tool-gates.md` "When to run which tool"). It checks only that every" newline "required `## ` section is present; the content checks above still apply." with: "Run `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`, then `uv run python tools/check_workitem_structure.py --file plans/{filename}.md` on the filled Plan (per `rules/tool-gates.md` "When to run which tool"). It checks the required `## ` sections and plain path citations; the content checks above still apply." (keep the file's line wrapping style).
3. Apply these offsets (exact old text to new text, line breaks as in the file):
   - "Repeat the" newline "Path A sizing check from Step 5: more than 3 `Implementation Target Files` rows in a Plan" newline "classified Path A is reclassified or split before the Plan is frozen." becomes "Repeat Step 5's" newline "Path A sizing check: more than 3 target rows in a Path A Plan means reclassify or split it" newline "before freezing." (saves 47 B);
   - "Verify the Requirement Traceability subsection has at least one row per Requirement ID" newline "(one per target file it affects) with all columns filled, including a Status entry" newline "from Step 2." becomes "Verify the Requirement Traceability subsection has one row per Requirement ID and target" newline "file it affects, all columns filled, including the Status entry from Step 2." (saves 17 B);
   - "This step has three sub-steps, applied in order: verify completeness and traceability" newline "(8a), validate and freeze the target-file inventory (8b), then report the outcome (8c)." becomes "Three sub-steps in order: verify completeness and traceability (8a), validate and freeze" newline "the target-file inventory (8b), report the outcome (8c)." (saves 28 B).
4. Run `wc -c` again: the size MUST be at most 42540. If larger, tighten another repeated phrase inside Step 8 without changing a rule, or stop and report (do not raise the ceiling).

### Method
- Edit with exact strings copied from the file; verify no instruction was dropped by re-reading Step 8a once.

### Details
- The Step 8a "Completed when" paragraph still ends with "the structure checker reports no findings", which now includes plain citations.

## Compatibility considerations
- The workflow is loaded by every Plan cycle; the added command is idempotent and writes only when a plain citation exists.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` (no ceiling raised, file at most 42540 B); the pre-commit hook "Check skills/rules/prompts file references resolve" on commit; the documentation-only checkers of `rules/tool-gates.md` for `skills/**/*.md`.

## Completion criteria
- Step 8a runs the normalizer before the structure check, the command text matches the tool's usage, and the size check passes.

## Out of Scope
- The tool and template (procedures 03 and 07) and the tool rows (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-172913_wfeff003_plan-path-citations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-173805
- **Related target files**: `skills/issue-to-plan/workflow.md`
