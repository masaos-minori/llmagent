## Goal
- Make `skills/issue-to-plan/workflow.md` Step 7 record the `Evidence revision` line, size neutral (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the edits below in this one file. Out of scope: any other section, and `tools/check_skill_size_baseline.txt` (no ceiling is raised).

## Assumptions
- Verified in Step 3a: the file is 42530 B against its ceiling 42540 B; Step 7 is the Traceability step; the Plan row also named the same-cycle dedup bullet, which stays unchanged here because the Step 7 statement already references the rule and the tool (one statement per workflow, Plan AC-08). The edit set below was applied to a copy and measured: 42530 B now, 42533 B after, so the file stays within its ceiling.
- Every old text below was checked to occur exactly once in the file. Procedure 01 creates the tool before this document runs (`seq` order).

## Design decisions
- Only redundant wording is tightened and no rule is removed; the added text is the shortest form that states the skip and names the tool (Plan D-4, D-6).

## Alternatives considered
- Raise the ceiling: rejected, the baseline only shrinks. Put the text in an edge file: not a Plan target.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Record `wc -c skills/issue-to-plan/workflow.md` (42530 expected).
2. Apply each edit below: replace the old text (copied exactly, line breaks as in the file) with the new text.
3. Run `wc -c` again: the size MUST be at most 42540 B (the ceiling; about 42533 B is expected); if it is larger, tighten another repeated phrase in the same file without changing a rule, or stop and report (do not raise the ceiling).
4. Re-read the changed section once to confirm every rule is intact.

Edit 1, old text:

```text
  `N/A: not applicable in this phase`; Generated at = the Step 5 timestamp; Related
  target files = the affected paths.
```

new text:

```text
  `N/A: not applicable in this phase`; Generated at = the Step 5 timestamp; Related
  target files = the affected paths; Evidence revision = the line `uv run python
  tools/check_evidence_freshness.py record plans/{filename}.md` prints.
```

Edit 2, old text:

```text
  Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: MUST NOT re-run a
  check already performed against the same file/claim at its current content within
  this cycle.
  Stop once every field extracted per `templates/issue.md` (extraction list below) has been checked against at least one concrete source (a file, test, or existing
  Plan/Implementation document) and the last full pass over that list found no new disconfirming evidence. This does not replace
  `rules/workflow-lifecycle.md`'s Completion Criteria, which gate the whole cycle.
```

new text:

```text
  Per `rules/ai-execution.md` Tool Usage's idempotent-command rule, MUST NOT re-run a check
  already performed against the same file/claim at its current content within this cycle.
  Stop once every field extracted per `templates/issue.md` (list below) has been checked
  against at least one concrete source (a file, test, or existing Plan/Implementation
  document) and the last full pass found no new disconfirming evidence. This does not
  replace `rules/workflow-lifecycle.md`'s Completion Criteria, which gate the whole cycle.
```

Edit 3, old text:

```text
- **Depth ceiling** (Steps 2, 3, and 8b): stay within the base order of
  `rules/ai-execution.md` Adversarial Verification (Base). Expand beyond it only when
  (a) a disconfirming finding produced inside that order points outside it, or (b) an
  Implementation Target Files row cannot meet one of the four Freeze criteria inside the
  order. Any other item that cannot be settled inside the order is classified
  `Needs confirmation` instead of being researched further.
```

new text:

```text
- **Depth ceiling** (Steps 2, 3, and 8b): stay within the base order of
  `rules/ai-execution.md` Adversarial Verification (Base). Expand beyond it only when (a) a
  disconfirming finding inside that order points outside it, or (b) a target row cannot meet
  one of the four Freeze criteria inside it. Anything else unsettled inside the order is
  `Needs confirmation`, not researched further.
```

Edit 4, old text:

```text
- Add the "Requirement Traceability" subsection immediately after those fields, using
  `templates/requirement-traceability.md`'s column format (Requirement ID, Source Issue
  section or evidence, Target file, Implementation step, Acceptance criterion, Test or
  validation item, Status). Status is the Step 2 evidence classification for that
  Requirement.
```

new text:

```text
- Add the "Requirement Traceability" subsection right after those fields, in the column
  format of `templates/requirement-traceability.md` (Requirement ID, Source Issue section
  or evidence, Target file, Implementation step, Acceptance criterion, Test or validation
  item, Status); Status is the Step 2 evidence classification of the Requirement.
```

### Method
- Exact-string edits only; no other line changes.

### Details
- The statement of the skip names `tools/check_evidence_freshness.py` so a stale-detector-style check can resolve it after procedure 01.

## Compatibility considerations
- The skip applies only when a Plan records an `Evidence revision`; Plans without one are verified in full as today.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py` (no ceiling raised); the pre-commit hook "Check skills/rules/prompts file references resolve" on commit; the documentation-only checkers of `rules/tool-gates.md` for the file.

## Completion criteria
- All edits are applied, the rules read as before plus the skip statement, and the size check passes.

## Out of Scope
- The tool, the template, and the other rule files (procedures 01 and 03 to 08).

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261126-151439_wfeff004_evidence-sha-carryover.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-182520_wfeff004_evidence-sha-carryover.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-183845
- **Related target files**: `skills/issue-to-plan/workflow.md`
