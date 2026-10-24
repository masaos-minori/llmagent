# Align the Issue-Creator Scaffold Policy With Actual Drafting Practice

## Priority
Low

## Summary
Resolve the drift between the `issue-creator` skill's scaffold guidance (`SKILL.md`
"scaffold the file"; `workflow.md` Step 10.2 "Prefer `tools/generate_workitem.py`") and
measured practice: scaffolding is used for complex first drafts and bypassed for fast
batch drafts. Replace the criteria-free "Prefer" with one explicit policy stated
consistently in both files.

## Background
Measured from the same session-history corpus as `perf006` (5 pure `issue-creator`
sessions, 34 issues): 20 `generate_workitem` invocations across 34 issues; 14 issues were
written without scaffolding — all fast batch drafts — and all passed Step 10.4 structure
verification (confirmed by measurement). `SKILL.md` step 10 says "scaffold the file";
`workflow.md` Step 10.2 says "Prefer" the tool and then describes a manual fallback,
without defining when the fallback is acceptable.

## Problem
The scaffold requirement is unenforceable as written: "Prefer" carries no criteria, and
the two skill files state different strengths ("scaffold the file" vs "Prefer"), so
compliance cannot be judged and the files can drift further. Note: the bypass produced no
observed harm in the corpus — no structure-check failures — so the problem is the
undefined policy, not the practice.

## Reason for Change
`perf001` and `perf004` show this repository's pattern: "Prefer"/MAY-level guidance
without stated criteria is observably ignored. This drift is the same failure mode at an
early, currently harmless stage. Settling it before `perf006` rewrites the drafting flow
avoids editing the same Phase 10 section twice.

## Implementation Intent
Decide one policy and state it identically in both files:
- Option A: the scaffold is required for every new issue file.
- Option B: direct writing from the canonical skeleton is allowed under explicit
  conditions (the skeleton already loaded in context plus per-file Step 10.4
  verification), replacing "Prefer" with those conditions.
Make the decision at policy level — what scaffolding guarantees (collision refusal,
verbatim skeleton) and which of those the direct-write path must reproduce — rather than
patching one file's wording in isolation.

## Target Files or Areas
- `skills/issue-creator/SKILL.md` (Issue Filename Generation / step 10)
- `skills/issue-creator/workflow.md` (Step 10.2, Step 10.3)

## Required Changes
- Replace the criteria-free "Prefer ..." line in Step 10.2 with the decided policy
  (required scaffold, or conditional direct-write).
- Make `SKILL.md` step 10 wording match the workflow policy.
- If Option B is chosen: state the direct-write conditions explicitly, including the
  path-uniqueness pre-check and per-file Step 10.4 verification that the scaffold path
  gets from the tool's collision refusal.

## Constraints
- No changes to `tools/generate_workitem.py` behavior, including its collision-refusal
  semantics.
- Step 10.4 verification stays mandatory in either option.
- MUST NOT change Step 10.2a collision-retry guidance.

## Acceptance Criteria
- `SKILL.md` and `workflow.md` state one consistent scaffold policy with explicit
  criteria; Step 10.2 no longer contains a criteria-free "Prefer".
- `check_workitem_structure` and the skills structure checker pass in both modes.

## Testing Expectations
Documentation-only change, no behavior affected:
- Run `check_skills_structure.sh` in both modes.
- Manual review that both files' wording matches the decided policy.

## Documentation Impact
Skill workflow files are the documentation changed: the scaffold policy becomes an
explicit contract instead of a preference. No other docs affected.

## Out of Scope
- `perf006` batch-mode semantics (shared pre-investigation, merge-edit procedure).
- `tools/generate_workitem.py` implementation or CLI changes.
- Step 10.2a collision-retry behavior.
- Lazy loading of the Step 0 mandatory-load set — excluded by the 2026-10-24
  prompt-cache user decision, same as the other perf issues.

## Dependencies
- `perf006` — same Phase 10 / multi-file drafting region of
  `skills/issue-creator/workflow.md`. Fix order: `perf006` first, then this issue, to
  avoid editing the same section twice.
- `perf001` — cross-reference only (same "Prefer/MAY ignored" failure pattern; this
  issue edits different files).

## Unresolved Questions
- Which policy to adopt: Option A (mandatory scaffold) or Option B (conditional
  direct-write). Needs user decision. The corpus shows the bypass is harmless and is
  where the fast drafting happens; mandating the scaffold adds roughly one tool call per
  issue.
- Under Option B, which existing guidance covers the direct-write path's filename
  uniqueness check (Step 10.2's manual procedure item 3) — confirm it applies verbatim
  or needs restating for batch drafting.

## AI Implementation Instruction
Apply this issue after `perf006`'s edits have landed. Limit changes to the two
`issue-creator` skill files; do not touch `tools/`. Do not renumber phases or alter
Step 10.4. Re-anchor against current file content before editing — these files churn
frequently. If the policy decision (Option A vs B) has not been made, stop and ask
before editing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-212657
- **Related target files**: `skills/issue-creator/SKILL.md`, `skills/issue-creator/workflow.md`
