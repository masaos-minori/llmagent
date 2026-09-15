# Add "Completed when" and failure-recovery condition to deploy workflow Phase 4

## Priority
High

## Summary
`skills/deploy/workflow.md` Phase 1 through Phase 3 (including all of Phase 3's sub-steps 3a-3d) each state an explicit "Completed when" and, where applicable, a "Stop and report"/failure-recovery condition — Phase 4 ("Verify deployment"), the final gate before considering a production deployment done, states none of either.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session; this entry covers the "goal + exit condition" criterion for the `deploy` skill specifically. Companion issues from the same review cover other files and other criteria.

## Problem
Confirmed by direct reading of `skills/deploy/workflow.md` lines 135-148 (Phase 4): the Phase states a Gate ("service is running; no new errors in logs") and the commands to check it (`curl`/`tail`, plus an agent-REPL `/mcp` check if the agent was restarted), but never states when those checks are considered passed, nor what to do if `/health` is not OK, if the log tail shows a new error, or if `/mcp` shows an unhealthy server. This is the deploy skill's final phase — an agent could run the checks, see an ambiguous or partially-bad result, and have no stated next step, unlike every other Phase in the same file.

## Reason for Change
Deployment verification is the last safety check before a change is considered live in production; per `AGENTS.md`'s emphasis on deployment as a high-blast-radius operation, this Phase having no stated pass/fail condition is a higher-severity gap than the same omission would be in a lower-stakes skill.

## Implementation Intent
Add a "Completed when" line stating the concrete pass condition (health check returns OK for every restarted service, and the log tail shows no new error since the restart timestamp), and a "Stop and report" line stating what to do if either check fails — likely routing back to Phase 3d's existing failure-recovery procedure rather than duplicating it, since Phase 3d already handles "service fails to start."

## Target Files or Areas
- `skills/deploy/workflow.md`

## Required Changes
- Add to Phase 4: "**Completed when**: every restarted service's `/health` endpoint returns OK, the log tail shows no new error timestamped after the restart, and (if the agent was restarted) `/mcp` shows every MCP server healthy."
- Add to Phase 4: "**If any check fails**: return to Phase 3d's failure-recovery procedure for the affected service rather than repeating ad hoc troubleshooting here."

## Constraints
Do not duplicate Phase 3d's failure-recovery steps inside Phase 4 — route back to it by reference, since Phase 3d already owns "service fails to start" recovery.

## Acceptance Criteria
- Phase 4 in `skills/deploy/workflow.md` has an explicit "Completed when" line matching its existing Gate statement.
- Phase 4 has an explicit failure path that references Phase 3d rather than duplicating its content.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/deploy/workflow.md`.

## Out of Scope
- Any other Phase in `skills/deploy/workflow.md` — all already have adequate completion/exit conditions per this review.
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the two lines described in Required Changes; do not restructure Phase 4 or duplicate Phase 3d's recovery steps — reference Phase 3d by name instead.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115009
- **Related target files**: skills/deploy/workflow.md
