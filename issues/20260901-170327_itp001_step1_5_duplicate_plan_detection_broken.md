# Step 1.5's duplicate-plan detection does not match actual Plan filenames

## Priority
High

## Summary
`skills/issue-to-plan/workflow.md` Step 1.5 detects an already-existing Plan by
globbing `plans/*{issue_id}*plan.md` or `plans/*{issue_timestamp}*plan.md`, but real
Plan filenames never contain the source Issue's ID or timestamp, so the glob never
matches and the duplicate check silently passes even when a Plan already exists.

## Background
Verified against the live repository (Evidence: Confirmed by repository evidence):

```
plans/20260831-222625_plan.md
- Source issue: issues/20260831-162016_doc001_overview_broken_links.md
```

The Plan's filename (`20260831-222625_plan.md`) uses the Plan-generation timestamp
(`date +%Y%m%d-%H%M%S` run at Step 5), not the source Issue's own timestamp
(`20260831-162016`) or ID (`doc001`). This pattern holds across every sampled Plan —
`plans/{filename}_plan.md` carries no trace of the Issue that produced it in its
filename; the link exists only inside the Plan's own `## Traceability` section
(`Source issue: {path}`).

## Problem
`workflow.md` Step 1.5 states:
- "If the Issue filename contains an ID... glob `plans/*{issue_id}*plan.md`"
- "If the Issue filename... has a timestamp prefix... glob... `plans/*{issue_timestamp}*plan.md`"

Both glob patterns search the *filename*, but the ID/timestamp only ever appears
inside the Plan's *content* (its Traceability section), never in its filename.
Every invocation of this check against a real Plan corpus returns "no matching plan"
regardless of whether one actually exists — a false negative on every real case,
not an edge case.

## Reason for Change
This check exists specifically "to prevent duplicate plans when multiple agents
process the same Issue concurrently" (Step 1.5's own stated purpose). Because the
check as written cannot ever find a real match, that purpose is not met: a second
run against an already-Planned Issue will proceed to Step 2 and generate a second,
duplicate Plan for the same Issue. This was worked around ad hoc during a real
session by grepping `plans/*.md`'s `Source issue:` field instead of globbing
filenames — i.e., the workflow document does not describe the procedure that
actually works.

## Implementation Intent
Replace the filename-glob check with a content-based check: for the current Issue's
repository-relative path, search `plans/*.md` and `plans/done/*.md` for a
`- **Source issue**: {issue_path}` line (exact match) inside the `## Traceability`
section. Preserve the existing scope restriction (do not check `issues/done/`) and
the existing behavior once a match is found (record it, skip Plan creation, proceed
to Step 9/10).

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 1.5)

## Required Changes
- Replace the ID/timestamp filename-glob logic in Step 1.5 with a `grep`-based search
  over `plans/*.md` and `plans/done/*.md` for an exact `Source issue` Traceability
  field match against the current Issue's repository-relative path.
- Keep the existing three-way branch structure (ID present / timestamp-only /
  neither) only if it remains meaningful under the new content-based check;
  otherwise simplify to a single content-search procedure, since the Issue path
  itself (not its ID or timestamp) is what the Traceability field actually stores.
- Note in the workflow that this is a correction of a previously non-functional
  check, so a reader does not assume the old glob behavior was ever a working
  fallback.

## Constraints
Do not change Step 1.5's scope restriction (only `plans/` and `plans/done/`, never
`issues/done/`) or its downstream behavior when a match is found — only the matching
mechanism itself is in scope.

## Acceptance Criteria
- Running the corrected Step 1.5 procedure against an Issue whose Plan already
  exists (verified via a real `Source issue` Traceability match) correctly reports
  the existing Plan's path and skips Plan creation.
- Running it against an Issue with no existing Plan correctly proceeds to Step 2.
- The check's description no longer references filename ID/timestamp globbing as
  its mechanism.

## Testing Expectations
Manual verification is sufficient (this is a documentation-only workflow-procedure
fix, not code): re-run the corrected procedure against at least one Issue with a
known existing Plan and one without, and confirm the outcome matches Acceptance
Criteria.

## Documentation Impact
N/A: this issue's fix is itself the documentation correction (`skills/issue-to-plan/workflow.md`); no `docs/*.md` file describes this internal workflow mechanism.

## Out of Scope
- Changing how Plans record their `Source issue` field.
- Adding an ID or timestamp to Plan filenames (a different, larger change with its
  own tradeoffs — not required to fix this specific detection gap).

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the glob-vs-content-search mismatch is directly confirmed against live
repository data, not inferred.

## AI Implementation Instruction
Read `skills/issue-to-plan/workflow.md` Step 1.5 in full before editing. Verify the
proposed `grep`-based replacement against at least 2-3 real `plans/*.md` files'
`## Traceability` sections to confirm the exact field-line format before finalizing
the pattern. Do not invent a filename convention that does not currently exist as
an alternative fix.
